"""Theme-aware AI content generation extracted from ZJUers Simulator.

Copyright (c) 2026 pirate-608. Licensed under the MIT License.

This module owns prompt assembly, structured-output validation, generic model
fallbacks, and MiniMax M2-her role-message construction. Applications still own
credentials, persistence, content caches, character retrieval, and telemetry.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from esimu_core.ai.parsing import dict_list, json_object_from_text, string_list
from esimu_core.ai.transport import ChatTransport
from esimu_core.content import (
    coerce_reply_options,
    normalize_event_entry,
    normalize_message_payload,
    normalize_message_role,
    sanitize_effects,
)
from esimu_core.world.catalog import WorldCatalog
from esimu_core.world.prompts import PromptConfig, ThemePrompts
from esimu_core.world.stat_definitions import StatDefinitions

M2HER_ALLOWED_ROLES = {
    "system",
    "user_system",
    "group",
    "sample_message_ai",
    "sample_message_user",
    "user",
    "assistant",
}


def safe_prompt_value(
    value: object, *, fallback: str = "Player", limit: int = 120
) -> str:
    """Remove control characters and prompt delimiters from short identity data."""
    text = re.sub(r"[\x00-\x1f\x7f]", " ", str(value or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return (text or fallback)[:limit]


class AIContentService:
    """Generate framework content through one general and optional RP transport."""

    def __init__(
        self,
        transport: ChatTransport | None,
        prompts: PromptConfig,
        stats: StatDefinitions,
        *,
        roleplay_transport: ChatTransport | None = None,
    ) -> None:
        self.transport = transport
        self.roleplay_transport = roleplay_transport
        self.prompts = prompts
        self.stats = stats

    @classmethod
    def for_theme(
        cls,
        transport: ChatTransport | None,
        theme_id: str,
        *,
        roleplay_transport: ChatTransport | None = None,
    ) -> "AIContentService":
        """Build a service from one theme pack's prompt and stat contracts."""
        catalog = WorldCatalog(theme_id)
        prompts = ThemePrompts(catalog.world_dir.parent / "prompts.json").config
        stats = StatDefinitions(catalog.path("stat_definitions.json"))
        return cls(
            transport,
            prompts,
            stats,
            roleplay_transport=roleplay_transport,
        )

    async def available(self) -> bool:
        """Probe the general model endpoint."""
        return self.transport is not None and await self.transport.probe()

    async def close(self) -> None:
        """Close transports owned by the surrounding adapter."""
        if self.transport is not None:
            await self.transport.close()
        if (
            self.roleplay_transport is not None
            and self.roleplay_transport is not self.transport
        ):
            await self.roleplay_transport.close()

    def state_fragment(self, player_stats: Mapping[str, Any]) -> str:
        """Build a bounded model-facing state summary from the stat registry."""
        parts: list[str] = []
        for definition in self.stats.stats:
            if not definition.llm_context:
                continue
            value = definition.clamp(
                player_stats.get(definition.id, definition.default)
            )
            parts.append(f"{definition.label}={value}")
        for field, label in (("major", "major"), ("semester", "period")):
            if player_stats.get(field):
                parts.append(f"{label}={safe_prompt_value(player_stats[field])}")
        return ", ".join(parts)

    async def generate_forum_post(
        self,
        player_stats: Mapping[str, Any],
        *,
        effect: str = "neutral",
        trigger: str = "campus life",
    ) -> dict[str, str] | None:
        """Generate one theme-aware forum post from a small batch."""
        if self.transport is None:
            return None
        prompt = (
            f"Player state: {self.state_fragment(player_stats)}\n"
            f"{self.prompts.forum_batch_instruction}\n"
            f'The first post must relate to "{safe_prompt_value(trigger)}" '
            f"and have a {safe_prompt_value(effect)} tone.\n"
            'Return strict JSON: {"posts":["post 1","post 2","post 3"]}'
        )
        raw = await self.transport.complete(
            [{"role": "user", "content": prompt}], max_tokens=350
        )
        posts = string_list(json_object_from_text(raw).get("posts"), limit=3)
        if not posts:
            return None
        return {"content": posts[0][:1000], "effect": effect, "trigger": trigger}

    async def generate_random_event(
        self,
        player_stats: Mapping[str, Any],
        *,
        history: Sequence[str] = (),
    ) -> dict[str, Any] | None:
        """Generate and validate one random event with bounded registered effects."""
        if self.transport is None:
            return None
        allowed = "/".join(sorted(self.stats.event_effect_fields))
        history_hint = ", ".join(safe_prompt_value(item) for item in history[-5:])
        prompt = (
            f"Player state: {self.state_fragment(player_stats)}\n"
            f"Recent events to avoid: {history_hint or 'none'}\n"
            f"{self.prompts.random_event_instruction}\n"
            "Generate 1-3 events with two choices each. Effects must be integer "
            f"deltas from -10 to 10 and only use: {allowed}.\n"
            'Return strict JSON: {"events":[{"title":"...","desc":"...",'
            '"options":[{"id":"A","text":"...","effects":'
            '{"energy":-2,"desc":"..."}}]}]}'
        )
        raw = await self.transport.complete(
            [{"role": "user", "content": prompt}], max_tokens=900
        )
        events = dict_list(json_object_from_text(raw).get("events"), limit=3)
        for event in events:
            normalized = self._validated_event(event)
            if normalized is not None:
                return normalized
        return None

    async def generate_message_opening(
        self,
        character: Mapping[str, Any],
        player_stats: Mapping[str, Any],
        *,
        context: str = "daily campus life",
    ) -> dict[str, Any] | None:
        """Generate one NPC opening, using M2-her role messages when configured."""
        role = normalize_message_role(str(character.get("role") or "unknown"))
        transport = self.roleplay_transport or self.transport
        if transport is None:
            return None
        messages = (
            self._roleplay_messages(character, player_stats, context)
            if self.roleplay_transport is not None
            else self._generic_opening_messages(character, player_stats, context)
        )
        raw = await transport.complete(
            messages,
            max_tokens=360,
            temperature=1.0 if self.roleplay_transport is not None else None,
            top_p=0.95 if self.roleplay_transport is not None else None,
        )
        data = json_object_from_text(raw)
        content = str(
            data.get("content")
            or data.get("message")
            or data.get("npc_reply")
            or raw
            or ""
        ).strip()
        if not content:
            return None
        payload = normalize_message_payload(
            {
                "sender": character.get("name") or "NPC",
                "role": role,
                "content": content[:500],
                "reply_options": data.get("reply_options"),
            },
            contact_prefix="msg",
        )
        return {
            "contact": payload.contact.as_dict(),
            "content": payload.content,
            "message": {"speaker": "npc", "content": payload.content},
            "reply_options": [item.as_dict() for item in payload.reply_options],
        }

    async def generate_message_reply(
        self,
        character: Mapping[str, Any],
        player_stats: Mapping[str, Any],
        history: Sequence[Mapping[str, Any]],
        player_reply: str,
        *,
        reply_count: int,
    ) -> dict[str, Any] | None:
        """Generate an NPC reply and settle every third player reply."""
        role = normalize_message_role(str(character.get("role") or "unknown"))
        sender = safe_prompt_value(character.get("name"), fallback="NPC")
        history_lines = []
        for item in history[-8:]:
            speaker = "Player" if item.get("speaker") == "player" else sender
            content = safe_prompt_value(item.get("content"), fallback="", limit=300)
            if content:
                history_lines.append(f"{speaker}: {content}")
        should_settle = reply_count >= 3
        allowed = "/".join(sorted(self.stats.event_effect_fields))
        output_contract = (
            '{"npc_reply":"...","settlement":{"desc":"...","effects":{"sanity":1}}}'
            if should_settle
            else '{"npc_reply":"...","reply_options":["option 1","option 2"]}'
        )
        request = (
            f"Conversation history:\n{chr(10).join(history_lines)}\n"
            f"Player just replied: {safe_prompt_value(player_reply, limit=300)}\n"
            "Write the NPC's next natural reply. "
            + (
                f"Settle this three-reply round with restrained integer effects using only {allowed}. "
                if should_settle
                else "Also generate 2-3 short player reply options. "
            )
            + f"Return strict JSON: {output_contract}"
        )
        transport = self.roleplay_transport or self.transport
        if transport is None:
            return None
        messages = (
            self._roleplay_messages(character, player_stats, "private conversation")
            if self.roleplay_transport is not None
            else self._generic_opening_messages(
                character, player_stats, "private conversation"
            )[:-1]
        )
        messages.append({"role": "user", "content": request})
        raw = await transport.complete(messages, max_tokens=460)
        data = json_object_from_text(raw)
        content = str(data.get("npc_reply") or raw or "").strip()
        if not content:
            return None
        result: dict[str, Any] = {"content": content[:500]}
        if should_settle:
            limits = {field: 10 for field in self.stats.event_effect_fields}
            result["settlement"] = sanitize_effects(
                data.get("settlement"), limits
            ).__dict__
        else:
            result["reply_options"] = [
                item.as_dict()
                for item in coerce_reply_options(data.get("reply_options"), role)
            ]
        return result

    async def generate_graduation_summary(
        self,
        final_stats: Mapping[str, Any],
    ) -> str | None:
        """Generate the theme's final narrative summary."""
        if self.transport is None:
            return None
        prompt = (
            f"Final player state: {self.state_fragment(final_stats)}\n"
            f"{self.prompts.graduation_instruction}\n"
            "Return only the final narrative, without Markdown or JSON."
        )
        raw = await self.transport.complete(
            [{"role": "user", "content": prompt}], max_tokens=500
        )
        return raw.strip()[:2000] if isinstance(raw, str) and raw.strip() else None

    def _validated_event(self, raw: Mapping[str, Any]) -> dict[str, Any] | None:
        title = str(raw.get("title") or "").strip()
        desc = str(raw.get("desc") or raw.get("description") or "").strip()
        options_raw = dict_list(raw.get("options"), limit=3)
        options: list[dict[str, Any]] = []
        limits = {field: 10 for field in self.stats.event_effect_fields}
        for index, option in enumerate(options_raw):
            text = str(option.get("text") or "").strip()
            if not text:
                continue
            effects_raw = option.get("effects")
            settlement = {
                "desc": effects_raw.get("desc")
                if isinstance(effects_raw, Mapping)
                else "",
                "effects": effects_raw if isinstance(effects_raw, Mapping) else {},
            }
            effects = sanitize_effects(settlement, limits)
            options.append(
                {
                    "id": str(option.get("id") or chr(65 + index)),
                    "text": text[:200],
                    "effects": {**effects.effects, "desc": effects.desc},
                }
            )
        if not title or not desc or len(options) < 2:
            return None
        return normalize_event_entry(
            {
                "id": raw.get("id"),
                "title": title[:160],
                "desc": desc[:1000],
                "options": options,
            }
        ).as_dict()

    def _generic_opening_messages(
        self,
        character: Mapping[str, Any],
        player_stats: Mapping[str, Any],
        context: str,
    ) -> list[dict[str, str]]:
        sender = safe_prompt_value(character.get("name"), fallback="NPC")
        role = normalize_message_role(str(character.get("role") or "unknown"))
        persona = safe_prompt_value(
            character.get("content")
            or character.get("description")
            or character.get("personality"),
            fallback=f"You are {sender}.",
            limit=1000,
        )
        prompt = (
            f"{self.prompts.private_chat_instruction}\n"
            f"Player state: {self.state_fragment(player_stats)}\n"
            f"Context: {safe_prompt_value(context)}\n"
            f"NPC: {sender}; role: {role}; persona: {persona}\n"
            "Generate one natural opening message under 80 characters and 2-3 short reply options. "
            'Return strict JSON: {"content":"...","reply_options":["...","..."]}'
        )
        return [{"role": "user", "content": prompt}]

    def _roleplay_messages(
        self,
        character: Mapping[str, Any],
        player_stats: Mapping[str, Any],
        context: str,
    ) -> list[dict[str, str]]:
        sender = safe_prompt_value(character.get("name"), fallback="NPC")
        persona = safe_prompt_value(
            character.get("content")
            or character.get("description")
            or character.get("personality"),
            fallback=f"You are {sender}.",
            limit=1000,
        )
        username = safe_prompt_value(player_stats.get("username"), fallback="Player")
        major = safe_prompt_value(player_stats.get("major"), fallback="unknown major")
        semester = safe_prompt_value(
            player_stats.get("semester"), fallback="current period"
        )
        charm_def = self.stats.by_id.get("charm")
        charm = charm_def.clamp(player_stats.get("charm")) if charm_def else 0
        charm_label = charm_def.label if charm_def else "charm"
        identity = self.prompts.player_identity_template.format(
            major=major,
            username=username,
            semester=semester,
            charm_label=charm_label,
            charm=charm,
        )
        messages = [
            {"role": "system", "content": f"You are {sender}.\n{persona}"},
            {"role": "user_system", "content": identity},
            {
                "role": "group",
                "content": self.prompts.messenger_scene_template.format(
                    semester=semester,
                    scene=safe_prompt_value(context),
                ),
            },
        ]
        examples = character.get("examples")
        if isinstance(examples, list):
            for index, example in enumerate(examples[:3]):
                text = safe_prompt_value(example, fallback="", limit=300)
                if not text:
                    continue
                messages.append({"role": "sample_message_ai", "content": text})
                if index < min(len(examples), 3) - 1:
                    messages.append(
                        {"role": "sample_message_user", "content": "Understood."}
                    )
        messages.append(
            {
                "role": "user",
                "content": self.prompts.messenger_open_template.format(
                    username=username
                )
                + '\nReturn strict JSON: {"content":"...","reply_options":["...","..."]}',
            }
        )
        return [
            message for message in messages if message["role"] in M2HER_ALLOWED_ROLES
        ]
