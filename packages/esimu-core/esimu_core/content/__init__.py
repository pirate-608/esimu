"""Theme-neutral content and message contracts for esimu adapters.

Copyright (c) 2026 pirate-608. Licensed under the MIT License.

The module owns deterministic payload shaping for local events, forum posts,
and messenger-like private conversations. It deliberately avoids Redis,
FastAPI, WebSocket, SQLAlchemy, and LLM clients; adapters remain responsible
for storage, networking, model calls, and legacy protocol IDs.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Literal, Mapping, Sequence

ContentConcept = Literal["feed", "forum", "messenger"]
MessageSpeaker = Literal["npc", "player", "system"]

LEGACY_CONCEPT_IDS: dict[str, ContentConcept] = {
    "cc98": "forum",
    "dingtalk": "messenger",
}

CONCEPT_LEGACY_IDS: dict[ContentConcept, str] = {
    "feed": "event",
    "forum": "cc98",
    "messenger": "dingtalk",
}

REPLYABLE_MESSAGE_ROLES = {
    "roommate",
    "classmate",
    "friend",
    "teaching_assistant",
    "teacher",
    "crush",
}

MESSAGE_ROLE_ALIASES = {
    "student": "classmate",
    "students": "classmate",
    "同学": "classmate",
    "同班同学": "classmate",
    "室友": "roommate",
    "舍友": "roommate",
    "roomie": "roommate",
    "ta": "teaching_assistant",
    "assistant": "teaching_assistant",
    "助教": "teaching_assistant",
    "老师": "teacher",
    "教师": "teacher",
    "朋友": "friend",
    "好友": "friend",
    "crush": "crush",
    "暗恋对象": "crush",
}

DEFAULT_REPLY_OPTIONS: dict[str, tuple[str, ...]] = {
    "roommate": ("哈哈收到", "我马上看看", "你先别急"),
    "classmate": ("可以，我看一下", "等我整理一下资料", "我也有点懵"),
    "friend": ("晚上再说？", "可以啊", "你这也太会了"),
    "teaching_assistant": ("谢谢助教提醒", "我有个问题想问", "我会尽快完成"),
    "teacher": ("谢谢老师", "我会提前准备", "我还有一个问题"),
    "crush": ("还好，你呢？", "我也在想这个", "要不要一起去？"),
}


@dataclass(frozen=True)
class EventPayload:
    """Adapter-facing random-event payload."""

    event_id: Any
    title: str
    desc: str
    options: list[Any]

    def as_dict(self) -> dict[str, Any]:
        """Return the legacy-compatible dictionary shape."""
        return {
            "id": self.event_id,
            "title": self.title,
            "desc": self.desc,
            "options": self.options,
        }


@dataclass(frozen=True)
class ForumPostPayload:
    """Adapter-facing local forum post payload."""

    content: str
    effect: str = ""
    trigger: str = ""

    def as_dict(self) -> dict[str, str]:
        """Return a JSON-friendly forum-post payload."""
        return {
            "content": self.content,
            "effect": self.effect,
            "trigger": self.trigger,
        }


@dataclass(frozen=True)
class ReplyOption:
    """One player-selectable private-message reply option."""

    option_id: str
    text: str

    def as_dict(self) -> dict[str, str]:
        """Return the reference-app reply option shape."""
        return {"option_id": self.option_id, "text": self.text}


@dataclass(frozen=True)
class MessageContactPayload:
    """Normalized private-message contact metadata."""

    contact_id: str
    sender: str
    role: str
    is_replyable: bool
    is_urgent: bool = False

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly contact payload."""
        return {
            "contact_id": self.contact_id,
            "sender": self.sender,
            "role": self.role,
            "is_replyable": self.is_replyable,
            "is_urgent": self.is_urgent,
        }


@dataclass(frozen=True)
class MessagePayload:
    """Normalized opening private-message payload."""

    contact: MessageContactPayload
    content: str
    reply_options: list[ReplyOption]


