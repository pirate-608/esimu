"""Regression tests for the esimu Beta Starter backend."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Mapping, Sequence

os.environ.setdefault("ESIMU_STARTER_SESSION_STORE", "memory")

from fastapi.testclient import TestClient
import pytest

from esimu_core import PROTOCOL_VERSION, STATE_VERSION
from esimu_core.ai import AIContentService

from app.ai import StarterAIAdapter
from app import main as main_module
from app.main import app
from app.session import StarterGameSession
from app.store import (
    FileSessionStore,
    SQLiteSessionStore,
    SessionStateVersionError,
    _restore_state,
)


def _receive_type(websocket, expected: str, limit: int = 20) -> dict:
    for _ in range(limit):
        message = websocket.receive_json()
        if message["type"] == expected:
            return message
    raise AssertionError(f"did not receive {expected}")


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
                ({"action": "messenger"}, "messenger_update"),
                ({"action": "item_buy", "item_id": "planner"}, "items_state"),
                ({"action": "item_sell", "item_id": "planner"}, "items_state"),
                ({"action": "exam"}, "semester_summary"),
                ({"action": "next_semester"}, "new_semester"),
                ({"action": "pause"}, "tick"),
                ({"action": "resume"}, "tick"),
            ):
                websocket.send_json(request)
                response = _receive_type(websocket, response_type)
                assert response["type"] == response_type
                assert response["protocol_version"] == PROTOCOL_VERSION


def test_websocket_save_and_exit_is_ordered() -> None:
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as websocket:
            websocket.send_json(
                {"token": "save_exit_test", "protocol_version": PROTOCOL_VERSION}
            )
            _receive_type(websocket, "auth_ok")
            _receive_type(websocket, "init")
            websocket.send_json({"action": "save_and_exit"})
            assert _receive_type(websocket, "save_result")["success"] is True
            assert _receive_type(websocket, "exit_confirmed")["type"] == "exit_confirmed"


def test_save_failure_returns_save_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fail_save(_token, _session):
        raise OSError("disk full")

    with TestClient(app) as client:
        with client.websocket_connect("/ws") as websocket:
            websocket.send_json({"token": "save_failure", "protocol_version": 2})
            _receive_type(websocket, "auth_ok")
            _receive_type(websocket, "init")
            monkeypatch.setattr(main_module._session_store, "set", fail_save)
            websocket.send_json({"action": "save_game"})
            result = _receive_type(websocket, "save_result")
            assert result["success"] is False
            assert "disk full" in result["message"]


def test_protocol_v1_keeps_legacy_messenger_response() -> None:
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as websocket:
            websocket.send_json({"token": "legacy_protocol", "protocol_version": 1})
            _receive_type(websocket, "auth_ok")
            _receive_type(websocket, "init")
            websocket.send_json({"action": "messenger"})
            assert _receive_type(websocket, "messenger_round")["protocol_version"] == 2


def test_messenger_ai_wait_does_not_block_other_actions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def delayed_reply(_session, _pending):
        await asyncio.sleep(0.05)
        return {"content": "later", "reply_options": ["continue"]}

    monkeypatch.setattr(main_module._ai, "messenger_reply", delayed_reply)
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as websocket:
            websocket.send_json({"token": "nonblocking_reply", "protocol_version": 2})
            _receive_type(websocket, "auth_ok")
            _receive_type(websocket, "init")
            websocket.send_json({"action": "messenger"})
            opening = _receive_type(websocket, "messenger_update")
            contact = opening["data"]["contact"]
            option = opening["data"]["reply_options"][0]
            websocket.send_json(
                {
                    "action": "messenger_reply",
                    "contact_id": contact["contact_id"],
                    "option_id": option["option_id"],
                }
            )
            immediate = _receive_type(websocket, "messenger_update")
            assert immediate["phase"] == "player"
            websocket.send_json({"action": "get_state"})
            assert _receive_type(websocket, "tick")["type"] == "tick"
            assert _receive_type(websocket, "messenger_update")["phase"] == "npc"


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


def test_v1_state_migrates_runtime_fields() -> None:
    state = StarterGameSession(username="Legacy")
    state.initialize(username="Legacy")
    raw = state.export_state()
    raw["state_version"] = 1
    for key in (
        "tick_count",
        "cooldown_timestamps",
        "action_counts",
        "achievements",
        "completed_terms",
        "last_exam",
        "content_mode",
        "ending_kind",
        "ending_reason",
    ):
        raw.pop(key, None)
    restored = _restore_state(json.dumps(raw))
    assert restored.state_version == STATE_VERSION
    assert restored.content_mode == "library"
    assert restored.action_counts == {}


def test_cooldown_achievement_and_game_over_are_session_state() -> None:
    session = StarterGameSession()
    session.initialize()
    session.relax("walk")
    assert session.relax_cooldowns()["walk"] > 0
    with pytest.raises(ValueError, match="cooling down"):
        session.relax("walk")
    unlocked = session.check_achievements()
    assert [item["code"] for item in unlocked] == ["first_step"]
    session.stats["sanity"] = 0
    game_over = session.check_game_over()
    assert game_over and session.ending_kind == "game_over"
    assert session.is_running is False


def test_content_mode_is_scoped_to_one_session() -> None:
    first = StarterGameSession()
    second = StarterGameSession()
    first.set_content_mode("hybrid", ai_available=True)
    assert first.content_mode == "hybrid"
    assert second.content_mode == "library"


def test_messenger_reply_is_two_phase_and_settles_every_third_reply() -> None:
    session = StarterGameSession()
    session.initialize()
    opening = session.messenger_round()
    contact_id = opening["contact"]["contact_id"]

    for count in range(1, 4):
        pending = session.begin_messenger_reply(contact_id, content=f"reply {count}")
        contact = session.messenger_state["contacts"][contact_id]
        assert contact["messages"][-1]["speaker"] == "player"
        assert contact["awaiting_reply"] is True
        completed = session.complete_messenger_reply(
            contact_id,
            {
                "content": f"npc {count}",
                "reply_options": ["continue"],
                "settlement": {"desc": "round done", "effects": {"sanity": 1}},
            },
        )
        assert pending["reply_count"] == count
        assert completed["state"]["contacts"][contact_id]["awaiting_reply"] is False

    contact = session.messenger_state["contacts"][contact_id]
    assert contact["round_open"] is False
    assert contact["completed_rounds"] == 1
    assert session.action_counts["messenger_round"] == 1


def test_restored_session_recovers_canceled_messenger_reply() -> None:
    session = StarterGameSession()
    session.initialize()
    opening = session.messenger_round()
    contact_id = opening["contact"]["contact_id"]
    session.begin_messenger_reply(contact_id, content="hello")

    restored = StarterGameSession.from_state(session.export_state())
    contact = restored.messenger_state["contacts"][contact_id]
    assert contact["awaiting_reply"] is False
    assert contact["round_reply_count"] == 0
    assert contact["pending_options"]


def test_messenger_settlement_does_not_cross_exam_boundary() -> None:
    session = StarterGameSession()
    session.initialize()
    opening = session.messenger_round()
    contact_id = opening["contact"]["contact_id"]
    contact = session.messenger_state["contacts"][contact_id]
    contact["round_reply_count"] = 2
    pending = session.begin_messenger_reply(contact_id, content="third reply")
    session.final_exam()
    sanity_after_exam = session.stats["sanity"]

    result = session.complete_messenger_reply(
        contact_id,
        {
            "content": "late reply",
            "settlement": {"desc": "late", "effects": {"sanity": 10}},
        },
        expected_semester_idx=pending["semester_idx"],
    )
    assert session.stats["sanity"] == sanity_after_exam
    assert result["feedback"]["changes"] == []


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


def test_ai_adapter_default_theme_follows_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ESIMU_THEME", "external-theme")
    monkeypatch.setenv("ESIMU_CONTENT_MODE", "library")
    adapter = StarterAIAdapter.from_env()
    assert adapter.theme_id == "external-theme"


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
        session.content_mode = "ai"

        event = await adapter.event(session)
        forum = await adapter.forum_post(session)
        message = await adapter.messenger_round(session)
        summary = await adapter.graduation_summary(session)

        assert event["title"] == "Generated event"
        assert forum["content"] == "Generated forum post"
        assert message["content"] == "Generated hello"
        assert summary == "Generated graduation summary."

    asyncio.run(run())
