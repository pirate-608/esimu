"""FastAPI entry point for the esimu Beta Starter backend."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress
import os
from typing import Any, AsyncIterator, Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.bootstrap import configure_project_environment

configure_project_environment()

from esimu_core import PROTOCOL_VERSION  # noqa: E402
from esimu_core.runtime.clock import tick_timing  # noqa: E402

from app.ai import StarterAIAdapter  # noqa: E402
from app.session import StarterGameSession  # noqa: E402
from app.store import SessionStoreError, build_session_store  # noqa: E402

_session_store = build_session_store()
_ai = StarterAIAdapter.from_env()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Initialize persistence and close optional resources on shutdown."""
    await _session_store.initialize()
    yield
    await _ai.close()
    await _session_store.close()


app = FastAPI(title="esimu Starter Backend", version="0.2.0b3", lifespan=lifespan)


def _cors_origins() -> list[str]:
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
    """Local-profile authentication request."""

    username: str = "Starter Player"
    token: str | None = None


class InitCharacterRequest(BaseModel):
    """Character initialization request."""

    token: str | None = None
    username: str = "Starter Player"
    major: str | None = None
    stats: dict[str, int] = Field(default_factory=dict)
    reset: bool = False


async def _session_for_token(token: str | None) -> StarterGameSession:
    if token:
        session = await _session_store.get(token)
        if session is not None:
            return session
    session = StarterGameSession()
    if token:
        await _session_store.set(token, session)
    return session


async def _save_session(token: str, session: StarterGameSession) -> None:
    if token:
        await _session_store.set(token, session)


@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    """Expose process and persistence readiness."""
    ready = await _session_store.health()
    if not ready:
        raise HTTPException(status_code=503, detail="session store unavailable")
    return {"status": "ok", "storage": "ready"}


@app.get("/config")
async def config() -> dict[str, Any]:
    """Return theme/story/stat metadata and protocol versions."""
    return StarterGameSession().config_payload()


@app.post("/api/auth")
async def auth(payload: AuthRequest) -> dict[str, str]:
    """Create or resume one opaque local-profile token."""
    if payload.token:
        existing = await _session_store.get(payload.token)
        if existing is not None:
            return {"status": "returning", "token": payload.token}
    token = f"esimu_{uuid4().hex}"
    await _session_store.set(token, StarterGameSession(username=payload.username))
    return {"status": "new", "token": token}


@app.get("/api/majors")
async def majors() -> list[dict[str, Any]]:
    """Return active-theme majors."""
    return StarterGameSession().majors_payload()


@app.post("/api/init_character")
async def init_character(payload: InitCharacterRequest) -> dict[str, Any]:
    """Initialize or restore a local character."""
    session = await _session_for_token(payload.token)
    if not session.stats or payload.reset:
        summary = session.initialize(
            major=payload.major,
            stats=payload.stats or None,
            username=payload.username,
        )
    else:
        summary = {
            "major": session.stats.get("major"),
            "major_abbr": session.stats.get("major_abbr"),
            "restored": True,
        }
    await _save_session(payload.token or "", session)
    return {"status": "ok", **summary, "init": session.init_payload()}


