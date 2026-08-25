"""Theme story-content loader for prologue and ending copy.

Copyright (c) 2026 pirate-608. Licensed under the MIT License.
Story content is intentionally separate from `theme.json`: theme manifests own
short nouns and identifiers, while this module validates longer narrative text.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from esimu_core.world.theme_paths import theme_dir

SceneTone = Literal["night", "morning", "sunset", "lake", "threshold"]


class PrologueSceneConfig(BaseModel):
    """Background image mapping for one prologue line index."""

    from_line: int = Field(ge=0)
    image: str
    tone: SceneTone

    @field_validator("image")
    @classmethod
    def validate_image(cls, value: str) -> str:
        """Reject path traversal and empty asset names."""
        image = value.strip()
        if not image or "/" in image or "\\" in image or ".." in image:
            raise ValueError("scene image must be a local public image filename")
        return image


class PrologueConfig(BaseModel):
    """Validated first-visit prologue copy and pacing inputs."""

    diary_title: str
    dedication_lines: list[str] = Field(min_length=1)
    diary_pages: list[list[str]] = Field(min_length=1)
    scenes: list[PrologueSceneConfig] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_lines_and_scenes(self) -> "PrologueConfig":
        """Ensure pages contain text and scene line indexes are reachable."""
        for page_index, page in enumerate(self.diary_pages):
            if not page:
                raise ValueError(f"diary_pages[{page_index}] cannot be empty")
            for line in page:
                if not line.strip():
                    raise ValueError("prologue lines cannot be empty")

        total_lines = len(self.dedication_lines) + sum(
            len(page) for page in self.diary_pages
        )
        previous = -1
        for scene in self.scenes:
            if scene.from_line >= total_lines:
                raise ValueError("scene.from_line must point to an existing line")
            if scene.from_line <= previous:
                raise ValueError("scenes must be sorted by increasing from_line")
            previous = scene.from_line
        return self


class EndingsConfig(BaseModel):
    """Validated end-screen copy and image names."""

    failure_date: str
    failure_title_lines: list[str] = Field(min_length=1)
    failure_default_reason: str
    failure_note: str
    graduation_kicker: str
    graduation_title: str
    graduation_line_low_gpa: str
    graduation_line_high_gpa: str
    graduation_summary_label: str
    graduation_fallback_summary: str
    graduation_background_images: list[str] = Field(min_length=1)

    @field_validator("graduation_background_images")
    @classmethod
    def validate_images(cls, values: list[str]) -> list[str]:
        """Reject path traversal and empty asset names."""
        for value in values:
            if not value.strip() or re.search(r"[\\/]|\.{2}", value):
                raise ValueError("ending background images must be filenames")
        return [value.strip() for value in values]


class StoryConfig(BaseModel):
    """Validated root object for `themes/<theme_id>/story.json`."""

    prologue: PrologueConfig
    endings: EndingsConfig

    def public_metadata(self) -> dict[str, Any]:
        """Return frontend-safe story metadata."""
        return self.model_dump()


class ThemeStory:
    """Load and expose the active theme story content."""

    _config: StoryConfig | None = None
    _config_path: Path | None = None

    @staticmethod
    def resolve_config_path(config_path: str | Path | None = None) -> Path:
        """Resolve the active story-content path."""
        if config_path is not None:
            return Path(config_path)
        return theme_dir() / "story.json"

    def __init__(self, config_path: str | Path | None = None):
        if self._config is None:
            self.load(config_path)
        elif config_path is not None:
            self.load(config_path)

    def load(self, config_path: str | Path | None = None) -> None:
        """Load and validate active theme story content from disk."""
        path = self.resolve_config_path(config_path)
        self._config_path = path
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        self._config = StoryConfig.model_validate(raw)

    def reload(self, config_path: str | Path | None = None) -> None:
        """Reload the story content."""
        self._config = None
        self.load(config_path or self._config_path)

    @property
    def config(self) -> StoryConfig:
        """Return loaded story content, loading lazily if needed."""
        if self._config is None:
            self.load(self._config_path)
        assert self._config is not None
        return self._config

    def public_metadata(self) -> dict[str, Any]:
        """Return metadata for frontend generation."""
        return self.config.public_metadata()
