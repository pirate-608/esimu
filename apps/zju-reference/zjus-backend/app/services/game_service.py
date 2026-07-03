"""Game lifecycle orchestration service.

Copyright (c) 2026 pirate-608. Licensed under the MIT License.
`GameService` prepares new/loaded contexts, initializes majors, and advances
semesters while coordinating Redis state and PostgreSQL persistence.
"""

import logging
from typing import Any, Dict, Optional

from esimu_core.domain.semester import recover_toward_baseline  # noqa: E402
from esimu_core.lifecycle import (
    build_initial_character_state,
    build_semester_reset_state,
)
from esimu_core.world.items import items
from esimu_core.world.stat_definitions import stat_definitions
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.input_safety import safe_username_for_prompt
from app.repositories.redis_repo import RedisRepository
from app.schemas.game_state import PlayerStats
from app.services.save_service import SaveService
from app.services.world_service import WorldService

logger = logging.getLogger(__name__)


class GameService:
    """Coordinate game lifecycle operations outside the real-time engine."""

    def __init__(self, user_id: str, repo: RedisRepository, world: WorldService):
        self.user_id = user_id
        self.repo = repo
        self.world = world

    @staticmethod
    def recover_energy_for_new_semester(current_energy: Any) -> int:
        """Recover halfway from current energy toward the configured baseline."""
        energy_stat = stat_definitions.by_id["energy"]
        return recover_toward_baseline(
            current_energy,
            baseline=energy_stat.default,
            minimum=energy_stat.min,
        )

    async def prepare_game_context(
        self,
        username: str,
        db: AsyncSession = None, # type: ignore
        save_slot: int = 1,
        force_load_save: bool = False,
    ) -> Dict[str, Any]:
        """Load an existing active/save-slot context or report a new game.

        Args:
            username: Current player's prompt-safe username.
            db: Optional database session used to restore persistent saves.
            save_slot: Save slot to load when PostgreSQL persistence is used.
            force_load_save: Skip active Redis reuse and require a DB save.

        Returns:
            A status/data pair consumed by the WebSocket startup route.
        """
        if force_load_save and db:
            loaded = await SaveService.load_from_db(
                self.user_id, self.repo, db, save_slot=save_slot
            )
            if loaded:
                return {
                    "data": await self.repo.get_all_game_data(),
                    "status": "loaded",
                }
            return {"data": None, "status": "missing_save"}

        if await self.repo.exists():
            return {
                "data": await self.repo.get_all_game_data(),
                "status": "existing",
            }

        if db:
            loaded = await SaveService.load_from_db(
                self.user_id, self.repo, db, save_slot=save_slot
            )
            if loaded:
                return {
                    "data": await self.repo.get_all_game_data(),
                    "status": "loaded",
                }

        return {"data": None, "status": "new"}

    async def assign_major_and_init(
        self,
        major_abbr: str,
        stat_overrides: Optional[Dict[str, int]] = None,
        username: str = "",
    ) -> Dict[str, Any]:
        """Initialize a new game with a major and registry-validated stats."""
        assignment = await self.world.get_major_by_abbr(major_abbr)
        if not assignment:
            raise ValueError(f"专业 {major_abbr} 不存在")

        major_info = assignment["major_info"]
        overrides = stat_definitions.normalize_initial_allocations(
            stat_overrides or {},
            allow_missing=True,
        )

        safe_username = safe_username_for_prompt(username)
        initial_stats = PlayerStats.build_initial(username=safe_username).model_dump()
        lifecycle_state = build_initial_character_state(
            username=safe_username,
            major_info=major_info,
            course_plan=assignment["course_plan"],
            initial_courses=assignment["initial_courses"],
            stat_defaults=stat_definitions.default_stats(),
            allocated_stats=overrides,
            initial_gold=items.initial_gold,
        )
        initial_stats.update(lifecycle_state.stats_update)

        await self.repo.set_game_data(
            stats=initial_stats,
            courses=lifecycle_state.courses_mastery,
            states=lifecycle_state.course_states,
            achievements=[],
        )

        return lifecycle_state.summary

    async def reset_courses_for_new_semester(self, semester_idx: int):
        """Replace course state and recover energy for a newly entered semester."""
        snapshot = await self.repo.get_snapshot()
        stats = snapshot.stats.model_dump() or {}
        major_abbr = stats.get("major_abbr", "")
        my_courses = await self.world.get_semester_courses(major_abbr, semester_idx)

        energy_default = stat_definitions.by_id["energy"].default
        try:
            current_energy = int(stats.get("energy", energy_default))
        except (TypeError, ValueError):
            current_energy = energy_default
        lifecycle_state = build_semester_reset_state(
            semester_idx=semester_idx,
            courses=my_courses,
            current_energy=current_energy,
            energy_default=energy_default,
            energy_minimum=stat_definitions.by_id["energy"].min,
        )

        await self.repo.update_courses_and_states(
            stats_update=lifecycle_state.stats_update,
            courses=lifecycle_state.courses_mastery,
            states=lifecycle_state.course_states,
        )
        return lifecycle_state.summary

    async def process_semester_transition(
        self,
        db: AsyncSession,
        holiday_event_factory=None,
        save_slot: int = 1,
    ) -> Dict[str, Any]:
        """Advance to the next semester, auto-save, or return graduation state."""
        current_semester_idx = await self.repo.increment_semester()

        async def _autosave_current_state() -> bool:
            try:
                autosave_ok = await SaveService.persist_to_db(
                    self.repo, db, save_slot=save_slot
                )
                if autosave_ok:
                    logger.info(
                        "Auto-save at end of semester for user %s", self.user_id
                    )
                return autosave_ok
            except Exception as e:
                logger.error("Auto-save failed for user %s: %s", self.user_id, e)
                return False

        if current_semester_idx > 8:
            snapshot = await self.repo.get_snapshot()
            stats = snapshot.stats.model_dump()
            achievements = list(await self.repo.get_unlocked_achievements())
            stats["achievements"] = achievements
            autosave_ok = await _autosave_current_state()
            return {
                "status": "graduated",
                "semester_idx": current_semester_idx,
                "stats": stats,
                "autosave_ok": autosave_ok,
            }

        semester_reset = await self.reset_courses_for_new_semester(current_semester_idx)
        holiday_event = None
        if holiday_event_factory is not None:
            holiday_event = await holiday_event_factory(
                {"context": "假期", "semester": current_semester_idx}
            )

        autosave_ok = await _autosave_current_state()
        return {
            "status": "continued",
            "semester_idx": current_semester_idx,
            "energy_recovery": semester_reset.get("energy_recovery", {}),
            "holiday_event": holiday_event,
            "autosave_ok": autosave_ok,
        }