@dataclass(frozen=True)
class SanitizedEffects:
    """Normalized stat/gold effects for a conversation settlement."""

    desc: str
    effects: dict[str, int]


def framework_concept_for_legacy(value: str) -> ContentConcept:
    """Map adapter legacy IDs to framework-facing content concepts."""
    normalized = str(value or "").strip().lower()
    return LEGACY_CONCEPT_IDS.get(normalized, normalized)  # type: ignore[return-value]


def legacy_id_for_concept(concept: ContentConcept) -> str:
    """Return the current reference-app legacy ID for a content concept."""
    return CONCEPT_LEGACY_IDS[concept]


def theme_term_for_concept(
    concept_or_legacy: str,
    terms: Mapping[str, str],
    fallback: str = "",
) -> str:
    """Return a visible theme term for a framework concept or legacy ID."""
    concept = framework_concept_for_legacy(concept_or_legacy)
    return str(terms.get(concept) or fallback or concept)


def normalize_event_entry(raw: Mapping[str, Any]) -> EventPayload:
    """Normalize a local/LLM event entry into the adapter-facing shape."""
    return EventPayload(
        event_id=raw.get("id"),
        title=str(raw.get("title") or ""),
        desc=str(raw.get("desc") or raw.get("description") or ""),
        options=list(raw.get("options") or []),
    )


def select_local_event(
    library: Sequence[Mapping[str, Any]],
    *,
    sanity: int | None = None,
    stress: int | None = None,
    seen_ids: Iterable[str] | None = None,
    sanity_default: int = 100,
    stress_default: int = 0,
    sanity_range: Sequence[int] = (0, 200),
    stress_range: Sequence[int] = (0, 200),
    choose: Callable[[Sequence[Mapping[str, Any]]], Mapping[str, Any]] | None = None,
) -> EventPayload | None:
    """Select a local random event by player state and recent history."""
    if not library:
        return None
    sanity_value = sanity_default if sanity is None else sanity
    stress_value = stress_default if stress is None else stress
    seen = set(seen_ids or ())
    candidates: list[Mapping[str, Any]] = []
    for event in library:
        if event.get("id") in seen:
            continue
        event_sanity_range = event.get("sanity_range", sanity_range)
        event_stress_range = event.get("stress_range", stress_range)
        if (
            _range_contains(event_sanity_range, sanity_value)
            and _range_contains(event_stress_range, stress_value)
        ):
            candidates.append(event)

    if not candidates:
        candidates = [event for event in library if event.get("id") not in seen]
    if not candidates:
        return None

    chooser = choose or random.choice
    return normalize_event_entry(chooser(candidates))


def normalize_forum_entry(raw: Mapping[str, Any], fallback: str) -> ForumPostPayload:
    """Normalize a local forum-library entry into visible content."""
    return ForumPostPayload(
        content=str(raw.get("content") or fallback),
        effect=str(raw.get("effect") or ""),
        trigger=str(raw.get("trigger") or raw.get("topic") or ""),
    )


def normalize_forum_post(raw: Mapping[str, Any], fallback: str) -> str:
    """Return only visible forum post content for legacy adapter callers."""
    return normalize_forum_entry(raw, fallback).content


def select_local_forum_post(
    library: Sequence[Mapping[str, Any]],
    *,
    effect: str = "neutral",
    trigger: str = "",
    fallback: str,
    choose: Callable[[Sequence[Mapping[str, Any]]], Mapping[str, Any]] | None = None,
) -> ForumPostPayload | None:
    """Select a local forum post by effect and optional trigger text."""
    if not library:
        return None

    candidates = [post for post in library if post.get("effect") == effect]
    if not candidates:
        candidates = list(library)

    trigger_norm = str(trigger or "").strip().lower()
    if trigger_norm:
        compact_trigger = trigger_norm.replace(" ", "")
        trigger_hits = []
        for post in candidates:
            topic = str(post.get("topic") or post.get("trigger") or "").lower()
            content = str(post.get("content") or "").lower()
            compact_topic = topic.replace(" ", "")
            compact_content = content.replace(" ", "")
            if (
                trigger_norm in topic
                or trigger_norm in content
                or compact_trigger in compact_topic
                or compact_trigger in compact_content
            ):
                trigger_hits.append(post)
        if trigger_hits:
            candidates = trigger_hits

    chooser = choose or random.choice
    return normalize_forum_entry(chooser(candidates), fallback)


