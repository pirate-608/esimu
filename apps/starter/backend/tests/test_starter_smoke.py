"""Regression tests for the esimu Beta Starter backend."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Mapping, Sequence

os.environ.setdefault("ESIMU_STARTER_SESSION_STORE", "memory")

from fastapi.testclient import TestClient
import pytest

from esimu_core import PROTOCOL_VERSION, STATE_VERSION
from esimu_core.ai import AIContentService

from app.ai import StarterAIAdapter
from app.main import app
from app.session import StarterGameSession
from app.store import (
    FileSessionStore,
    SQLiteSessionStore,
    SessionStateVersionError,
)


def test_starter_session_runs_two_term_game_loop() -> None:
    session = StarterGameSession()
    summary = session.initialize()
    session.advance_tick()
    event = session.event()
    forum_post = session.forum_post()
    messenger = session.messenger_round()
    reply = session.messenger_reply(messenger["contact"]["contact_id"])
    items_state = session.buy_item("planner")
    sold_state = session.sell_item("planner")
    exam = session.final_exam()
    next_term = session.next_semester()

    assert summary["major_abbr"] == "GEN"
    assert session.tick_payload()["protocol_version"] == PROTOCOL_VERSION
    assert event["title"] == "社团摊位前"
    assert "校园笑话" in forum_post["content"]
    assert reply["npc_message"]
    assert "planner" in items_state["owned"]
    assert "planner" not in sold_state["owned"]
    assert exam["cgpa"] >= 0
    assert next_term["ended"] is False
    assert session.stats["semester_idx"] == 2


def test_starter_http_routes_expose_config_and_resume() -> None:
    with TestClient(app) as client:
        health = client.get("/healthz")
        config = client.get("/config")
        majors = client.get("/api/majors")
        auth = client.post("/api/auth", json={"username": "Alex"})
        token = auth.json()["token"]
        init = client.post(
            "/api/init_character",
            json={"token": token, "username": "Alex", "major": "GEN"},
        )
        resumed = client.post(
            "/api/auth", json={"username": "Alex", "token": token}
        )

    assert health.json() == {"status": "ok", "storage": "ready"}
    assert config.json()["protocol_version"] == PROTOCOL_VERSION
    assert config.json()["state_version"] == STATE_VERSION
    assert config.json()["theme"]["themeId"] == "demo-campus"
    assert majors.json()[0]["abbr"] == "GEN"
    assert init.json()["init"]["data"]["major_abbr"] == "GEN"
    assert resumed.json()["status"] == "returning"


def test_starter_http_allows_documented_dev_origin() -> None:
    with TestClient(app) as client:
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


def test_starter_websocket_runs_neutral_actions() -> None:
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as websocket:
            websocket.send_json(
                {
                    "token": "starter_test",
                    "username": "Alex",
                    "protocol_version": PROTOCOL_VERSION,
                }
            )
            assert websocket.receive_json()["type"] == "auth_ok"
            assert websocket.receive_json()["type"] == "init"

            for request, response_type in (
                ({"action": "relax", "target": "walk"}, "feedback"),
                ({"action": "event"}, "event"),
                ({"action": "event_choice", "option_index": 0}, "feedback"),
                ({"action": "forum"}, "forum_post"),
                ({"action": "messenger"}, "messenger_round"),
                ({"action": "item_buy", "item_id": "planner"}, "items_state"),
                ({"action": "item_sell", "item_id": "planner"}, "items_state"),
                ({"action": "exam"}, "semester_summary"),
                ({"action": "next_semester"}, "new_semester"),
                ({"action": "pause"}, "tick"),
                ({"action": "resume"}, "tick"),
            ):
                websocket.send_json(request)
                response = websocket.receive_json()
                assert response["type"] == response_type
                assert response["protocol_version"] == PROTOCOL_VERSION


@pytest.mark.asyncio
async def test_file_session_store_round_trips_legacy_state(tmp_path: Path) -> None:
    store = FileSessionStore(tmp_path)
    session = StarterGameSession(username="Alex")
    session.initialize(username="Alex")
    session.buy_item("planner")

    await store.set("token/with unsafe chars", session)
    restored = await store.get("token/with unsafe chars")

    assert restored is not None
    assert restored.username == "Alex"
    assert "planner" in restored.items_state["owned"]


@pytest.mark.asyncio
async def test_sqlite_store_persists_hashed_tokens_and_restarts(tmp_path: Path) -> None:
    path = tmp_path / "esimu.sqlite3"
    store = SQLiteSessionStore(path)
    session = StarterGameSession(username="Alex")
    session.initialize(username="Alex")
    session.advance_tick()
    await store.set("secret-local-token", session)
    await store.close()

    reopened = SQLiteSessionStore(path)
    restored = await reopened.get("secret-local-token")

    assert restored is not None
    assert restored.stats["elapsed_game_time"] > 0
    database_bytes = path.read_bytes()
    assert b"secret-local-token" not in database_bytes


@pytest.mark.asyncio
async def test_sqlite_rejects_newer_state_version(tmp_path: Path) -> None:
    import aiosqlite

    store = SQLiteSessionStore(tmp_path / "future.sqlite3")
    session = StarterGameSession()
    session.initialize()
    await store.set("token", session)
    async with aiosqlite.connect(store.path) as database:
        await database.execute(
            "UPDATE sessions SET state_json = ?",
            ('{"state_version":999}',),
        )
        await database.commit()

    with pytest.raises(SessionStateVersionError):
        await store.get("token")


class FakeAITransport:
    """Small queue-backed transport for Starter AI integration tests."""

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
        assert forum["content"] == "Generated forum post"
        assert message["content"] == "Generated hello"
        assert summary == "Generated graduation summary."

    asyncio.run(run())
