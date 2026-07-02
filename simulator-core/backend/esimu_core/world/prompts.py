"""Theme prompt-fragment loader for esimu-core.

Copyright (c) 2026 pirate-608. Licensed under the MIT License.
Prompt fragments are theme-owned text used by LLM-backed content generation.
They intentionally do not rename internal protocol IDs such as cc98/dingtalk.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from esimu_core.world.theme_paths import theme_dir


class PromptConfig(BaseModel):
    """Validated root object for `themes/<theme_id>/prompts.json`."""

    campus_context: str
    forum_name: str
    messenger_name: str
    forum_batch_instruction: str
    random_event_instruction: str
    messenger_batch_instruction: str
    private_chat_instruction: str
    player_identity_template: str
    messenger_scene_template: str
    messenger_open_template: str
    graduation_instruction: str
    forum_empty_fallback: str = "论坛暂无新帖。"
    forum_unavailable_fallback: str = "论坛暂时维护中。"


class ThemePrompts:
    """Load and expose active theme prompt fragments."""

    _config: PromptConfig | None = None
    _config_path: Path | None = None

    @staticmethod
    def resolve_config_path(config_path: str | Path | None = None) -> Path:
        """Resolve the active prompt-fragment path."""
        if config_path is not None:
            return Path(config_path)
        return theme_dir() / "prompts.json"

    def __init__(self, config_path: str | Path | None = None):
        if self._config is None:
            self.load(config_path)
        elif config_path is not None:
            self.load(config_path)

    def load(self, config_path: str | Path | None = None) -> None:
        """Load and validate active theme prompt fragments."""
        path = self.resolve_config_path(config_path)
        self._config_path = path
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        self._config = PromptConfig.model_validate(raw)

    def reload(self, config_path: str | Path | None = None) -> None:
        """Reload prompt fragments."""
        self._config = None
        self.load(config_path or self._config_path)

    @property
    def config(self) -> PromptConfig:
        """Return loaded prompt fragments, loading lazily if needed."""
        if self._config is None:
            self.load(self._config_path)
        assert self._config is not None
        return self._config


theme_prompts = ThemePrompts()