def normalize_message_role(role: str) -> str:
    """Normalize human-facing role aliases into canonical message role IDs."""
    normalized = str(role or "unknown").strip().lower()
    return MESSAGE_ROLE_ALIASES.get(normalized, normalized)


def build_message_contact_id(sender: str, role: str, *, prefix: str = "msg") -> str:
    """Build a deterministic contact ID from a sender name and role."""
    raw = f"{normalize_message_role(role)}:{sender.strip()}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def select_message_character(
    characters: Sequence[Mapping[str, Any]],
    contacts: Mapping[str, Mapping[str, Any]],
    *,
    max_contacts: int,
    reuse_probability: float,
    random_value: Callable[[], float] = random.random,
    choose: Callable[[Sequence[Mapping[str, Any]]], Mapping[str, Any]] = random.choice,
) -> Mapping[str, Any] | None:
    """Balance new-character diversity against reusable closed contacts."""
    available = [item for item in characters if isinstance(item, Mapping)]
    if not available:
        return None
    reusable_contacts = [
        contact
        for contact in contacts.values()
        if isinstance(contact, Mapping) and not bool(contact.get("round_open"))
    ]
    reusable_contacts.sort(key=lambda item: float(item.get("last_active_at", 0) or 0))
    existing_ids = set(contacts)
    unused = [
        character
        for character in available
        if build_message_contact_id(
            str(character.get("name") or "NPC"),
            str(character.get("role") or "unknown"),
        )
        not in existing_ids
    ]

    should_reuse = bool(reusable_contacts) and (
        len(existing_ids) >= max(1, int(max_contacts))
        or random_value() < max(0.0, min(1.0, float(reuse_probability)))
    )
    if should_reuse:
        contact = reusable_contacts[0]
        sender = str(contact.get("sender") or "")
        role = normalize_message_role(str(contact.get("role") or "unknown"))
        matches = [
            character
            for character in available
            if str(character.get("name") or "") == sender
            and normalize_message_role(str(character.get("role") or "unknown"))
            == role
        ]
        if matches:
            return choose(matches)
    if unused and len(existing_ids) < max(1, int(max_contacts)):
        return choose(unused)
    if reusable_contacts:
        contact = reusable_contacts[0]
        sender = str(contact.get("sender") or "")
        return next(
            (item for item in available if str(item.get("name") or "") == sender),
            None,
        )
    return None


def compact_message_contacts(
    contacts: Mapping[str, Mapping[str, Any]],
    *,
    max_contacts: int,
) -> dict[str, dict[str, Any]]:
    """Drop the oldest closed contacts while preserving open conversations."""
    normalized = {
        str(contact_id): dict(contact)
        for contact_id, contact in contacts.items()
        if isinstance(contact, Mapping)
    }
    limit = max(1, int(max_contacts))
    if len(normalized) <= limit:
        return normalized
    removable = sorted(
        (
            (contact_id, contact)
            for contact_id, contact in normalized.items()
            if not bool(contact.get("round_open"))
        ),
        key=lambda item: float(item[1].get("last_active_at", 0) or 0),
    )
    for contact_id, _contact in removable:
        if len(normalized) <= limit:
            break
        normalized.pop(contact_id, None)
    return normalized


def is_replyable_message_role(role: str) -> bool:
    """Return whether a normalized role supports player replies."""
    return normalize_message_role(role) in REPLYABLE_MESSAGE_ROLES


