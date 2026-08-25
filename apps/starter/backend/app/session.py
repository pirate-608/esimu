"""Starter game session built on esimu-core.

Copyright (c) 2026 pirate-608. Licensed under the MIT License.

The starter intentionally avoids Redis, PostgreSQL, and admin editors. Optional
LLM calls live in ``app.ai`` while this session keeps deterministic local paths:
world loading, character setup, runtime payloads, local events/forum posts,
messenger payloads, item buy/sell, relax effects, and final-exam settlement.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping

from app.bootstrap import configure_project_environment

configure_project_environment()

from esimu_core.content import (  # noqa: E402
    normalize_message_payload,
    select_local_event,
    select_local_forum_post,
)
from esimu_core.domain.effects import (  # noqa: E402
    StatBounds,
    apply_delta_to_snapshot,
)
from esimu_core.domain.semester import (  # noqa: E402
    CourseExamInput,
    settle_course_exam,
    settle_semester_exam,
)
from esimu_core import PROTOCOL_VERSION, STATE_VERSION, __version__  # noqa: E402
from esimu_core.lifecycle import (  # noqa: E402
    build_initial_character_state,
    build_semester_reset_state,
)
from esimu_core.runtime.snapshot import (  # noqa: E402
    RuntimePayloadDefaults,
    build_init_payload_from_snapshot,
    build_tick_payload_from_snapshot,
)
from esimu_core.runtime.state import RuntimeSnapshot  # noqa: E402
from esimu_core.world.balance import GameBalance  # noqa: E402
from esimu_core.world.catalog import WorldCatalog  # noqa: E402
from esimu_core.world.items import ItemCatalog  # noqa: E402
from esimu_core.world.stat_definitions import StatDefinitions  # noqa: E402
from esimu_core.world.story import ThemeStory  # noqa: E402
from esimu_core.world.theme import ThemeManifest  # noqa: E402


@dataclass
class StarterGameSession:
    """One in-memory player session for starter smoke runs."""

    username: str = "Starter Player"
    theme_id: str = "demo-campus"
    catalog: WorldCatalog = field(init=False)
    stats_registry: StatDefinitions = field(init=False)
    balance: GameBalance = field(init=False)
    items: ItemCatalog = field(init=False)
    theme: ThemeManifest = field(init=False)
    story: ThemeStory = field(init=False)
    stats: dict[str, Any] = field(default_factory=dict)
    courses: dict[str, float] = field(default_factory=dict)
    course_states: dict[str, int] = field(default_factory=dict)
    items_state: dict[str, Any] = field(default_factory=lambda: {"owned": []})
    messenger_state: dict[str, Any] = field(default_factory=lambda: {"contacts": {}})
    last_event: dict[str, Any] | None = None
    ended: bool = False
    state_version: int = STATE_VERSION
    is_running: bool = False
    speed_multiplier: float = 1.0
    exam_completed: bool = False

    def __post_init__(self) -> None:
        self.catalog = WorldCatalog(self.theme_id)
        self.stats_registry = StatDefinitions(
            self.catalog.path("stat_definitions.json")
        )
        self.balance = GameBalance()
        self.balance.load(self.catalog.path("game_balance.json"))
        self.items = ItemCatalog()
        self.items.load(self.catalog.path("items.json"))
        theme_path = self.catalog.world_dir.parent / "theme.json"
        story_path = self.catalog.world_dir.parent / "story.json"
        self.theme = ThemeManifest(theme_path)
        self.story = ThemeStory(story_path)

    def config_payload(self) -> dict[str, Any]:
        """Return public starter config for the minimal frontend."""
        return {
            "core_version": __version__,
            "protocol_version": PROTOCOL_VERSION,
            "state_version": STATE_VERSION,
            "theme": self.theme.public_metadata(),
            "story": self.story.public_metadata(),
            "stats": self.stats_registry.public_metadata(),
            "items": self.items.public_catalog(),
            "relax_actions": sorted(self.balance.relax_actions),
        }

    def majors_payload(self) -> list[dict[str, Any]]:
        """Return active-theme majors."""
        return self.catalog.majors()

    def initialize(
        self,
        *,
        major: str | None = None,
        stats: Mapping[str, Any] | None = None,
        username: str | None = None,
    ) -> dict[str, Any]:
        """Initialize a character using core lifecycle helpers."""
        major_id = major or self.majors_payload()[0]["abbr"]
        assignment = self.catalog.major_assignment(major_id)
        if assignment is None:
            raise ValueError(f"unknown major: {major_id}")
        allocations = self.stats_registry.normalize_initial_allocations(
            dict(stats or self.stats_registry.initial_default_stats()),
            allow_missing=True,
        )
        self.username = username or self.username
        state = build_initial_character_state(
            username=self.username,
            major_info=assignment["major_info"],
            course_plan=assignment["course_plan"],
            initial_courses=assignment["initial_courses"],
            stat_defaults=self.stats_registry.default_stats(),
            allocated_stats=allocations,
            initial_gold=self.items.initial_gold,
        )
        self.stats = {
            **self.stats_registry.default_stats(),
            **state.stats_update,
        }
        self.courses = {
            course_id: float(value)
            for course_id, value in state.courses_mastery.items()
        }
        self.course_states = dict(state.course_states)
        self.items_state = self.items.normalize_state({"owned": []})
        self.messenger_state = {"contacts": {}}
        self.last_event = None
        self.ended = False
        self.is_running = True
        self.speed_multiplier = 1.0
        self.exam_completed = False
        return state.summary

    def export_state(self) -> dict[str, Any]:
        """Serialize mutable player state for starter persistence adapters."""
        return {
            "username": self.username,
            "theme_id": self.theme_id,
            "stats": self.stats,
            "courses": self.courses,
            "course_states": self.course_states,
            "items_state": self.items_state,
            "messenger_state": self.messenger_state,
            "last_event": self.last_event,
            "ended": self.ended,
            "state_version": self.state_version,
            "is_running": self.is_running,
            "speed_multiplier": self.speed_multiplier,
            "exam_completed": self.exam_completed,
        }

    @classmethod
    def from_state(cls, state: Mapping[str, Any]) -> "StarterGameSession":
        """Restore a starter session from an adapter-owned state mapping."""
        session = cls(
            username=str(state.get("username") or "Starter Player"),
            theme_id=str(state.get("theme_id") or "demo-campus"),
        )
        session.stats = dict(state.get("stats") or {})
        session.courses = {
            str(course_id): float(value)
            for course_id, value in dict(state.get("courses") or {}).items()
        }
        session.course_states = {
            str(course_id): int(value)
            for course_id, value in dict(state.get("course_states") or {}).items()
        }
        session.items_state = session.items.normalize_state(
            state.get("items_state") or {"owned": []}
        )
        session.messenger_state = dict(state.get("messenger_state") or {"contacts": {}})
        last_event = state.get("last_event")
        session.last_event = (
            dict(last_event) if isinstance(last_event, Mapping) else None
        )
        session.ended = bool(state.get("ended", False))
        session.state_version = int(state.get("state_version", STATE_VERSION))
        session.is_running = bool(state.get("is_running", False))
        session.speed_multiplier = float(state.get("speed_multiplier", 1.0))
        session.exam_completed = bool(state.get("exam_completed", False))
        return session

    def snapshot(self) -> RuntimeSnapshot:
        """Build the core runtime snapshot from in-memory state."""
        self._ensure_initialized()
        effective_stats = self.items.apply_bonuses_to_stats(
            self.stats, self.items_state
        )
        return RuntimeSnapshot.from_mappings(
            stats=effective_stats,
            courses=self.courses,
            course_states=self.course_states,
            relax_cooldowns={},
            semester_duration=self._semester_duration(),
            dingtalk_state=self.messenger_state,
            items_state=self.items.state_payload(self.items_state),
        )

    def init_payload(self) -> dict[str, Any]:
        """Return the adapter's initial game payload."""
        payload = build_init_payload_from_snapshot(
            self.snapshot(), self._payload_defaults()
        )
        payload["messenger_state"] = payload.pop("dingtalk_state", {})
        payload.update(
            {
                "protocol_version": PROTOCOL_VERSION,
                "state_version": STATE_VERSION,
                "is_running": self.is_running,
                "speed_multiplier": self.speed_multiplier,
                "exam_completed": self.exam_completed,
                "ended": self.ended,
            }
        )
        return payload

    def tick_payload(self) -> dict[str, Any]:
        """Return a current tick payload without advancing time."""
        payload = build_tick_payload_from_snapshot(
            self.snapshot(), self._payload_defaults()
        )
        payload.update(
            {
                "protocol_version": PROTOCOL_VERSION,
                "is_running": self.is_running,
                "speed_multiplier": self.speed_multiplier,
                "exam_completed": self.exam_completed,
                "ended": self.ended,
            }
        )
        return payload

    def advance_tick(self) -> dict[str, Any]:
        """Advance one virtual tick while the session is running."""
        self._ensure_initialized()
        if not self.is_running or self.exam_completed or self.ended:
            return self.tick_payload()
        tick_config = self.balance.raw.get("tick") or {}
        course_config = self.balance.raw.get("course") or {}
        interval = max(1, int(tick_config.get("interval_seconds", 3)))
        self.stats["elapsed_game_time"] = int(
            self.stats.get("elapsed_game_time", 0)
        ) + interval
        base_gain = float(course_config.get("base_mastery_gain", 0.8))
        for course_id, state in self.course_states.items():
            if int(state) <= 0:
                continue
            multiplier = 1.0 if int(state) == 1 else 1.5
            self.courses[course_id] = min(
                120.0,
                float(self.courses.get(course_id, 0)) + base_gain * multiplier,
            )
        if int(self.stats["elapsed_game_time"]) >= self._semester_duration():
            self.stats["elapsed_game_time"] = self._semester_duration()
            self.is_running = False
        return self.tick_payload()

    def pause(self) -> dict[str, Any]:
        """Pause gameplay mutation and ticking."""
        self.is_running = False
        return self.tick_payload()

    def resume(self) -> dict[str, Any]:
        """Resume ticking unless the term already requires settlement."""
        if not self.exam_completed and not self.ended:
            self.is_running = True
        return self.tick_payload()

    def set_speed(self, speed: object) -> dict[str, Any]:
        """Set one of the Starter-supported speed multipliers."""
        parsed = float(speed)
        if parsed not in {1.0, 1.5, 2.0}:
            raise ValueError("speed must be 1, 1.5, or 2")
        self.speed_multiplier = parsed
        return self.tick_payload()

    def change_course_state(self, course_id: str, state: object) -> dict[str, Any]:
        """Update one course strategy while gameplay is running."""
        if not self.is_running:
            raise ValueError("game is paused")
        if course_id not in self.course_states:
            raise ValueError(f"unknown course: {course_id}")
        parsed = int(state)
        if parsed not in {0, 1, 2}:
            raise ValueError("course state must be 0, 1, or 2")
        self.course_states[course_id] = parsed
        return self.tick_payload()

    def next_semester(self) -> dict[str, Any]:
        """Advance to the next configured term after an exam."""
        if not self.exam_completed:
            raise ValueError("finish the exam before starting the next semester")
        next_index = int(self.stats.get("semester_idx", 1)) + 1
        major = str(self.stats.get("major_abbr") or "")
        courses = self.catalog.courses_for_semester(major, next_index)
        if not courses:
            self.ended = True
            self.is_running = False
            return {"ended": True, "tick": self.tick_payload()}
        reset = build_semester_reset_state(
            semester_idx=next_index,
            courses=courses,
            current_energy=self.stats.get("energy", 100),
            energy_default=self.stats_registry.by_id["energy"].default,
            energy_minimum=self.stats_registry.by_id["energy"].min,
        )
        self.stats.update(reset.stats_update)
        self.stats["semester_idx"] = next_index
        self.courses = {
            course_id: float(value)
            for course_id, value in reset.courses_mastery.items()
        }
        self.course_states = dict(reset.course_states)
        self.exam_completed = False
        self.is_running = True
        return {
            "ended": False,
            "summary": reset.summary,
            "tick": self.tick_payload(),
        }

    def restart(self) -> dict[str, Any]:
        """Reset the current local player to a fresh first term."""
        major = str(self.stats.get("initial_major_abbr") or "") or None
        self.initialize(major=major, username=self.username)
        return self.init_payload()

    def messenger_reply(
        self,
        contact_id: str,
        option_id: str | None = None,
        content: str | None = None,
    ) -> dict[str, Any]:
        """Append one player reply and an immediate deterministic NPC response."""
        contacts = self.messenger_state.get("contacts") or {}
        contact = contacts.get(contact_id)
        if not isinstance(contact, dict):
            raise ValueError(f"unknown messenger contact: {contact_id}")
        options = list(contact.get("pending_options") or [])
        selected = next(
            (
                option
                for option in options
                if str(option.get("id") or "") == str(option_id or "")
            ),
            options[0] if options else {"text": content or "收到"},
        )
        player_text = str(content or selected.get("text") or "收到")
        messages = contact.setdefault("messages", [])
        messages.append({"speaker": "player", "content": player_text})
        npc_text = f"我知道了。关于“{player_text}”，我们之后再聊。"
        messages.append({"speaker": "npc", "content": npc_text})
        contact["pending_options"] = [
            {"id": "continue", "text": "继续聊聊"},
            {"id": "later", "text": "稍后再说"},
        ]
        contact["rounds"] = int(contact.get("rounds", 0)) + 1
        return {
            "contact_id": contact_id,
            "player_message": player_text,
            "npc_message": npc_text,
            "reply_options": contact["pending_options"],
            "state": self.messenger_state,
        }

    def relax(self, action: str = "walk") -> dict[str, Any]:
        """Apply one configured relax action deterministically."""
        self._ensure_initialized()
        config = self.balance.relax_actions.get(action)
        if not isinstance(config, Mapping):
            raise ValueError(f"unknown relax action: {action}")

        changes: list[dict[str, Any]] = []
        for field_name, config_key in (
            ("energy", "energy_cost"),
            ("energy", "energy_gain"),
            ("sanity", "sanity_gain"),
            ("stress", "stress_change"),
            ("charm", "charm_gain"),
        ):
            if config_key not in config:
                continue
            result = self._apply_stat_delta(field_name, int(config[config_key]))
            if result.change:
                changes.append(result.change.as_dict())

        if action == "forum_browse":
            effect = (config.get("effects") or [{}])[0]
            if isinstance(effect, Mapping):
                for field_name, delta in effect.items():
                    if field_name == "weight":
                        continue
                    result = self._apply_stat_delta(str(field_name), int(delta))
                    if result.change:
                        changes.append(result.change.as_dict())

        return {"action": action, "changes": changes, "tick": self.tick_payload()}

    def event(self) -> dict[str, Any]:
        """Select one local event from the active theme."""
        self._ensure_initialized()
        selected = select_local_event(
            self.catalog.event_library(),
            sanity=int(self.stats.get("sanity", 100)),
            stress=int(self.stats.get("stress", 0)),
            choose=lambda candidates: candidates[0],
        )
        if selected is None:
            raise ValueError("event library is empty")
        self.last_event = selected.as_dict()
        return self.last_event

    def accept_event(self, event: Mapping[str, Any]) -> dict[str, Any]:
        """Store an event generated by an optional content adapter."""
        normalized = {
            "id": event.get("id"),
            "title": str(event.get("title") or ""),
            "desc": str(event.get("desc") or ""),
            "options": list(event.get("options") or []),
        }
        if not normalized["title"] or len(normalized["options"]) < 2:
            raise ValueError("generated event is incomplete")
        self.last_event = normalized
        return normalized

    def choose_event(self, option_index: int = 0) -> dict[str, Any]:
        """Apply one option from the currently selected event."""
        if self.last_event is None:
            self.event()
        assert self.last_event is not None
        options = self.last_event.get("options") or []
        option = options[option_index]
        effects = option.get("effects") if isinstance(option, Mapping) else {}
        effects = effects if isinstance(effects, Mapping) else {}
        changes: list[dict[str, Any]] = []
        for field_name, delta in effects.items():
            if field_name == "desc":
                continue
            result = self._apply_stat_delta(str(field_name), int(delta))
            if result.change:
                changes.append(result.change.as_dict())
        return {"desc": str(effects.get("desc") or ""), "changes": changes}

    def forum_post(self) -> dict[str, str]:
        """Return one active-theme forum post."""
        post = select_local_forum_post(
            self.catalog.forum_library(),
            effect="positive",
            trigger="校园梗",
            fallback="forum fallback",
            choose=lambda candidates: candidates[0],
        )
        if post is None:
            raise ValueError("forum library is empty")
        return post.as_dict()

    def messenger_round(self) -> dict[str, Any]:
        """Return one normalized messenger contact and opening message."""
        characters = self.catalog.load_json(self.catalog.path("characters.json"), [])
        character = characters[0] if characters else {"name": "Guide", "role": "friend"}
        payload = normalize_message_payload(
            {
                "contact": {
                    "sender": character.get("name"),
                    "role": character.get("role"),
                },
                "content": f"{character.get('name', 'Guide')} 发来一条问候。",
                "reply_options": ["收到", "稍后聊"],
            },
            contact_prefix="msg",
        )
        return self.accept_messenger_round(
            {
                "contact": payload.contact.as_dict(),
                "content": payload.content,
                "reply_options": [option.as_dict() for option in payload.reply_options],
            }
        )

    def accept_messenger_round(self, raw: Mapping[str, Any]) -> dict[str, Any]:
        """Store one normalized local or AI-generated messenger opening."""
        payload = normalize_message_payload(raw, contact_prefix="msg")
        contact = payload.contact.as_dict()
        self.messenger_state["contacts"][contact["contact_id"]] = {
            **contact,
            "messages": [{"speaker": "npc", "content": payload.content}],
            "pending_options": [option.as_dict() for option in payload.reply_options],
            "rounds": 0,
        }
        return {
            "contact": contact,
            "content": payload.content,
            "reply_options": [option.as_dict() for option in payload.reply_options],
        }

    def first_character(self) -> dict[str, Any]:
        """Return one theme character for the minimal messenger flow."""
        characters = self.catalog.load_json(self.catalog.path("characters.json"), [])
        if isinstance(characters, list) and characters:
            return dict(characters[0])
        return {"name": "Guide", "role": "friend", "description": "Helpful."}

    def buy_item(self, item_id: str | None = None) -> dict[str, Any]:
        """Buy the first affordable item or a requested item."""
        self._ensure_initialized()
        target_id = item_id or self.items.public_items[0]["id"]
        new_state, item, error = self.items.build_buy_state(self.items_state, target_id)
        if error or new_state is None or item is None:
            raise ValueError(error or "item buy failed")
        price = int(item.get("price", 0))
        if int(self.stats.get("gold", 0)) < price:
            raise ValueError("not enough gold")
        self._apply_stat_delta("gold", -price)
        self.items_state = new_state
        return self.items.state_payload(self.items_state)

    def sell_item(self, item_id: str | None = None) -> dict[str, Any]:
        """Sell one owned item."""
        owned = list(self.items_state.get("owned") or [])
        target_id = item_id or (str(owned[0]) if owned else "")
        new_state, item, error = self.items.build_sell_state(
            self.items_state, target_id
        )
        if error or new_state is None or item is None:
            raise ValueError(error or "item sell failed")
        self._apply_stat_delta("gold", int(item.get("sell_price", 0)))
        self.items_state = new_state
        return self.items.state_payload(self.items_state)

    def final_exam(self) -> dict[str, Any]:
        """Settle one term with core semester/GPA helpers."""
        self._ensure_initialized()
        courses = json.loads(str(self.stats.get("course_info_json", "[]")))
        settled = []
        for course in courses:
            course_id = str(course.get("id"))
            result = settle_course_exam(
                CourseExamInput(
                    id=course_id,
                    name=str(course.get("name") or course_id),
                    credits=float(course.get("credits", 1)),
                    mastery=float(self.courses.get(course_id, 75)),
                ),
                modifier=5,
                luck_delta=0,
                fail_threshold=float(self.balance.fail_threshold),
            )
            settled.append(result)

        summary = settle_semester_exam(
            settled,
            self.stats,
            previous_highest_gpa=float(self.stats.get("highest_gpa", 0) or 0),
        )
        self.stats.update(
            {
                "gpa": summary.cgpa,
                "highest_gpa": summary.highest_gpa,
                "gpa_points_total": summary.gpa_points_total,
                "gpa_credits_total": summary.gpa_credits_total,
            }
        )
        self.exam_completed = True
        self.is_running = False
        next_index = int(self.stats.get("semester_idx", 1)) + 1
        major = str(self.stats.get("major_abbr") or "")
        self.ended = not bool(
            self.catalog.courses_for_semester(major, next_index)
        )
        return {
            "term_gpa": summary.term_gpa,
            "cgpa": summary.cgpa,
            "failed_count": summary.failed_count,
            "courses": [course.__dict__ for course in summary.courses],
            "ended": self.ended,
        }

    def _ensure_initialized(self) -> None:
        if not self.stats:
            self.initialize()

    def _semester_duration(self) -> int:
        tick = self.balance.raw.get("tick")
        if isinstance(tick, Mapping) and tick.get("semester_duration_seconds"):
            return int(tick["semester_duration_seconds"])
        return self.balance.get_semester_duration(
            int(self.stats.get("semester_idx", 1))
        )

    def _payload_defaults(self) -> RuntimePayloadDefaults:
        stats = self.stats_registry.by_id
        return RuntimePayloadDefaults(
            iq=stats["iq"].default,
            stress=stats["stress"].default,
            efficiency=stats.get("efficiency", stats["iq"]).default,
        )

    def _stat_bounds(self) -> dict[str, StatBounds]:
        return {
            stat.id: StatBounds(
                minimum=stat.min,
                maximum=stat.max,
                positive_endpoint=stat.positive_endpoint,
            )
            for stat in self.stats_registry.stats
        }

    def _apply_stat_delta(self, field_name: str, delta: int):
        """Apply one bounded numeric delta while preserving non-stat fields."""
        _, result = apply_delta_to_snapshot(
            self.stats,
            field_name,
            delta,
            self._stat_bounds(),
            self.stats_registry.feedback_labels,
        )
        self.stats[field_name] = result.value
        return result
