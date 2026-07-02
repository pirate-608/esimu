"""Theme manifest loader for the simulator framework lab.

Theme manifests define user-facing nouns, storage prefixes, and asset paths.
They are intentionally small so early framework extraction can keep gameplay
logic unchanged while replacing ZJU-specific copy step by step.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from esimu_core.world.theme_paths import active_theme_id, theme_dir

logger = logging.getLogger(__name__)


class ThemeStorage(BaseModel):
    """Browser/runtime storage namespace settings."""

    prefix: str = "simlab"

    @field_validator("prefix")
    @classmethod
    def validate_prefix(cls, value: str) -> str:
        """Validate storage prefixes used for browser key names."""
        prefix = value.strip()
        if not re.fullmatch(r"[a-z][a-z0-9_]*", prefix):
            raise ValueError("storage.prefix must match [a-z][a-z0-9_]*")
        return prefix


class ThemeManifestConfig(BaseModel):
    """Validated root object for `themes/<theme_id>/theme.json`."""

    theme_id: str
    display_name: str
    locale: str = "zh-CN"
    terms: dict[str, str] = Field(default_factory=dict)
    storage: ThemeStorage = Field(default_factory=ThemeStorage)
    assets: dict[str, str] = Field(default_factory=dict)
    notes: str = ""

    @field_validator("theme_id")
    @classmethod
    def validate_theme_id(cls, value: str) -> str:
        """Validate theme IDs used in paths and save metadata."""
        theme_id = value.strip()
        if not re.fullmatch(r"[a-z][a-z0-9-]*", theme_id):
            raise ValueError("theme_id must match [a-z][a-z0-9-]*")
        return theme_id

    @field_validator("terms", "assets")
    @classmethod
    def validate_string_map(cls, value: dict[str, str]) -> dict[str, str]:
        """Normalize string maps and reject empty keys."""
        normalized: dict[str, str] = {}
        for raw_key, raw_value in value.items():
            key = str(raw_key).strip()
            if not key:
                raise ValueError("theme map keys cannot be empty")
            normalized[key] = str(raw_value)
        return normalized

    @model_validator(mode="after")
    def validate_required_terms(self) -> "ThemeManifestConfig":
        """Require the minimal nouns current framework surfaces need."""
        required = {"campus", "forum", "messenger", "player", "semester", "course", "item"}
        missing = sorted(required - set(self.terms))
        if missing:
            raise ValueError(f"missing theme terms: {', '.join(missing)}")
        return self

    def public_metadata(self) -> dict[str, Any]:
        """Return the frontend-safe metadata shape."""
        return {
            "themeId": self.theme_id,
            "displayName": self.display_name,
            "locale": self.locale,
            "terms": self.terms,
            "storage": self.storage.model_dump(),
            "assets": self.assets,
        }


class ThemeManifest:
    """Load and expose the active theme manifest."""

    _config: ThemeManifestConfig | None = None
    _config_path: Path | None = None

    @staticmethod
    def resolve_config_path(config_path: str | Path | None = None) -> Path:
        """Resolve the active theme manifest path."""
        if config_path is not None:
            return Path(config_path)
        return theme_dir() / "theme.json"

    def __init__(self, config_path: str | Path | None = None):
        if self._config is None:
            self.load(config_path)
        elif config_path is not None:
            self.load(config_path)

    def load(self, config_path: str | Path | None = None) -> None:
        """Load and validate the active theme manifest from disk."""
        path = self.resolve_config_path(config_path)
        self._config_path = path
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        self._config = ThemeManifestConfig.model_validate(raw)
        if self._config.theme_id != active_theme_id() and config_path is None:
            logger.warning(
                "Theme manifest id %s differs from active SIMULATOR_THEME %s",
                self._config.theme_id,
                active_theme_id(),
            )
        logger.info("Theme manifest loaded: %s", self._config.theme_id)

    def reload(self, config_path: str | Path | None = None) -> None:
        """Reload the theme manifest."""
        self._config = None
        self.load(config_path or self._config_path)

    @property
    def config(self) -> ThemeManifestConfig:
        """Return the loaded config, loading lazily if needed."""
        if self._config is None:
            self.load(self._config_path)
        assert self._config is not None
        return self._config

    @property
    def config_path(self) -> Path:
        """Return the current theme manifest path."""
        return self._config_path or self.resolve_config_path()

    def term(self, key: str, fallback: str = "") -> str:
        """Return a theme term with a fallback."""
        value = self.config.terms.get(key)
        return value if value is not None else fallback

    def public_metadata(self) -> dict[str, Any]:
        """Return metadata for frontend generation."""
        return self.config.public_metadata()


theme_manifest = ThemeManifest()


