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
import time
from typing import Any, Mapping

from app.bootstrap import configure_project_environment

configure_project_environment()

from esimu_core.content import (  # noqa: E402
    compact_message_contacts,
    normalize_message_payload,
    select_local_event,
    select_local_forum_post,
    select_message_character,
)
from esimu_core.domain.achievements import (  # noqa: E402
    newly_unlocked_achievement_codes,
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
    achievement_details,
    build_initial_character_state,
    build_semester_reset_state,
)
from esimu_core.runtime.snapshot import (  # noqa: E402
    RuntimePayloadDefaults,
    build_init_payload_from_snapshot,
    build_tick_payload_from_snapshot,
)
from esimu_core.runtime.cooldowns import build_cooldown_map  # noqa: E402
from esimu_core.runtime.scheduling import (  # noqa: E402
    ContentScheduleDecision,
    scheduled_content_decision,
)
from esimu_core.runtime.state import RuntimeSnapshot  # noqa: E402
from esimu_core.world.balance import GameBalance  # noqa: E402
from esimu_core.world.catalog import WorldCatalog  # noqa: E402
from esimu_core.world.items import ItemCatalog  # noqa: E402
from esimu_core.world.stat_definitions import StatDefinitions  # noqa: E402
from esimu_core.world.story import ThemeStory  # noqa: E402
from esimu_core.world.theme import ThemeManifest  # noqa: E402
from esimu_core.world.theme_paths import active_theme_id  # noqa: E402


