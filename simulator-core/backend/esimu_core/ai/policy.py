"""Content-mode fallback policy shared by simulator adapters."""

from __future__ import annotations

import inspect
import random
from dataclasses import dataclass
from typing import Awaitable, Callable, Generic, Literal, TypeVar

ContentMode = Literal["library", "hybrid", "ai"]
ContentSource = Literal["library", "ai", "fallback"]
T = TypeVar("T")


@dataclass(frozen=True)
class ResolvedContent(Generic[T]):
    """One resolved content value plus degradation metadata."""

    value: T | None
    source: ContentSource
    degraded: bool = False
    error: str | None = None


async def _call(factory: Callable[[], T | Awaitable[T] | None]) -> T | None:
    value = factory()
    if inspect.isawaitable(value):
        return await value
    return value


async def resolve_content(
    mode: ContentMode,
    *,
    ai_factory: Callable[[], T | Awaitable[T] | None] | None,
    library_factory: Callable[[], T | Awaitable[T] | None],
    hybrid_ai_probability: float = 0.35,
    random_value: Callable[[], float] = random.random,
) -> ResolvedContent[T]:
    """Resolve AI/library content with deterministic degradation semantics.

    Library mode never calls a model. AI mode tries the model first and falls
    back locally. Hybrid mode chooses AI with the configured probability and
    otherwise prefers the library, still using the other source if needed.
    """
    if mode not in {"library", "hybrid", "ai"}:
        raise ValueError(f"unsupported content mode: {mode}")
    probability = max(0.0, min(1.0, hybrid_ai_probability))
    ai_first = mode == "ai" or (
        mode == "hybrid" and ai_factory is not None and random_value() < probability
    )
    if mode == "library" or ai_factory is None:
        return ResolvedContent(await _call(library_factory), "library")

    first_name: ContentSource = "ai" if ai_first else "library"
    second_name: ContentSource = "library" if ai_first else "ai"
    first = ai_factory if ai_first else library_factory
    second = library_factory if ai_first else ai_factory
    first_error: str | None = None
    try:
        value = await _call(first)
        if value is not None:
            return ResolvedContent(value, first_name)
    except Exception as exc:  # adapters decide how to log/display degradation
        first_error = str(exc)
    try:
        value = await _call(second)
        return ResolvedContent(
            value,
            second_name if value is not None else "fallback",
            degraded=first_name == "ai",
            error=first_error,
        )
    except Exception as exc:
        return ResolvedContent(
            None,
            "fallback",
            degraded=first_name == "ai",
            error=first_error or str(exc),
        )
