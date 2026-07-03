"""World-data loader for majors, courses, achievements, and static content.

Copyright (c) 2026 pirate-608. Licensed under the MIT License.
All gameplay world JSON/Markdown data is read through this service so runtime
code does not need to know whether it is running locally or in Docker.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from esimu_core.world.catalog import WorldCatalog

logger = logging.getLogger(__name__)


class WorldService:
    """Load static world data from the mounted or local world directory."""

    _static_cache: Dict[str, Any] = {}
    _cache_lock = asyncio.Lock()

    def __init__(self, theme_id: str | None = None):
        """Resolve world-data paths through the active esimu theme catalog."""
        self.catalog = WorldCatalog(theme_id)
        self.world_dir = self.catalog.world_dir
        self.majors_path = self.catalog.path("majors.json")
        self.courses_dir = self.catalog.courses_dir
        self.achievements_path = self.catalog.path("achievements.json")

    async def _load_json(self, path: Path) -> Any:
        """Load a JSON file with a process-wide async cache."""
        path_str = str(path)
        async with self._cache_lock:
            if path_str in self._static_cache:
                return self._static_cache[path_str]

            if not path.exists():
                logger.error("World data missing: %s", path)
                return {}

            loop = asyncio.get_running_loop()
            try:
                data = await loop.run_in_executor(
                    None,
                    self.catalog.load_json,
                    path,
                    {},
                )
                self._static_cache[path_str] = data
                return data
            except Exception as e:
                logger.error("Failed to parse %s: %s", path, e)
                return {}

    async def get_all_majors(self) -> List[Dict[str, Any]]:
        """Return all majors as a flat list, regardless of tier grouping."""
        return self.catalog.majors()

    async def get_major_by_abbr(self, abbr: str) -> Optional[Dict[str, Any]]:
        """Find one major and its first-semester courses by abbreviation."""
        return self.catalog.major_assignment(abbr)

    async def get_semester_courses(
        self, major_abbr: str, semester_idx: int
    ) -> List[Dict]:
        """Return the course list for a major and semester index."""
        return self.catalog.courses_for_semester(major_abbr, semester_idx)

    async def get_achievements(self) -> dict[str, dict[str, Any]]:
        """Return achievements keyed by code from the active theme."""
        return self.catalog.achievements()
