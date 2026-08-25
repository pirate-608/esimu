"""Model configuration for the optional esimu AI integration.

Copyright (c) 2026 pirate-608. Licensed under the MIT License.
"""

from __future__ import annotations

import os
from typing import Literal, Mapping

from pydantic import BaseModel, Field, field_validator, model_validator

PROVIDER_BASE_URLS: dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "glm": "https://open.bigmodel.cn/api/paas/v4",
    "moonshot": "https://api.moonshot.cn/v1",
    "minimax": "https://api.minimaxi.com/v1",
    "ollama": "http://127.0.0.1:11434/v1",
}

RoleProfile = Literal["generic", "minimax_m2her"]


class AIModelConfig(BaseModel):
    """One OpenAI-compatible model endpoint without application persistence."""

    provider: str = "openai"
    model: str = "gpt-4o-mini"
    api_key: str | None = Field(default=None, repr=False)
    base_url: str | None = None
    timeout_seconds: float = Field(default=20.0, gt=0, le=300)
    role_profile: RoleProfile = "generic"

    @field_validator("provider", "model")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        """Normalize required model identifiers."""
        normalized = value.strip()
        if not normalized:
            raise ValueError("model provider/name cannot be empty")
        return normalized

    @field_validator("base_url")
    @classmethod
    def normalize_base_url(cls, value: str | None) -> str | None:
        """Accept both SDK base URLs and older full completion endpoints."""
        if value is None:
            return None
        normalized = value.strip().rstrip("/")
        for suffix in ("/chat/completions", "/text/chatcompletion_v2"):
            if normalized.endswith(suffix):
                normalized = normalized[: -len(suffix)].rstrip("/")
        return normalized or None

    @model_validator(mode="after")
    def fill_provider_url(self) -> "AIModelConfig":
        """Use a known provider URL when the caller omitted an override."""
        if self.base_url is None:
            self.base_url = PROVIDER_BASE_URLS.get(self.provider.lower())
        return self

    @property
    def is_configured(self) -> bool:
        """Return whether the endpoint has enough information to be attempted."""
        return bool(self.api_key or self.provider.lower() == "ollama")

    @classmethod
    def from_env(
        cls,
        prefix: str = "ESIMU_LLM",
        *,
        environ: Mapping[str, str] | None = None,
        default_provider: str = "openai",
        default_model: str = "gpt-4o-mini",
        role_profile: RoleProfile = "generic",
    ) -> "AIModelConfig":
        """Load a model endpoint from a namespaced environment mapping."""
        values = os.environ if environ is None else environ
        provider = values.get(f"{prefix}_PROVIDER", default_provider)
        timeout_raw = values.get(f"{prefix}_TIMEOUT_SECONDS", "20")
        try:
            timeout = float(timeout_raw)
        except ValueError:
            timeout = 20.0
        return cls(
            provider=provider,
            model=values.get(f"{prefix}_MODEL", default_model),
            api_key=values.get(f"{prefix}_API_KEY") or None,
            base_url=values.get(f"{prefix}_BASE_URL") or None,
            timeout_seconds=timeout,
            role_profile=role_profile,
        )


def generic_model_config_from_env(
    environ: Mapping[str, str] | None = None,
) -> AIModelConfig:
    """Load the framework's general content model configuration."""
    return AIModelConfig.from_env("ESIMU_LLM", environ=environ)


def roleplay_model_config_from_env(
    environ: Mapping[str, str] | None = None,
) -> AIModelConfig:
    """Load the optional MiniMax M2-her role-play model configuration."""
    return AIModelConfig.from_env(
        "ESIMU_RP",
        environ=environ,
        default_provider="minimax",
        default_model="M2-her",
        role_profile="minimax_m2her",
    )