async def _run_tick_loop(
    *,
    token: str,
    session: StarterGameSession,
    session_lock: asyncio.Lock,
    send: Callable[[dict[str, Any]], Awaitable[None]],
) -> None:
    """Advance and persist one connected session until the socket closes."""
    while True:
        tick_config = session.balance.raw.get("tick") or {}
        timing = tick_timing(
            tick_config.get("interval_seconds", 3),
            session.speed_multiplier,
        )
        await asyncio.sleep(timing.sleep_seconds)
        async with session_lock:
            before = int(session.stats.get("elapsed_game_time", 0) or 0)
            payload = session.advance_tick()
            after = int(session.stats.get("elapsed_game_time", 0) or 0)
            if after != before:
                await _save_session(token, session)
        await send({"type": "tick", **payload})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Run the versioned neutral Starter WebSocket protocol."""
    await websocket.accept()
    token = ""
    session = StarterGameSession()
    session_lock = asyncio.Lock()
    send_lock = asyncio.Lock()
    tick_task: asyncio.Task[None] | None = None

    async def send(message: dict[str, Any]) -> None:
        envelope = {"protocol_version": PROTOCOL_VERSION, **message}
        async with send_lock:
            await websocket.send_json(envelope)

    async def mutate(
        callback: Callable[[], Any],
        *,
        persist: bool = True,
    ) -> Any:
        async with session_lock:
            result = callback()
            if persist:
                await _save_session(token, session)
            return result

    try:
        first = await websocket.receive_json()
        requested_protocol = int(first.get("protocol_version", PROTOCOL_VERSION))
        if requested_protocol > PROTOCOL_VERSION:
            await send(
                {
                    "type": "error",
                    "message": "client protocol is newer than this server",
                }
            )
            await websocket.close(code=1002)
            return

        token = str(first.get("token") or f"esimu_{uuid4().hex}")
        session = await _session_for_token(token)
        restored = bool(session.stats)
        if not restored:
            session.initialize(username=str(first.get("username") or session.username))
            await _save_session(token, session)

        await send({"type": "auth_ok", "token": token, "restored": restored})
        await send({"type": "init", **session.init_payload()})
        tick_task = asyncio.create_task(
            _run_tick_loop(
                token=token,
                session=session,
                session_lock=session_lock,
                send=send,
            )
        )

        while True:
            message = await websocket.receive_json()
            action = str(message.get("action") or "get_state")
            try:
                if action in {"get_state", "start"}:
                    await send({"type": "tick", **session.tick_payload()})
                elif action == "pause":
                    await send({"type": "tick", **await mutate(session.pause)})
                elif action == "resume":
                    await send({"type": "tick", **await mutate(session.resume)})
                elif action == "set_speed":
                    result = await mutate(
                        lambda: session.set_speed(message.get("speed", 1))
                    )
                    await send({"type": "tick", **result})
                elif action == "restart":
                    result = await mutate(session.restart)
                    await send({"type": "init", **result})
                elif action == "change_course_state":
                    result = await mutate(
                        lambda: session.change_course_state(
                            str(message.get("course_id") or ""),
                            message.get("state", 1),
                        )
                    )
                    await send({"type": "tick", **result})
                elif action == "relax":
                    if not session.is_running:
                        raise ValueError("resume the game before using an action")
                    result = await mutate(
                        lambda: session.relax(str(message.get("target") or "walk"))
                    )
                    await send({"type": "feedback", "data": result})
                elif action == "event":
                    if not session.is_running:
                        raise ValueError("resume the game before requesting an event")
                    result = await _ai.event(session)
                    await _save_session(token, session)
                    await send({"type": "event", "data": result})
                elif action == "event_choice":
                    result = await mutate(
                        lambda: session.choose_event(
                            int(message.get("option_index") or 0)
                        )
                    )
                    await send({"type": "feedback", "data": result})
                elif action == "forum":
                    await send(
                        {
                            "type": "forum_post",
                            "data": await _ai.forum_post(session),
                        }
                    )
                elif action == "messenger":
                    result = await _ai.messenger_round(session)
                    await _save_session(token, session)
                    await send({"type": "messenger_round", "data": result})
                elif action == "messenger_reply":
                    result = await mutate(
                        lambda: session.messenger_reply(
                            str(message.get("contact_id") or ""),
                            str(message.get("option_id") or "") or None,
                            str(message.get("content") or "") or None,
                        )
                    )
                    await send({"type": "messenger_reply", "data": result})
                elif action == "item_buy":
                    result = await mutate(
                        lambda: session.buy_item(message.get("item_id"))
                    )
                    await send({"type": "items_state", "data": result})
                elif action == "item_sell":
                    result = await mutate(
                        lambda: session.sell_item(message.get("item_id"))
                    )
                    await send({"type": "items_state", "data": result})
                elif action == "exam":
                    result = await mutate(session.final_exam)
                    await send({"type": "semester_summary", "data": result})
                elif action == "next_semester":
                    result = await mutate(session.next_semester)
                    await send({"type": "new_semester", "data": result})
                elif action == "ending":
                    summary = await _ai.graduation_summary(session)
                    await send(
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
                    await send(
                        {"type": "toast", "level": "warning", "message": f"unknown action: {action}"}
                    )
            except (ValueError, SessionStoreError) as exc:
                await send(
                    {"type": "toast", "level": "error", "message": str(exc)}
                )
    except WebSocketDisconnect:
        pass
    finally:
        if tick_task is not None:
            tick_task.cancel()
            with suppress(asyncio.CancelledError):
                await tick_task
