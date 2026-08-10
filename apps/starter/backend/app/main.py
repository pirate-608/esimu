"""FastAPI entry point for the minimal esimu starter backend."""

from __future__ import annotations

from contextlib import asynccontextmanager
import os
from typing import Any, AsyncIterator
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.bootstrap import configure_project_environment

configure_project_environment()

from app.ai import StarterAIAdapter  # noqa: E402
from app.session import StarterGameSession  # noqa: E402
from app.store import build_session_store  # noqa: E402

_session_store = build_session_store()
_ai = StarterAIAdapter.from_env()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Close optional model clients when the starter process stops."""
    yield
    await _ai.close()


app = FastAPI(title="esimu Starter Backend", lifespan=lifespan)


def _cors_origins() -> list[str]:
    """Return explicit browser origins allowed to call the starter API."""
    configured = os.environ.get(
        "ESIMU_CORS_ORIGINS",
        "http://127.0.0.1:15175,http://localhost:15175",
    )
    return [origin.strip() for origin in configured.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AuthRequest(BaseModel):
    """Minimal placeholder auth request for starter projects."""

    username: str = "Starter Player"


class InitCharacterRequest(BaseModel):
    """Minimal character initialization request."""

    token: str | None = None
    username: str = "Starter Player"
    major: str | None = None
    stats: dict[str, int] = Field(default_factory=dict)


def _session_for_token(token: str | None) -> StarterGameSession:
    if token:
        session = _session_store.get(token)
        if session is not None:
            return session
    session = StarterGameSession()
    if token:
        _session_store.set(token, session)
    return session


def _save_session(token: str, session: StarterGameSession) -> None:
    """Persist a starter session when a token is available."""
    if token:
        _session_store.set(token, session)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Expose a dependency-light readiness endpoint for local and CI smoke."""
    return {"status": "ok"}


@app.get("/config")
def config() -> dict[str, Any]:
    """Return theme/story/stat metadata for a starter frontend."""
    return StarterGameSession().config_payload()


@app.post("/api/auth")
def auth(payload: AuthRequest) -> dict[str, str]:
    """Create a placeholder in-memory session token."""
    token = f"starter_{uuid4().hex[:12]}"
    _session_store.set(token, StarterGameSession(username=payload.username))
    return {"status": "new", "token": token}


@app.get("/api/majors")
def majors() -> list[dict[str, Any]]:
    """Return active-theme majors."""
    return StarterGameSession().majors_payload()


@app.post("/api/init_character")
def init_character(payload: InitCharacterRequest) -> dict[str, Any]:
    """Initialize a starter character in memory."""
    session = _session_for_token(payload.token)
    summary = session.initialize(
        major=payload.major,
        stats=payload.stats or None,
        username=payload.username,
    )
    _save_session(payload.token or "", session)
    return {"status": "ok", **summary, "init": session.init_payload()}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Handle a tiny WebSocket protocol compatible with starter smoke tests."""
    await websocket.accept()
    token = ""
    session = StarterGameSession()
    try:
        first = await websocket.receive_json()
        token = str(first.get("token") or f"starter_{uuid4().hex[:12]}")
        session = _session_for_token(token)
        session.initialize(username=str(first.get("username") or session.username))
        _save_session(token, session)
        await websocket.send_json({"type": "auth_ok", "token": token})
        await websocket.send_json({"type": "init", **session.init_payload()})

        while True:
            message = await websocket.receive_json()
            action = str(message.get("action") or "get_state")
            if action in {"get_state", "start"}:
                await websocket.send_json({"type": "tick", **session.tick_payload()})
            elif action == "relax":
                result = session.relax(str(message.get("target") or "walk"))
                _save_session(token, session)
                await websocket.send_json({"type": "feedback", "data": result})
            elif action == "event":
                result = await _ai.event(session)
                _save_session(token, session)
                await websocket.send_json({"type": "event", "data": result})
            elif action == "event_choice":
                result = session.choose_event(int(message.get("option_index") or 0))
                _save_session(token, session)
                await websocket.send_json({"type": "feedback", "data": result})
            elif action == "forum":
                await websocket.send_json(
                    {"type": "forum_post", "data": await _ai.forum_post(session)}
                )
            elif action == "messenger":
                await websocket.send_json(
                    {
                        "type": "messenger_round",
                        "data": await _ai.messenger_round(session),
                    }
                )
            elif action == "item_buy":
                result = session.buy_item(message.get("item_id"))
                _save_session(token, session)
                await websocket.send_json({"type": "items_state", "data": result})
            elif action == "item_sell":
                result = session.sell_item(message.get("item_id"))
                _save_session(token, session)
                await websocket.send_json({"type": "items_state", "data": result})
            elif action == "exam":
                result = session.final_exam()
                _save_session(token, session)
                await websocket.send_json({"type": "semester_summary", "data": result})
            elif action == "ending":
                summary = await _ai.graduation_summary(session)
                await websocket.send_json(
                    {
                        "type": "ending",
                        "data": {
                            "ended": session.ended,
                            "stats": session.tick_payload()["stats"],
                            "summary": summary,
                        },
                    }
                )
            else:
                await websocket.send_json(
                    {"type": "toast", "message": f"unknown action: {action}"}
                )
    except WebSocketDisconnect:
        pass
