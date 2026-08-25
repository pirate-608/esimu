"""Transport interfaces and optional OpenAI-compatible implementation."""

from __future__ import annotations

import inspect
from hashlib import sha256
from typing import Any, Mapping, Protocol, Sequence, cast

from esimu_core.ai.config import AIModelConfig


class ChatTransport(Protocol):
    """Minimal async chat-completion boundary consumed by esimu AI services."""

    async def complete(
        self,
        messages: Sequence[Mapping[str, str]],
        *,
        max_tokens: int = 500,
        temperature: float | None = None,
        top_p: float | None = None,
    ) -> str | None:
        """Return model text, or ``None`` when no usable choice is produced."""

    async def probe(self) -> bool:
        """Return whether the configured endpoint appears reachable."""

    async def close(self) -> None:
        """Release any client resources owned by this transport."""


class OpenAICompatibleTransport:
    """OpenAI SDK transport supporting generic and MiniMax role profiles.

    The SDK is imported lazily so the base ``esimu-core`` package remains usable
    without AI dependencies. Install ``esimu-core[ai]`` to construct this class.
    """

    def __init__(self, config: AIModelConfig, *, client: Any | None = None) -> None:
        self.config = config
        self._owns_client = client is None
        if client is not None:
            self._client = client
            return
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(
                "OpenAI transport requires the 'ai' extra: pip install esimu-core[ai]"
            ) from exc
        self._client = AsyncOpenAI(
            api_key=config.api_key or "not-required",
            base_url=config.base_url,
            timeout=config.timeout_seconds,
        )

    async def complete(
        self,
        messages: Sequence[Mapping[str, str]],
        *,
        max_tokens: int = 500,
        temperature: float | None = None,
        top_p: float | None = None,
    ) -> str | None:
        """Call ``chat.completions`` and normalize the first text choice."""
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": cast(Any, list(messages)),
        }
        token_key = (
            "max_completion_tokens"
            if self.config.role_profile == "minimax_m2her"
            else "max_tokens"
        )
        kwargs[token_key] = max_tokens
        if temperature is not None:
            kwargs["temperature"] = temperature
        if top_p is not None:
            kwargs["top_p"] = top_p
        response = await self._client.chat.completions.create(**kwargs)
        choices = getattr(response, "choices", None) or []
        if not choices:
            return None
        content = getattr(choices[0].message, "content", None)
        return content.strip() if isinstance(content, str) and content.strip() else None

    async def probe(self) -> bool:
        """Probe the endpoint through the SDK model-list surface."""
        if not self.config.is_configured:
            return False
        try:
            await self._client.models.list()
        except Exception:
            return False
        return True

    async def close(self) -> None:
        """Close clients created by this transport."""
        if not self._owns_client:
            return
        close = getattr(self._client, "close", None)
        if close is None:
            return
        result = close()
        if inspect.isawaitable(result):
            await result


class OpenAITransportRegistry:
    """Own shared platform transports while isolating player credentials.

    Applications explicitly choose ``shared`` for deployment-owned credentials
    and ``session`` for player-provided keys. Session transports are never kept
    in this registry and must be closed by their caller.
    """

    def __init__(self) -> None:
        self._shared: dict[
            tuple[str, str, str, str, float], OpenAICompatibleTransport
        ] = {}

    @staticmethod
    def _key(config: AIModelConfig) -> tuple[str, str, str, str, float]:
        secret_hash = sha256((config.api_key or "").encode("utf-8")).hexdigest()
        return (
            config.provider,
            config.model,
            config.base_url or "",
            secret_hash,
            config.timeout_seconds,
        )

    def shared(self, config: AIModelConfig) -> OpenAICompatibleTransport:
        """Return one reusable transport for application-owned credentials."""
        key = self._key(config)
        transport = self._shared.get(key)
        if transport is None:
            transport = OpenAICompatibleTransport(config)
            self._shared[key] = transport
        return transport

    def session(self, config: AIModelConfig) -> OpenAICompatibleTransport:
        """Return an uncached transport for session-sensitive credentials."""
        return OpenAICompatibleTransport(config)

    async def close(self) -> None:
        """Close all application-owned shared transports."""
        transports = list(self._shared.values())
        self._shared.clear()
        for transport in transports:
            await transport.close()
