"""Precompiled event and CC98 library retrieval.

Copyright (c) 2026 pirate-608. Licensed under the MIT License.

Notes:
    Runtime selection avoids LLM calls by matching local JSON content against
    state ranges, tags, and recent event history.
"""

import json
import logging
import random
from typing import Any, Dict, List, Optional, Set

from esimu_core.content import select_local_event, select_local_forum_post
from esimu_core.world.catalog import WorldCatalog
from esimu_core.world.stat_definitions import stat_definitions

logger = logging.getLogger(__name__)

_catalog = WorldCatalog()


# ============================================================
# Random event library.
# ============================================================

_event_library: List[Dict[str, Any]] = []


def _stat_default(stat_id: str) -> int:
    return stat_definitions.by_id[stat_id].default


def _stat_range(stat_id: str) -> list[int]:
    definition = stat_definitions.by_id[stat_id]
    return [definition.min, definition.max]


def _load_event_library() -> List[Dict[str, Any]]:
    global _event_library
    if _event_library:
        return _event_library
    path = _catalog.event_library_path()
    if not path.exists():
        logger.warning("event_library.json not found at %s", path)
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            _event_library = json.load(f)
        logger.info("Loaded %d events from event_library.json", len(_event_library))
    except Exception as e:
        logger.error("Failed to load event_library.json: %s", e)
    return _event_library


def pick_random_event(
    sanity: int | None = None,
    stress: int | None = None,
    seen_ids: Optional[Set[str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Pick an unseen event from the precompiled library by player state range.

    The returned shape remains compatible with the LLM event payload and carries
    `id` for history-based deduplication:
    {"id": "evt_xxx", "title": ..., "desc": ..., "options": [...]}。
    """
    library = _load_event_library()
    if not library:
        return None

    # Return the clean LLM-compatible shape and expose `id` for deduplication.
    event = select_local_event(
        library,
        sanity=sanity,
        stress=stress,
        seen_ids=seen_ids,
        sanity_default=_stat_default("sanity"),
        stress_default=_stat_default("stress"),
        sanity_range=_stat_range("sanity"),
        stress_range=_stat_range("stress"),
        choose=random.choice,
    )
    return event.as_dict() if event else None


# ============================================================
# CC98 post library.
# ============================================================

_cc98_library: List[Dict[str, Any]] = []


def _load_cc98_library() -> List[Dict[str, Any]]:
    global _cc98_library
    if _cc98_library:
        return _cc98_library
    path = _catalog.forum_library_path()
    if not path.exists():
        logger.warning("cc98_library.json not found at %s", path)
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            _cc98_library = json.load(f)
        logger.info("Loaded %d posts from cc98_library.json", len(_cc98_library))
    except Exception as e:
        logger.error("Failed to load cc98_library.json: %s", e)
    return _cc98_library


def pick_cc98_post(
    effect: str = "neutral",
    trigger: str = "",
) -> Optional[str]:
    """
        Pick a CC98 post from the precompiled library by trigger and effect.

        Matching strategy:
            1) Filter by effect first.
            2) Prefer topic/content hits for the trigger.
            3) Fall back to a random effect-matched candidate.

    Returns:
        Post content, or None when the library is empty and LLM fallback should run.
    """
    library = _load_cc98_library()
    if not library:
        return None

    post = select_local_forum_post(
        library,
        effect=effect,
        trigger=trigger,
        fallback="CC98 帖子加载失败...",
        choose=random.choice,
    )
    return post.content if post else None