@dataclass
class StarterGameSession:
    """One in-memory player session for starter smoke runs."""

    username: str = "Starter Player"
    theme_id: str = field(default_factory=active_theme_id)
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
    tick_count: int = 0
    cooldown_timestamps: dict[str, float] = field(default_factory=dict)
    action_counts: dict[str, int] = field(default_factory=dict)
    achievements: list[str] = field(default_factory=list)
    completed_terms: int = 0
    last_exam: dict[str, Any] = field(default_factory=dict)
    content_mode: str = "library"
    ending_kind: str | None = None
    ending_reason: str | None = None

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
            "achievements": self.catalog.achievements(),
            "content_modes": ["library", "hybrid", "ai"],
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
        self.tick_count = 0
        self.cooldown_timestamps = {}
        self.action_counts = {}
        self.achievements = []
        self.completed_terms = 0
        self.last_exam = {}
        self.ending_kind = None
        self.ending_reason = None
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
            "tick_count": self.tick_count,
            "cooldown_timestamps": self.cooldown_timestamps,
            "action_counts": self.action_counts,
            "achievements": self.achievements,
            "completed_terms": self.completed_terms,
            "last_exam": self.last_exam,
            "content_mode": self.content_mode,
            "ending_kind": self.ending_kind,
            "ending_reason": self.ending_reason,
        }

    @classmethod
    def from_state(cls, state: Mapping[str, Any]) -> "StarterGameSession":
        """Restore a starter session from an adapter-owned state mapping."""
        session = cls(
            username=str(state.get("username") or "Starter Player"),
            theme_id=str(state.get("theme_id") or active_theme_id()),
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
        session.tick_count = int(state.get("tick_count", 0) or 0)
        session.cooldown_timestamps = {
            str(key): float(value)
            for key, value in dict(state.get("cooldown_timestamps") or {}).items()
        }
        session.action_counts = {
            str(key): int(value)
            for key, value in dict(state.get("action_counts") or {}).items()
        }
        session.achievements = [
            str(code) for code in list(state.get("achievements") or [])
        ]
        session.completed_terms = int(state.get("completed_terms", 0) or 0)
        session.last_exam = dict(state.get("last_exam") or {})
        mode = str(state.get("content_mode") or "library")
        session.content_mode = mode if mode in {"library", "hybrid", "ai"} else "library"
        session.ending_kind = str(state.get("ending_kind") or "") or None
        session.ending_reason = str(state.get("ending_reason") or "") or None
        session._normalize_messenger_state()
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
            relax_cooldowns=self.relax_cooldowns(),
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
                "content_mode": self.content_mode,
                "achievements": self.achievement_detail_payloads(),
                "ending_kind": self.ending_kind,
                "ending_reason": self.ending_reason,
                "current_event": self.last_event,
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
                "content_mode": self.content_mode,
                "achievements": self.achievement_detail_payloads(),
                "ending_kind": self.ending_kind,
                "ending_reason": self.ending_reason,
                "current_event": self.last_event,
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
        self.tick_count += 1
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
            self.ending_kind = "graduation"
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
        self.last_event = None
        self.ending_kind = None
        self.ending_reason = None
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
        """Compatibility helper that completes one deterministic reply inline."""
        pending = self.begin_messenger_reply(contact_id, option_id, content)
        return self.complete_messenger_reply(
            contact_id,
            {
                "content": f"我知道了。关于“{pending['player_message']}”，我们之后再聊。",
                "reply_options": ["继续聊聊", "稍后再说"],
            },
            expected_semester_idx=int(self.stats.get("semester_idx", 1) or 1),
        )

    def begin_messenger_reply(
        self,
        contact_id: str,
        option_id: str | None = None,
        content: str | None = None,
    ) -> dict[str, Any]:
        """Persist a player message immediately before background generation."""
        contacts = self.messenger_state.get("contacts") or {}
        contact = contacts.get(contact_id)
        if not isinstance(contact, dict):
            raise ValueError(f"unknown messenger contact: {contact_id}")
        if not contact.get("is_replyable", True):
            raise ValueError("this contact does not support replies")
        if not contact.get("round_open", True):
            raise ValueError("this conversation round has ended")
        if contact.get("awaiting_reply"):
            raise ValueError("this contact is already preparing a reply")
        options = list(contact.get("pending_options") or [])
        selected = next(
            (
                option
                for option in options
                if str(option.get("option_id") or option.get("id") or "")
                == str(option_id or "")
            ),
            options[0] if options else {"text": content or "收到"},
        )
        player_text = str(content or selected.get("text") or "收到")
        messages = contact.setdefault("messages", [])
        messages.append({"speaker": "player", "content": player_text})
        contact["pending_options"] = []
        contact["awaiting_reply"] = True
        contact["round_reply_count"] = int(contact.get("round_reply_count", 0)) + 1
        contact["last_active_at"] = time.time()
        self._record_action("messenger_reply")
        return {
            "contact_id": contact_id,
            "player_message": player_text,
            "reply_count": contact["round_reply_count"],
            "semester_idx": int(self.stats.get("semester_idx", 1) or 1),
            "character": self.character_for_contact(contact_id),
            "history": list(messages),
            "state": self.messenger_state,
        }

    def complete_messenger_reply(
        self,
        contact_id: str,
        generated: Mapping[str, Any] | None,
        *,
        expected_semester_idx: int | None = None,
    ) -> dict[str, Any]:
        """Append an NPC reply, settle the third reply, and reopen options."""
        contacts = self.messenger_state.get("contacts") or {}
        contact = contacts.get(contact_id)
        if not isinstance(contact, dict):
            raise ValueError(f"unknown messenger contact: {contact_id}")
        if not contact.get("awaiting_reply"):
            raise ValueError("no messenger reply is pending")
        payload = dict(generated or {})
        npc_text = str(payload.get("content") or "收到，我们之后再聊。").strip()
        contact.setdefault("messages", []).append(
            {"speaker": "npc", "content": npc_text}
        )
        contact["awaiting_reply"] = False
        contact["unread_count"] = int(contact.get("unread_count", 0)) + 1
        contact["last_active_at"] = time.time()
        reply_count = int(contact.get("round_reply_count", 0))
        feedback: dict[str, Any] | None = None
        if reply_count >= 3:
            settlement = payload.get("settlement")
            settlement = settlement if isinstance(settlement, Mapping) else {}
            effects = settlement.get("effects")
            effects = effects if isinstance(effects, Mapping) else {}
            settlement_allowed = expected_semester_idx is None or (
                int(self.stats.get("semester_idx", 1) or 1)
                == expected_semester_idx
                and not self.exam_completed
                and not self.ended
            )
            changes: list[dict[str, Any]] = []
            for field_name, delta in (
                effects.items() if settlement_allowed else ()
            ):
                if field_name not in self.stats_registry.event_effect_fields:
                    continue
                result = self._apply_stat_delta(str(field_name), int(delta))
                if result.change:
                    changes.append(result.change.as_dict())
            feedback = {
                "desc": str(settlement.get("desc") or "这一轮对话结束了。"),
                "changes": changes,
            }
            contact["round_open"] = False
            contact["round_reply_count"] = 0
            contact["completed_rounds"] = int(contact.get("completed_rounds", 0)) + 1
            contact["pending_options"] = []
            self._record_action("messenger_round")
        else:
            options = payload.get("reply_options")
            normalized = normalize_message_payload(
                {
                    "contact": {
                        "sender": contact.get("sender"),
                        "role": contact.get("role"),
                    },
                    "content": npc_text,
                    "reply_options": options,
                }
            )
            contact["pending_options"] = [
                option.as_dict() for option in normalized.reply_options
            ]
        if feedback is not None:
            feedback["tick"] = self.tick_payload()
        return {
            "contact_id": contact_id,
            "npc_message": npc_text,
            "reply_options": contact["pending_options"],
            "feedback": feedback,
            "state": self.messenger_state,
        }

    def relax(self, action: str = "walk") -> dict[str, Any]:
        """Apply one configured relax action deterministically."""
        self._ensure_initialized()
        config = self.balance.relax_actions.get(action)
        if not isinstance(config, Mapping):
            raise ValueError(f"unknown relax action: {action}")
        remaining = self.relax_cooldowns().get(action, 0)
        if remaining > 0:
            raise ValueError(f"action is cooling down for {remaining} seconds")
        minimum_energy = int(config.get("min_energy_required", 0) or 0)
        if int(self.stats.get("energy", 0) or 0) < minimum_energy:
            raise ValueError(f"action requires at least {minimum_energy} energy")

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

        self.cooldown_timestamps[action] = time.time()
        self._record_action("relax")
        self._record_action(action)
        return {"action": action, "changes": changes, "tick": self.tick_payload()}

    def relax_cooldowns(self, *, now: float | None = None) -> dict[str, int]:
        """Return remaining configured cooldowns for every relax action."""
        return build_cooldown_map(
            tuple(self.balance.relax_actions),
            self.cooldown_timestamps,
            {
                action: self.balance.get_cooldown(action)
                for action in self.balance.relax_actions
            },
            time.time() if now is None else now,
        )

    def event(self) -> dict[str, Any]:
        """Select one local event from the active theme."""
        return self.accept_event(self.local_event())

    def local_event(self) -> dict[str, Any]:
        """Return one local event without changing active session state."""
        self._ensure_initialized()
        selected = select_local_event(
            self.catalog.event_library(),
            sanity=int(self.stats.get("sanity", 100)),
            stress=int(self.stats.get("stress", 0)),
            choose=lambda candidates: candidates[0],
        )
        if selected is None:
            raise ValueError("event library is empty")
        return selected.as_dict()

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
        self._record_action("event")
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
        self.last_event = None
        self._record_action("event_choice")
        return {
            "desc": str(effects.get("desc") or ""),
            "changes": changes,
            "tick": self.tick_payload(),
        }

    def forum_post(self) -> dict[str, str]:
        """Return one active-theme forum post."""
        result = self.local_forum_post()
        self._record_action("forum")
        return result

    def local_forum_post(self) -> dict[str, str]:
        """Return a local forum post without recording a player action."""
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
        character = self.next_messenger_character()
        if character is None:
            raise ValueError("no closed messenger contact is currently available")
        return self.accept_messenger_round(self.local_messenger_opening(character))

    def local_messenger_opening(
        self,
        character: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Build one deterministic opening without mutating contact state."""
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
        return {
            "contact": payload.contact.as_dict(),
            "content": payload.content,
            "reply_options": [option.as_dict() for option in payload.reply_options],
        }

    def accept_messenger_round(self, raw: Mapping[str, Any]) -> dict[str, Any]:
        """Store one normalized local or AI-generated messenger opening."""
        payload = normalize_message_payload(raw, contact_prefix="msg")
        contact = payload.contact.as_dict()
        contacts = self.messenger_state.setdefault("contacts", {})
        existing = contacts.get(contact["contact_id"])
        state = dict(existing) if isinstance(existing, Mapping) else {}
        messages = list(state.get("messages") or [])
        messages.append({"speaker": "npc", "content": payload.content})
        state.update(
            {
                **contact,
                "messages": messages[-50:],
                "pending_options": [
                    option.as_dict() for option in payload.reply_options
                ],
                "round_open": bool(contact.get("is_replyable"))
                and bool(payload.reply_options),
                "round_reply_count": 0,
                "completed_rounds": int(state.get("completed_rounds", 0)),
                "awaiting_reply": False,
                "unread_count": int(state.get("unread_count", 0)) + 1,
                "last_active_at": time.time(),
            }
        )
        contacts[contact["contact_id"]] = state
        self.messenger_state["contacts"] = compact_message_contacts(
            contacts,
            max_contacts=self.balance.dingtalk_max_contacts,
        )
        self._record_action("messenger")
        return {
            "contact": contact,
            "content": payload.content,
            "reply_options": [option.as_dict() for option in payload.reply_options],
            "state": self.messenger_state,
        }

    def next_messenger_character(self) -> dict[str, Any] | None:
        """Choose a new or reusable character using active-theme balance."""
        characters = self.catalog.load_json(self.catalog.path("characters.json"), [])
        if not isinstance(characters, list):
            return None
        selected = select_message_character(
            characters,
            self.messenger_state.get("contacts") or {},
            max_contacts=self.balance.dingtalk_max_contacts,
            reuse_probability=self.balance.dingtalk_reuse_closed_contact_probability,
        )
        return dict(selected) if selected is not None else None

    def first_character(self) -> dict[str, Any]:
        """Return one character through the compatibility helper."""
        return self.next_messenger_character() or {
            "name": "Guide",
            "role": "friend",
            "description": "Helpful.",
        }

    def character_for_contact(self, contact_id: str) -> dict[str, Any]:
        """Resolve a persisted contact back to its theme character definition."""
        contact = (self.messenger_state.get("contacts") or {}).get(contact_id) or {}
        sender = str(contact.get("sender") or "")
        role = str(contact.get("role") or "")
        characters = self.catalog.load_json(self.catalog.path("characters.json"), [])
        if isinstance(characters, list):
            for character in characters:
                if not isinstance(character, Mapping):
                    continue
                if str(character.get("name") or "") == sender and str(
                    character.get("role") or ""
                ) == role:
                    return dict(character)
        return {"name": sender or "Guide", "role": role or "friend"}

    def mark_messenger_read(self, contact_id: str) -> dict[str, Any]:
        """Clear one contact's unread marker and return current messenger state."""
        contact = (self.messenger_state.get("contacts") or {}).get(contact_id)
        if not isinstance(contact, dict):
            raise ValueError(f"unknown messenger contact: {contact_id}")
        contact["unread_count"] = 0
        return self.messenger_state

    def recover_pending_messenger_replies(self) -> int:
        """Make canceled/crashed reply tasks selectable again on reconnect."""
        recovered = 0
        contacts = self.messenger_state.get("contacts") or {}
        for contact in contacts.values():
            if not isinstance(contact, dict) or not contact.get("awaiting_reply"):
                continue
            contact["awaiting_reply"] = False
            contact["round_reply_count"] = max(
                0,
                int(contact.get("round_reply_count", 0) or 0) - 1,
            )
            normalized = normalize_message_payload(
                {
                    "contact": {
                        "sender": contact.get("sender"),
                        "role": contact.get("role"),
                    },
                    "content": "",
                    "reply_options": contact.get("pending_options") or [],
                }
            )
            contact["pending_options"] = [
                option.as_dict() for option in normalized.reply_options
            ]
            recovered += 1
        return recovered

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
        self._record_action("item_buy")
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
        self._record_action("item_sell")
        return self.items.state_payload(self.items_state)

    def final_exam(self) -> dict[str, Any]:
        """Settle one term with core semester/GPA helpers."""
        self._ensure_initialized()
        if self.exam_completed:
            raise ValueError("this semester has already been settled")
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
        if summary.failed_count:
            self._apply_stat_delta(
                "sanity",
                int(self.balance.fail_sanity_penalty) * summary.failed_count,
            )
        else:
            self._apply_stat_delta("sanity", int(self.balance.pass_all_bonus))
        exam_gold = self.items.calculate_exam_gold(
            summary.term_gpa,
            summary.failed_count,
        )
        self._apply_stat_delta("gold", exam_gold)
        self.exam_completed = True
        self.is_running = False
        self.completed_terms += 1
        self._record_action("exam")
        self.last_exam = {
            "term_gpa": summary.term_gpa,
            "failed_count": summary.failed_count,
        }
        next_index = int(self.stats.get("semester_idx", 1)) + 1
        major = str(self.stats.get("major_abbr") or "")
        self.ended = not bool(
            self.catalog.courses_for_semester(major, next_index)
        )
        if self.ended:
            self.ending_kind = "graduation"
        new_achievements = self.check_achievements()
        return {
            "term_gpa": summary.term_gpa,
            "cgpa": summary.cgpa,
            "failed_count": summary.failed_count,
            "courses": [course.__dict__ for course in summary.courses],
            "gold_earned": exam_gold,
            "achievements": new_achievements,
            "ended": self.ended,
        }

    def automatic_content_decision(self) -> ContentScheduleDecision:
        """Return automatic event/message work due after the latest tick."""
        events = self.balance.events
        messenger = events.get("messenger") or events.get("dingtalk") or {}
        return scheduled_content_decision(
            tick_count=self.tick_count,
            is_running=self.is_running,
            exam_completed=self.exam_completed,
            ended=self.ended,
            has_active_event=self.last_event is not None,
            random_event_config=events.get("random_event") or {},
            messenger_config=messenger,
        )

    def set_content_mode(self, mode: object, *, ai_available: bool) -> str:
        """Set a session-scoped content mode after adapter capability checks."""
        normalized = str(mode or "library").strip().lower()
        if normalized not in {"library", "hybrid", "ai"}:
            raise ValueError("mode must be library, hybrid, or ai")
        if normalized == "ai" and not ai_available:
            raise ValueError("AI mode is unavailable because no model is configured")
        self.content_mode = normalized
        return normalized

    def check_game_over(self) -> dict[str, Any] | None:
        """End the session when a configured fail threshold is reached."""
        if self.ending_kind == "game_over":
            return None
        config = self.balance.game_over_config
        checks = (
            ("sanity", "sanity_threshold", "lte"),
            ("stress", "stress_threshold", "gte"),
            ("energy", "energy_threshold", "lte"),
        )
        failed_field = ""
        for field_name, config_key, operator in checks:
            if config_key not in config:
                continue
            value = float(self.stats.get(field_name, 0) or 0)
            threshold = float(config[config_key])
            if (operator == "lte" and value <= threshold) or (
                operator == "gte" and value >= threshold
            ):
                failed_field = field_name
                break
        if not failed_field:
            return None
        label = self.stats_registry.feedback_labels.get(failed_field, failed_field)
        reason = f"{label}触及了无法继续的界限。"
        self.ended = True
        self.is_running = False
        self.ending_kind = "game_over"
        self.ending_reason = reason
        return {
            "reason": reason,
            "failure_default_reason": self.story.config.endings.failure_default_reason,
            "restartable": True,
            "stats": self.tick_payload()["stats"],
            "achievements": self.achievement_detail_payloads(),
        }

    def check_achievements(self) -> list[dict[str, str]]:
        """Unlock newly satisfied declarative achievements."""
        session_metrics = {
            "semester_idx": int(self.stats.get("semester_idx", 1) or 1),
            "completed_terms": self.completed_terms,
            "failed_count": int(self.last_exam.get("failed_count", 0) or 0),
            "term_gpa": float(self.last_exam.get("term_gpa", 0) or 0),
            "cumulative_gpa": float(self.stats.get("gpa", 0) or 0),
        }
        codes = newly_unlocked_achievement_codes(
            self.catalog.achievements(),
            unlocked=self.achievements,
            stats=self.stats,
            actions=self.action_counts,
            session=session_metrics,
        )
        self.achievements.extend(codes)
        return achievement_details(codes, self.catalog.achievements())

    def achievement_detail_payloads(self) -> list[dict[str, str]]:
        """Return details for every persisted achievement code."""
        return achievement_details(self.achievements, self.catalog.achievements())

    def record_action(self, action: str, amount: int = 1) -> None:
        """Record one neutral public action for declarative achievements."""
        self._record_action(action, amount)

    def _record_action(self, action: str, amount: int = 1) -> None:
        self.action_counts[action] = int(self.action_counts.get(action, 0)) + amount

    def _normalize_messenger_state(self) -> None:
        contacts = self.messenger_state.get("contacts")
        if not isinstance(contacts, Mapping):
            self.messenger_state = {"contacts": {}}
            return
        normalized: dict[str, dict[str, Any]] = {}
        for contact_id, raw in contacts.items():
            if not isinstance(raw, Mapping):
                continue
            contact = dict(raw)
            contact.setdefault("messages", [])
            contact.setdefault("pending_options", [])
            contact.setdefault("round_open", bool(contact.get("pending_options")))
            contact.setdefault("round_reply_count", 0)
            contact.setdefault("completed_rounds", int(contact.get("rounds", 0) or 0))
            contact.setdefault("awaiting_reply", False)
            contact.setdefault("unread_count", 0)
            contact.setdefault("last_active_at", 0.0)
            normalized[str(contact_id)] = contact
        self.messenger_state = {
            "contacts": compact_message_contacts(
                normalized,
                max_contacts=self.balance.dingtalk_max_contacts,
            )
        }
        self.recover_pending_messenger_replies()

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
