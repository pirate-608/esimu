"""Optional esimu AI adapter for the starter backend.

The adapter loads credentials from environment variables and owns transport
lifecycle. Session state and deterministic library fallbacks remain in the
starter application.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, TypeVar

from esimu_core.ai import (
    AIContentService,
    OpenAICompatibleTransport,
    ResolvedContent,
    generic_model_config_from_env,
    resolve_content,
    roleplay_model_config_from_env,
)
from esimu_core.ai.policy import ContentMode

from app.session import StarterGameSession

logger = logging.getLogger(__name__)
T = TypeVar("T")


def _content_mode() -> ContentMode:
    raw = os.getenv("ESIMU_CONTENT_MODE", "library").strip().lower()
    return raw if raw in {"library", "hybrid", "ai"} else "library"  # type: ignore[return-value]


@dataclass
class StarterAIAdapter:
    """Bridge optional model generation into deterministic starter sessions."""

    service: AIContentService | None
    mode: ContentMode = "library"
    hybrid_ai_probability: float = 0.35

    @classmethod
    def from_env(cls, theme_id: str = "demo-campus") -> "StarterAIAdapter":
        """Build transports only when the environment configures a model."""
        mode = _content_mode()
        generic_config = generic_model_config_from_env()
        roleplay_config = roleplay_model_config_from_env()
        if mode == "library" or not (
            generic_config.is_configured or roleplay_config.is_configured
        ):
            return cls(service=None, mode=mode)
        generic = (
            OpenAICompatibleTransport(generic_config)
            if generic_config.is_configured
            else None
        )
        roleplay = (
            OpenAICompatibleTransport(roleplay_config)
            if roleplay_config.is_configured
            else None
        )
        probability_raw = os.getenv("ESIMU_HYBRID_AI_PROBABILITY", "0.35")
        try:
            probability = float(probability_raw)
        except ValueError:
            probability = 0.35
        return cls(
            service=AIContentService.for_theme(
                generic,
                theme_id,
                roleplay_transport=roleplay,
            ),
            mode=mode,
            hybrid_ai_probability=max(0.0, min(1.0, probability)),
        )

    @property
    def enabled(self) -> bool:
        """Return whether starter actions may attempt model generation."""
        return self.service is not None and self.mode != "library"

    async def close(self) -> None:
        """Release optional SDK clients during FastAPI shutdown."""
        if self.service is not None:
            await self.service.close()

    async def _resolve(
        self,
        ai_factory: Callable[[], T | Awaitable[T] | None],
        library_factory: Callable[[], T | Awaitable[T] | None],
    ) -> ResolvedContent[T]:
        result = await resolve_content(
            self.mode,
            ai_factory=ai_factory if self.service is not None else None,
            library_factory=library_factory,
            hybrid_ai_probability=self.hybrid_ai_probability,
        )
        if result.degraded:
            logger.warning("AI content degraded to local library: %s", result.error)
        return result

    async def event(self, session: StarterGameSession) -> dict[str, Any]:
        """Resolve one AI/local event and update the session's active event."""
        service = self.service

        async def generate() -> dict[str, Any] | None:
            if service is None:
                return None
            return await service.generate_random_event(session.stats)

        result = await self._resolve(generate, session.event)
        if result.value is None:
            return session.event()
        if result.source == "ai":
            return session.accept_event(result.value)
        return result.value

    async def forum_post(self, session: StarterGameSession) -> dict[str, str]:
        """Resolve one AI/local forum post."""
        service = self.service

        async def generate() -> dict[str, str] | None:
            if service is None:
                return None
            return await service.generate_forum_post(
                session.stats,
                effect="positive",
                trigger="campus life",
            )

        result = await self._resolve(generate, session.forum_post)
        return result.value or session.forum_post()

    async def messenger_round(self, session: StarterGameSession) -> dict[str, Any]:
        """Resolve one AI/local messenger opening and store its contact state."""
        service = self.service
        character = session.first_character()

        async def generate() -> dict[str, Any] | None:
            if service is None:
                return None
            return await service.generate_message_opening(character, session.stats)

        result = await self._resolve(generate, session.messenger_round)
        if result.value is None:
            return session.messenger_round()
        if result.source == "ai":
            return session.accept_messenger_round(result.value)
        return result.value

    async def graduation_summary(self, session: StarterGameSession) -> str:
        """Generate a final summary or return the theme-owned fallback prose."""
        service = self.service
        fallback = session.story.config.endings.graduation_fallback_summary

        async def generate() -> str | None:
            if service is None:
                return None
            return await service.generate_graduation_summary(session.stats)

        result = await self._resolve(generate, lambda: fallback)
        return result.value or fallback