def coerce_reply_options(
    raw_options: Any,
    role: str,
    *,
    max_options: int = 3,
    max_text_length: int = 80,
) -> list[ReplyOption]:
    """Normalize reply options and provide role-specific fallbacks."""
    normalized_role = normalize_message_role(role)
    if not is_replyable_message_role(normalized_role):
        return []

    options: list[ReplyOption] = []
    if isinstance(raw_options, list):
        for idx, item in enumerate(raw_options[:max_options]):
            option_id = f"opt_{idx + 1}"
            text = ""
            if isinstance(item, str):
                text = item.strip()
            elif isinstance(item, Mapping):
                text = str(item.get("text") or item.get("content") or "").strip()
                if item.get("option_id"):
                    option_id = str(item.get("option_id"))
            elif hasattr(item, "text"):
                text = str(getattr(item, "text") or "").strip()
                raw_option_id = getattr(item, "option_id", "")
                if raw_option_id:
                    option_id = str(raw_option_id)
            if text:
                options.append(
                    ReplyOption(
                        option_id=option_id,
                        text=text[:max_text_length],
                    )
                )

    if options:
        return options

    fallback = DEFAULT_REPLY_OPTIONS.get(
        normalized_role,
        ("好的收到", "我想想怎么回", "可以再说详细点吗"),
    )
    return [
        ReplyOption(option_id=f"opt_{idx + 1}", text=text)
        for idx, text in enumerate(fallback[:max_options])
    ]


def normalize_message_payload(
    msg_data: Mapping[str, Any],
    *,
    contact_prefix: str = "msg",
    fallback_sender: str = "未知",
) -> MessagePayload:
    """Normalize raw LLM/library messenger data into contact and message parts."""
    contact_raw = msg_data.get("contact")
    contact = contact_raw if isinstance(contact_raw, Mapping) else {}
    sender = str(contact.get("sender") or msg_data.get("sender") or fallback_sender)
    role = normalize_message_role(
        str(contact.get("role") or msg_data.get("role") or "unknown")
    )
    contact_id = str(
        contact.get("contact_id")
        or build_message_contact_id(sender, role, prefix=contact_prefix)
    )
    is_urgent = bool(contact.get("is_urgent", msg_data.get("is_urgent", False)))

    content = ""
    message_raw = msg_data.get("message")
    if isinstance(message_raw, Mapping):
        content = str(message_raw.get("content") or "").strip()
    if not content:
        content = str(msg_data.get("content") or "").strip()

    options = coerce_reply_options(msg_data.get("reply_options"), role)
    if not is_replyable_message_role(role):
        options = []
    return MessagePayload(
        contact=MessageContactPayload(
            contact_id=contact_id,
            sender=sender,
            role=role,
            is_replyable=is_replyable_message_role(role),
            is_urgent=is_urgent,
        ),
        content=content,
        reply_options=options,
    )


def sanitize_effects(
    settlement: Any,
    allowed_fields: Mapping[str, int],
    *,
    empty_desc: str = "这轮对话没有产生明显影响。",
    default_desc: str = "这轮对话产生了一些影响。",
) -> SanitizedEffects:
    """Clamp stat/gold effects according to adapter-provided field limits."""
    if not isinstance(settlement, Mapping):
        return SanitizedEffects(desc=empty_desc, effects={})
    desc = str(settlement.get("desc") or default_desc).strip()
    effects_raw = settlement.get("effects")
    effects_raw = effects_raw if isinstance(effects_raw, Mapping) else {}
    effects: dict[str, int] = {}
    for key, value in effects_raw.items():
        field = str(key)
        max_delta = allowed_fields.get(field)
        if max_delta is None:
            continue
        try:
            delta = int(value)
        except (TypeError, ValueError):
            continue
        effects[field] = max(-max_delta, min(max_delta, delta))
    return SanitizedEffects(desc=desc, effects=effects)


def _range_contains(raw_range: Any, value: int) -> bool:
    """Return whether a raw two-number range contains an integer value."""
    if not isinstance(raw_range, Sequence) or len(raw_range) < 2:
        return True
    try:
        low = int(raw_range[0])
        high = int(raw_range[1])
    except (TypeError, ValueError):
        return True
    return low <= value <= high
