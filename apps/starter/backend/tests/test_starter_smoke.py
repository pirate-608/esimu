"""Smoke tests for the minimal esimu starter backend."""

import asyncio
from pathlib import Path
from typing import Mapping, Sequence

from fastapi.testclient import TestClient

from esimu_core.ai import AIContentService

from app.ai import StarterAIAdapter
from app.main import app
from app.session import StarterGameSession
from app.store import FileSessionStore


def test_starter_session_runs_minimal_game_loop() -> None:
    session = StarterGameSession()

    summary = session.initialize()
    tick = session.tick_payload()
    event = session.event()
    forum_post = session.forum_post()
    messenger = session.messenger_round()
    items_state = session.buy_item("planner")
    sold_state = session.sell_item("planner")
    exam = session.final_exam()

    assert summary["major_abbr"] == "GEN"
    assert tick["stats"]["major_abbr"] == "GEN"
    assert event["title"] == "社团摊位前"
    assert "校园笑话" in forum_post["content"]
    assert messenger["contact"]["role"] in {"roommate", "teacher", "classmate"}
    assert "planner" in items_state["owned"]
    assert "planner" not in sold_state["owned"]
    assert exam["cgpa"] >= 0


def test_starter_http_routes_expose_config_and_init() -> None:
    client = TestClient(app)

    health = client.get("/healthz")
    config = client.get("/config")
    majors = client.get("/api/majors")
    auth = client.post("/api/auth", json={"username": "Alex"})
    token = auth.json()["token"]
    init = client.post(
        "/api/init_character",
        json={"token": token, "username": "Alex", "major": "GEN"},
    )

    assert health.json() == {"status": "ok"}
    assert config.status_code == 200
    assert config.json()["theme"]["themeId"] == "demo-campus"
    assert majors.json()[0]["abbr"] == "GEN"
    assert auth.json()["status"] == "new"
    assert init.json()["status"] == "ok"
    assert init.json()["init"]["data"]["major_abbr"] == "GEN"


def test_starter_http_allows_documented_dev_origin() -> None:
    client = TestClient(app)

    response = client.options(
        "/api/auth",
        headers={
            "Origin": "http://127.0.0.1:15175",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "http://127.0.0.1:15175"
    )


def test_starter_websocket_sends_init_and_actions() -> None:
    client = TestClient(app)

    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({"token": "starter_test", "username": "Alex"})
        assert websocket.receive_json()["type"] == "auth_ok"
        init = websocket.receive_json()
        assert init["type"] == "init"
        assert init["data"]["major_abbr"] == "GEN"

        websocket.send_json({"action": "relax", "target": "walk"})
        relax = websocket.receive_json()
        assert relax["type"] == "feedback"
        assert "changes" in relax["data"]

        websocket.send_json({"action": "event"})
        event = websocket.receive_json()
        assert event["type"] == "event"
        assert event["data"]["options"]

        websocket.send_json({"action": "event_choice", "option_index": 0})
        event_feedback = websocket.receive_json()
        assert event_feedback["type"] == "feedback"

        websocket.send_json({"action": "forum"})
        forum = websocket.receive_json()
        assert forum["type"] == "forum_post"
        assert "content" in forum["data"]

        websocket.send_json({"action": "messenger"})
        message = websocket.receive_json()
        assert message["type"] == "messenger_round"
        assert message["data"]["reply_options"]

        websocket.send_json({"action": "item_buy", "item_id": "planner"})
        bought = websocket.receive_json()
        assert bought["type"] == "items_state"
        assert "planner" in bought["data"]["owned"]

        websocket.send_json({"action": "item_sell", "item_id": "planner"})
        sold = websocket.receive_json()
        assert sold["type"] == "items_state"
        assert "planner" not in sold["data"]["owned"]

        websocket.send_json({"action": "exam"})
        exam = websocket.receive_json()
        assert exam["type"] == "semester_summary"
        assert "cgpa" in exam["data"]

        websocket.send_json({"action": "ending"})
        ending = websocket.receive_json()
        assert ending["type"] == "ending"
        assert ending["data"]["ended"] is True
        assert ending["data"]["summary"]


def test_file_session_store_round_trips_session(tmp_path: Path) -> None:
    store = FileSessionStore(tmp_path)
    session = StarterGameSession(username="Alex")
    session.initialize(username="Alex")
    session.buy_item("planner")

    store.set("token/with unsafe chars", session)
    restored = store.get("token/with unsafe chars")

    assert restored is not None
    assert restored.username == "Alex"
    assert "planner" in restored.items_state["owned"]


class FakeAITransport:
    """Small queue-backed transport for starter AI integration tests."""

    def __init__(self, *responses: str) -> None:
        self.responses = list(responses)

    async def complete(
        self,
        messages: Sequence[Mapping[str, str]],
        *,
        max_tokens: int = 500,
        temperature: float | None = None,
        top_p: float | None = None,
    ) -> str | None:
        del messages, max_tokens, temperature, top_p
        return self.responses.pop(0) if self.responses else None

    async def probe(self) -> bool:
        return True

    async def close(self) -> None:
        return None


def test_starter_ai_adapter_drives_generated_content() -> None:
    async def run() -> None:
        transport = FakeAITransport(
            '{"events":[{"title":"Generated event","desc":"A surprise",'
            '"options":[{"text":"Join","effects":{"sanity":2}},'
            '{"text":"Leave","effects":{"stress":-1}}]}]}',
            '{"posts":["Generated forum post"]}',
            '{"content":"Generated hello","reply_options":["Reply one","Reply two"]}',
            "Generated graduation summary.",
        )
        service = AIContentService.for_theme(transport, "demo-campus")
        adapter = StarterAIAdapter(service=service, mode="ai")
        session = StarterGameSession()
        session.initialize(username="Alex")

        event = await adapter.event(session)
        forum = await adapter.forum_post(session)
        message = await adapter.messenger_round(session)
        summary = await adapter.graduation_summary(session)

        assert event["title"] == "Generated event"
        assert session.last_event == event
        assert forum["content"] == "Generated forum post"
        assert message["content"] == "Generated hello"
        assert message["contact"]["contact_id"] in session.messenger_state["contacts"]
        assert summary == "Generated graduation summary."

    asyncio.run(run())
