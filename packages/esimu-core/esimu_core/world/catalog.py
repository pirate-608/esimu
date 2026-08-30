"""Theme world catalog loader for majors, courses, achievements, and libraries.

The catalog centralizes static world-data shape compatibility while staying
free of FastAPI, Redis, SQLAlchemy, WebSocket, and LLM client imports.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from esimu_core.world.theme_paths import world_dir


class WorldCatalog:
    """Read static JSON world data for one active or explicit theme."""

    def __init__(
        self,
        theme_id: str | None = None,
        world_path: str | Path | None = None,
    ) -> None:
        self.theme_id = theme_id
        self.world_dir = (
            Path(world_path).expanduser().resolve()
            if world_path is not None
            else world_dir(theme_id)
        )
        self.courses_dir = self.world_dir / "courses"

    def path(self, filename: str) -> Path:
        """Return a path inside this catalog's world directory."""
        return self.world_dir / filename

    def load_json(self, path: str | Path, default: Any = None) -> Any:
        """Load a JSON file, returning default when it is missing or invalid."""
        resolved = Path(path)
        if not resolved.exists():
            return default
        try:
            return json.loads(resolved.read_text(encoding="utf-8"))
        except Exception:
            return default

    def majors_raw(self) -> Any:
        """Return raw majors config."""
        return self.load_json(self.path("majors.json"), {})

    def majors(self) -> list[dict[str, Any]]:
        """Return majors as flat reference-app-compatible dictionaries."""
        raw = self.majors_raw()
        if isinstance(raw, list):
            candidates = raw
        elif isinstance(raw, dict):
            candidates = [
                major
                for group in raw.values()
                if isinstance(group, list)
                for major in group
            ]
        else:
            candidates = []

        return [
            self._normalize_major(major)
            for major in candidates
            if isinstance(major, dict)
        ]

    def course_plan_path(self, major_abbr: str) -> Path:
        """Return the course-plan path for a major identifier."""
        return self.courses_dir / f"{major_abbr}.json"

    def course_plan(self, major_abbr: str) -> dict[str, Any]:
        """Return a normalized course plan for a major identifier."""
        raw = self.load_json(self.course_plan_path(major_abbr), {})
        if isinstance(raw, list):
            semester_ids = sorted(
                {
                    max(1, int(course.get("semester", 1)))
                    for course in raw
                    if isinstance(course, dict)
                }
            )
            return {
                "major": major_abbr,
                "abbr": major_abbr,
                "plan": [
                    {
                        "semester": semester_id,
                        "courses": [
                            course
                            for course in raw
                            if isinstance(course, dict)
                            and max(1, int(course.get("semester", 1)))
                            == semester_id
                        ],
                    }
                    for semester_id in semester_ids
                ],
            }
        if isinstance(raw, dict):
            return raw
        return {}

    def plan_terms(self, course_plan: dict[str, Any]) -> list[dict[str, Any]]:
        """Return normalized semester entries from a course plan."""
        raw_terms = course_plan.get("semesters") or course_plan.get("plan") or []
        if not isinstance(raw_terms, list):
            return []
        return [term for term in raw_terms if isinstance(term, dict)]

    def courses_for_semester(
        self,
        major_abbr: str,
        semester_idx: int,
    ) -> list[dict[str, Any]]:
        """Return courses for a 1-based semester index."""
        terms = self.plan_terms(self.course_plan(major_abbr))
        if 0 < semester_idx <= len(terms):
            courses = terms[semester_idx - 1].get("courses") or []
            return [course for course in courses if isinstance(course, dict)]
        return []

    def major_assignment(self, major_abbr: str) -> dict[str, Any] | None:
        """Return major info, course plan, and first-term courses."""
        for major in self.majors():
            if major.get("abbr") == major_abbr or major.get("id") == major_abbr:
                abbr = str(major.get("abbr") or major_abbr)
                course_plan = self.course_plan(abbr)
                terms = self.plan_terms(course_plan)
                initial_courses = (
                    terms[0].get("courses", []) if terms else []
                )
                return {
                    "major_info": major,
                    "course_plan": course_plan,
                    "initial_courses": [
                        course
                        for course in initial_courses
                        if isinstance(course, dict)
                    ],
                }
        return None

    def achievements_raw(self) -> Any:
        """Return raw achievement config."""
        return self.load_json(self.path("achievements.json"), {})

    def achievements(self) -> dict[str, dict[str, Any]]:
        """Return achievements keyed by code, accepting dict or list configs."""
        raw = self.achievements_raw()
        if isinstance(raw, dict):
            return {
                str(code): data if isinstance(data, dict) else {}
                for code, data in raw.items()
            }
        if isinstance(raw, list):
            result: dict[str, dict[str, Any]] = {}
            for item in raw:
                if not isinstance(item, dict):
                    continue
                code = str(item.get("code") or item.get("id") or "").strip()
                if code:
                    result[code] = item
            return result
        return {}

    def event_library_path(self) -> Path:
        """Path to the local random-event library."""
        return self.path("event_library.json")

    def event_library(self) -> list[dict[str, Any]]:
        """Return local random-event entries."""
        raw = self.load_json(self.event_library_path(), [])
        return raw if isinstance(raw, list) else []

    def forum_library_path(self) -> Path:
        """Path to the local forum-compatible post library."""
        neutral_path = self.path("forum_library.json")
        if neutral_path.exists():
            return neutral_path
        return self.path("cc98_library.json")

    def forum_library(self) -> list[dict[str, Any]]:
        """Return local forum-compatible post entries."""
        raw = self.load_json(self.forum_library_path(), [])
        return raw if isinstance(raw, list) else []

    def query_embeddings_path(self) -> Path:
        """Path to precomputed query embeddings, if present."""
        return self.path("query_embeddings.json")

    @staticmethod
    def _normalize_major(raw: dict[str, Any]) -> dict[str, Any]:
        abbr = str(raw.get("abbr") or raw.get("id") or "").strip()
        return {
            **raw,
            "id": str(raw.get("id") or abbr),
            "name": str(raw.get("name") or abbr),
            "abbr": abbr,
            "iq_buff": int(raw.get("iq_buff", raw.get("iq_bonus", 0)) or 0),
            "stress_base": int(raw.get("stress_base", 0) or 0),
            "desc": str(raw.get("desc") or raw.get("description") or ""),
        }
