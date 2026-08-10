"""AI transport, generation, and degradation contract tests."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Mapping, Sequence

import pytest

from esimu_core.ai import (
    AIContentService,
    AIModelConfig,
    OpenAICompatibleTransport,
    OpenAITransportRegistry,
    resolve_content,
)
from esimu_core.ai.config import roleplay_model_config_from_env
from esimu_core.ai.parsing import json_object_from_text


class FakeTransport:
    """Queue-backed transport that records model-facing messages."""

    def __init__(self, *responses: str | None) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []
        self.closed = False

    async def complete(
        self,
        messages: Sequence[Mapping[str, str]],
        *,
        max_tokens: int = 500,
        temperature: float | None = None,
        top_p: float | None = None,
    ) -> str | None:
        self.calls.append(
            {
                "messages": list(messages),
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
            }
        )
        return self.responses.pop(0) if self.responses else None

    async def probe(self) -> bool:
        return True

    async def close(self) -> None:
        self.closed = True


class FakeCompletions:
    def __init__(self) -> None:
        self.kwargs: dict[str, Any] = {}

    async def create(self, **kwargs: Any) -> Any:
        self.kwargs = kwargs
        message = SimpleNamespace(content=" response ")
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.chat = SimpleNamespace(completions=FakeCompletions())
        self.models = SimpleNamespace(list=self.list_models)
        self.closed = False

    async def list_models(self) -> list[Any]:
        return []

    async def close(self) -> None:
        self.closed = True


def test_model_config_normalizes_provider_and_m2her_endpoint() -> None:
    generic = AIModelConfig(provider="ollama", model="qwen3")
    roleplay = roleplay_model_config_from_env(
        {
            "ESIMU_RP_API_KEY": "secret",
            "ESIMU_RP_BASE_URL": "https://api.minimaxi.com/v1/chat/completions",
        }
    )

    assert generic.base_url == "http://127.0.0.1:11434/v1"
    assert generic.is_configured is True
    assert roleplay.model == "M2-her"
    assert roleplay.base_url == "https://api.minimaxi.com/v1"
    assert roleplay.role_profile == "minimax_m2her"


def test_json_parser_accepts_fenced_output() -> None:
    assert json_object_from_text('```json\n{"events": []}\n```') == {"events": []}


@pytest.mark.asyncio
async def test_openai_transport_uses_role_profile_token_parameter() -> None:
    generic_client = FakeOpenAIClient()
    generic = OpenAICompatibleTransport(
        AIModelConfig(api_key="x", model="generic"), client=generic_client
    )
    rp_client = FakeOpenAIClient()
    roleplay = OpenAICompatibleTransport(
        AIModelConfig(
            provider="minimax",
            api_key="x",
            model="M2-her",
            role_profile="minimax_m2her",
        ),
        client=rp_client,
    )

    assert await generic.complete([{"role": "user", "content": "hello"}]) == "response"
    assert (
        await roleplay.complete([{"role": "user_system", "content": "hello"}])
        == "response"
    )
    assert "max_tokens" in generic_client.chat.completions.kwargs
    assert "max_completion_tokens" in rp_client.chat.completions.kwargs
    assert rp_client.chat.completions.kwargs["messages"][0]["role"] == "user_system"


def test_transport_registry_separates_shared_and_session_clients(monkeypatch) -> None:
    created: list[AIModelConfig] = []

    class StubTransport:
        def __init__(self, config: AIModelConfig) -> None:
            created.append(config)

    monkeypatch.setattr(
        "esimu_core.ai.transport.OpenAICompatibleTransport",
        StubTransport,
    )
    registry = OpenAITransportRegistry()
    config = AIModelConfig(api_key="platform", model="model")

    assert registry.shared(config) is registry.shared(config)
    assert registry.session(config) is not registry.session(config)
    assert len(created) == 3


@pytest.mark.asyncio
async def test_content_policy_degrades_ai_to_library() -> None:
    async def broken_ai() -> None:
        raise TimeoutError("model timeout")

    result = await resolve_content(
        "ai",
        ai_factory=broken_ai,
        library_factory=lambda: {"title": "local"},
    )

    assert result.value == {"title": "local"}
    assert result.source == "library"
    assert result.degraded is True
    assert result.error == "model timeout"


@pytest.mark.asyncio
async def test_content_policy_hybrid_can_choose_each_source() -> None:
    def ai() -> str:
        return "ai"

    def library() -> str:
        return "library"

    ai_result = await resolve_content(
        "hybrid",
        ai_factory=ai,
        library_factory=library,
        random_value=lambda: 0.0,
    )
    library_result = await resolve_content(
        "hybrid",
        ai_factory=ai,
        library_factory=library,
        random_value=lambda: 1.0,
    )

    assert ai_result.value == "ai"
    assert library_result.value == "library"


@pytest.mark.asyncio
async def test_service_generates_and_sanitizes_theme_content() -> None:
    transport = FakeTransport(
        '{"events":[{"title":"AI event","desc":"desc","options":['
        '{"text":"A","effects":{"energy":999,"unknown":5,"desc":"cost"}},'
        '{"text":"B","effects":{"sanity":3,"desc":"rest"}}]}]}',
        '{"posts":["Generated campus post"]}',
        "A thoughtful graduation summary.",
    )
    service = AIContentService.for_theme(transport, "demo-campus")

    event = await service.generate_random_event({"energy": 80, "sanity": 90})
    forum = await service.generate_forum_post({}, effect="positive", trigger="clubs")
    summary = await service.generate_graduation_summary({"gpa": 4.2})

    assert event is not None
    assert event["title"] == "AI event"
    assert event["options"][0]["effects"]["energy"] == 10
    assert "unknown" not in event["options"][0]["effects"]
    assert forum == {
        "content": "Generated campus post",
        "effect": "positive",
        "trigger": "clubs",
    }
    assert summary == "A thoughtful graduation summary."


@pytest.mark.asyncio
async def test_service_uses_m2her_roles_and_normalizes_message() -> None:
    generic = FakeTransport()
    roleplay = FakeTransport(
        '{"content":"Remember the seminar.","reply_options":["Thanks","Got it"]}'
    )
    service = AIContentService.for_theme(
        generic,
        "demo-campus",
        roleplay_transport=roleplay,
    )

    result = await service.generate_message_opening(
        {
            "name": "Professor Chen",
            "role": "teacher",
            "description": "Patient and direct.",
            "examples": ["Please read chapter two."],
        },
        {
            "username": "Alex",
            "major": "General Studies",
            "semester": "Year 1",
            "charm": 80,
        },
    )

    assert result is not None
    assert result["contact"]["role"] == "teacher"
    assert result["reply_options"][0]["text"] == "Thanks"
    roles = [item["role"] for item in roleplay.calls[0]["messages"]]
    assert {"system", "user_system", "group", "sample_message_ai", "user"} <= set(roles)
    assert roleplay.calls[0]["temperature"] == 1.0


@pytest.mark.asyncio
async def test_service_clamps_third_reply_settlement() -> None:
    transport = FakeTransport(
        '{"npc_reply":"Take a break.","settlement":'
        '{"desc":"You feel better.","effects":{"sanity":99,"hack":100}}}'
    )
    service = AIContentService.for_theme(transport, "demo-campus")

    result = await service.generate_message_reply(
        {"name": "Lin", "role": "roommate", "description": "Kind."},
        {"username": "Alex"},
        [{"speaker": "npc", "content": "You look tired."}],
        "I will rest.",
        reply_count=3,
    )

    assert result is not None
    assert result["settlement"]["effects"] == {"sanity": 10}
