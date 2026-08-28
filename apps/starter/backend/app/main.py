"""FastAPI entry point for the esimu Beta Starter backend."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress
import logging
import os
from typing import Any, AsyncIterator, Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.bootstrap import configure_project_environment

configure_project_environment()

from esimu_core import PROTOCOL_VERSION, __version__  # noqa: E402
from esimu_core.runtime.actions import decide_runtime_action  # noqa: E402
from esimu_core.runtime.clock import tick_timing  # noqa: E402
from esimu_core.runtime.tasks import TargetTaskRegistry  # noqa: E402

from app.ai import StarterAIAdapter  # noqa: E402
from app.session import StarterGameSession  # noqa: E402
from app.store import SessionStoreError, build_session_store  # noqa: E402

_session_store = build_session_store()
_ai = StarterAIAdapter.from_env()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Initialize persistence and close optional resources on shutdown."""
    await _session_store.initialize()
    yield
    await _ai.close()
    await _session_store.close()


app = FastAPI(title="esimu Starter Backend", version=__version__, lifespan=lifespan)


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


def _fresh_session(username: str = "Starter Player") -> StarterGameSession:
    return StarterGameSession(username=username, content_mode=_ai.mode)


async def _session_for_token(token: str | None) -> StarterGameSession:
    if token:
        session = await _session_store.get(token)
        if session is not None:
            return session
    session = _fresh_session()
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
    payload = _fresh_session().config_payload()
    payload["llm_available"] = _ai.enabled
    payload["default_content_mode"] = _ai.mode
    return payload


@app.post("/api/auth")
async def auth(payload: AuthRequest) -> dict[str, str]:
    """Create or resume one opaque local-profile token."""
    if payload.token:
        existing = await _session_store.get(payload.token)
        if existing is not None:
            return {"status": "returning", "token": payload.token}
    token = f"esimu_{uuid4().hex}"
    await _session_store.set(token, _fresh_session(payload.username))
    return {"status": "new", "token": token}


@app.get("/api/majors")
async def majors() -> list[dict[str, Any]]:
    """Return active-theme majors."""
    return _fresh_session().majors_payload()


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
    emit_outcomes: Callable[
        [list[dict[str, str]], dict[str, Any] | None], Awaitable[None]
    ],
    on_scheduled_content: Callable[[Any], Awaitable[None]],
) -> None:
    """Advance and persist one connected session until the socket closes."""
    while True:
        tick_config = session.balance.raw.get("tick") or {}
        timing = tick_timing(
            tick_config.get("interval_seconds", 3),
            session.speed_multiplier,
        )
        await asyncio.sleep(timing.sleep_seconds)
        summary: dict[str, Any] | None = None
        achievements: list[dict[str, str]] = []
        game_over: dict[str, Any] | None = None
        async with session_lock:
            before = int(session.stats.get("elapsed_game_time", 0) or 0)
            payload = session.advance_tick()
            after = int(session.stats.get("elapsed_game_time", 0) or 0)
            if after != before:
                if (
                    not session.is_running
                    and not session.exam_completed
                    and not session.ended
                    and after >= session.snapshot().semester_duration
                ):
                    summary = session.final_exam()
                    achievements.extend(summary.get("achievements") or [])
                achievements.extend(session.check_achievements())
                game_over = session.check_game_over()
                await _save_session(token, session)
            decision = session.automatic_content_decision()
        await send({"type": "tick", **payload})
        if summary is not None:
            await send({"type": "semester_summary", "data": summary, "automatic": True})
        await emit_outcomes(achievements, game_over)
        await on_scheduled_content(decision)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Run the versioned neutral Starter WebSocket protocol."""
    await websocket.accept()
    token = ""
    session = _fresh_session()
    session_lock = asyncio.Lock()
    send_lock = asyncio.Lock()
    tick_task: asyncio.Task[None] | None = None
    background = TargetTaskRegistry()
    requested_protocol = PROTOCOL_VERSION

    async def send(message: dict[str, Any]) -> None:
        envelope = {"protocol_version": PROTOCOL_VERSION, **message}
        async with send_lock:
            await websocket.send_json(envelope)

    async def mutate(
        callback: Callable[[], Any],
        *,
        persist: bool = True,
        evaluate: bool = True,
    ) -> tuple[Any, list[dict[str, str]], dict[str, Any] | None]:
        async with session_lock:
            result = callback()
            achievements = session.check_achievements() if evaluate else []
            game_over = session.check_game_over() if evaluate else None
            if persist:
                await _save_session(token, session)
            return result, achievements, game_over

    async def persist_with_result(message: str) -> bool:
        """Persist a checkpoint and always return a protocol-level result."""
        try:
            async with session_lock:
                await _save_session(token, session)
        except Exception as exc:
            logger.error("Starter save failed: %s", exc)
            await send(
                {
                    "type": "save_result",
                    "success": False,
                    "message": f"save failed: {exc}",
                }
            )
            return False
        await send({"type": "save_result", "success": True, "message": message})
        return True

    async def emit_outcomes(
        achievements: list[dict[str, str]],
        game_over: dict[str, Any] | None,
    ) -> None:
        for achievement in achievements:
            await send({"type": "achievement_unlocked", "data": achievement})
        if game_over is not None:
            if requested_protocol >= 2:
                await send({"type": "game_over", "data": game_over})
            else:
                await send(
                    {
                        "type": "ending",
                        "data": {"outcome": "game_over", **game_over},
                    }
                )

    async def send_messenger_update(
        data: dict[str, Any],
        *,
        legacy_type: str,
        phase: str,
    ) -> None:
        if requested_protocol >= 2:
            await send({"type": "messenger_update", "phase": phase, "data": data})
        else:
            await send({"type": legacy_type, "data": data})

    def track(coro: Any, *, target: str) -> bool:
        task = background.track(
            coro,
            target=target,
            on_error=lambda exc: logger.error(
                "Starter background task %s failed: %s", target, exc
            ),
        )
        return task is not None

    async def run_event_generation() -> None:
        try:
            generated = await _ai.event(session)
            async with session_lock:
                if session.last_event is not None or not session.is_running:
                    return
                result = session.accept_event(generated)
                achievements = session.check_achievements()
                game_over = session.check_game_over()
                await _save_session(token, session)
            await send({"type": "event", "data": result})
            await emit_outcomes(achievements, game_over)
        except Exception as exc:
            await send({"type": "toast", "level": "error", "message": str(exc)})

    async def run_forum_generation() -> None:
        try:
            result = await _ai.forum_post(session)
            async with session_lock:
                session.record_action("forum")
                achievements = session.check_achievements()
                await _save_session(token, session)
            await send({"type": "forum_post", "data": result})
            await emit_outcomes(achievements, None)
        except Exception as exc:
            await send({"type": "toast", "level": "error", "message": str(exc)})

    async def run_messenger_opening() -> None:
        try:
            async with session_lock:
                character = session.next_messenger_character()
            if character is None:
                raise ValueError("no closed messenger contact is currently available")
            generated = await _ai.messenger_round(session, character)
            async with session_lock:
                if not session.is_running:
                    return
                result = session.accept_messenger_round(generated)
                achievements = session.check_achievements()
                await _save_session(token, session)
            await send_messenger_update(
                result,
                legacy_type="messenger_round",
                phase="opening",
            )
            await emit_outcomes(achievements, None)
        except Exception as exc:
            await send({"type": "toast", "level": "error", "message": str(exc)})

    async def run_messenger_reply(pending: dict[str, Any]) -> None:
        contact_id = str(pending["contact_id"])
        try:
            generated = await _ai.messenger_reply(session, pending)
        except Exception:
            generated = {
                "content": "收到，我明白你的意思了。",
                "reply_options": ["继续聊聊", "稍后再说"],
            }
        async with session_lock:
            result = session.complete_messenger_reply(
                contact_id,
                generated,
                expected_semester_idx=int(pending["semester_idx"]),
            )
            achievements = session.check_achievements()
            game_over = session.check_game_over()
            await _save_session(token, session)
        await send_messenger_update(
            result,
            legacy_type="messenger_reply",
            phase="npc",
        )
        if result.get("feedback"):
            await send({"type": "feedback", "data": result["feedback"]})
        else:
            await send({"type": "tick", **session.tick_payload()})
        await emit_outcomes(achievements, game_over)

    async def schedule_automatic_content(decision: Any) -> None:
        if decision.event_due:
            track(run_event_generation(), target="event")
        if decision.messenger_due:
            track(run_messenger_opening(), target="messenger-opening")

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
                emit_outcomes=emit_outcomes,
                on_scheduled_content=schedule_automatic_content,
            )
        )

        should_close = False
        while True:
            message = await websocket.receive_json()
            action = str(message.get("action") or "get_state")
            try:
                decision = decide_runtime_action(
                    action,
                    is_running=session.is_running,
                    exam_completed=session.exam_completed,
                )
                if not decision.allowed:
                    await send(
                        {
                            "type": "toast",
                            "level": "warning",
                            "message": "resume gameplay before using this action",
                        }
                    )
                    continue
                if action == "ping":
                    await send({"type": "pong"})
                elif action == "save_game":
                    await persist_with_result("game saved")
                elif action == "save_and_exit":
                    if await persist_with_result("game saved"):
                        await send({"type": "exit_confirmed"})
                        await websocket.close(code=1000, reason="save_and_exit")
                        should_close = True
                elif action == "exit_without_save":
                    await send({"type": "exit_confirmed"})
                    await websocket.close(code=1000, reason="exit_without_save")
                    should_close = True
                elif action in {"get_state", "start"}:
                    await send({"type": "tick", **session.tick_payload()})
                elif action == "pause":
                    result, achievements, game_over = await mutate(session.pause)
                    await send({"type": "tick", **result})
                    await emit_outcomes(achievements, game_over)
                elif action == "resume":
                    result, achievements, game_over = await mutate(session.resume)
                    await send({"type": "tick", **result})
                    await emit_outcomes(achievements, game_over)
                elif action == "set_speed":
                    result, achievements, game_over = await mutate(
                        lambda: session.set_speed(message.get("speed", 1))
                    )
                    await send({"type": "tick", **result})
                    await emit_outcomes(achievements, game_over)
                elif action == "set_mode":
                    result, _achievements, _game_over = await mutate(
                        lambda: session.set_content_mode(
                            message.get("mode"), ai_available=_ai.enabled
                        ),
                        evaluate=False,
                    )
                    await send(
                        {
                            "type": "mode_changed",
                            "mode": result,
                            "llm_available": _ai.enabled,
                        }
                    )
                elif action == "restart":
                    await background.cancel_and_wait()
                    result, achievements, game_over = await mutate(session.restart)
                    await send({"type": "init", **result})
                    await emit_outcomes(achievements, game_over)
                elif action == "change_course_state":
                    result, achievements, game_over = await mutate(
                        lambda: session.change_course_state(
                            str(message.get("course_id") or ""),
                            message.get("state", 1),
                        )
                    )
                    await send({"type": "tick", **result})
                    await emit_outcomes(achievements, game_over)
                elif action == "relax":
                    result, achievements, game_over = await mutate(
                        lambda: session.relax(str(message.get("target") or "walk"))
                    )
                    await send({"type": "feedback", "data": result})
                    await emit_outcomes(achievements, game_over)
                elif action == "event":
                    if not track(run_event_generation(), target="event"):
                        raise ValueError("an event is already being prepared")
                elif action == "event_choice":
                    result, achievements, game_over = await mutate(
                        lambda: session.choose_event(
                            int(message.get("option_index") or 0)
                        )
                    )
                    await send({"type": "feedback", "data": result})
                    await emit_outcomes(achievements, game_over)
                elif action == "forum":
                    if not track(run_forum_generation(), target="forum"):
                        raise ValueError("a forum post is already being prepared")
                elif action == "messenger":
                    if not track(
                        run_messenger_opening(), target="messenger-opening"
                    ):
                        raise ValueError("a messenger opening is already being prepared")
                elif action == "messenger_mark_read":
                    result, _achievements, _game_over = await mutate(
                        lambda: session.mark_messenger_read(
                            str(message.get("contact_id") or "")
                        ),
                        evaluate=False,
                    )
                    await send_messenger_update(
                        {"state": result},
                        legacy_type="messenger_reply",
                        phase="read",
                    )
                elif action == "messenger_reply":
                    pending, achievements, game_over = await mutate(
                        lambda: session.begin_messenger_reply(
                            str(message.get("contact_id") or ""),
                            str(message.get("option_id") or "") or None,
                            str(message.get("content") or "") or None,
                        )
                    )
                    await send_messenger_update(
                        pending,
                        legacy_type="messenger_reply",
                        phase="player",
                    )
                    await emit_outcomes(achievements, game_over)
                    if not track(
                        run_messenger_reply(pending),
                        target=f"messenger:{pending['contact_id']}",
                    ):
                        raise ValueError("this contact is already preparing a reply")
                elif action == "item_buy":
                    result, achievements, game_over = await mutate(
                        lambda: session.buy_item(message.get("item_id"))
                    )
                    await send({"type": "items_state", "data": result})
                    await send({"type": "tick", **session.tick_payload()})
                    await emit_outcomes(achievements, game_over)
                elif action == "item_sell":
                    result, achievements, game_over = await mutate(
                        lambda: session.sell_item(message.get("item_id"))
                    )
                    await send({"type": "items_state", "data": result})
                    await send({"type": "tick", **session.tick_payload()})
                    await emit_outcomes(achievements, game_over)
                elif action == "exam":
                    result, achievements, game_over = await mutate(session.final_exam)
                    await send({"type": "semester_summary", "data": result})
                    await emit_outcomes(
                        [*(result.get("achievements") or []), *achievements],
                        game_over,
                    )
                elif action == "next_semester":
                    result, achievements, game_over = await mutate(session.next_semester)
                    await send({"type": "new_semester", "data": result})
                    await emit_outcomes(achievements, game_over)
                elif action == "ending":
                    summary = await _ai.graduation_summary(session)
                    await send(
                        {
                            "type": "ending",
                            "data": {
                                "ended": session.ended,
                                "outcome": session.ending_kind or "graduation",
                                "reason": session.ending_reason,
                                "stats": session.tick_payload()["stats"],
                                "summary": summary,
                                "achievements": session.achievement_detail_payloads(),
                            },
                        }
                    )
                else:
                    await send(
                        {"type": "toast", "level": "warning", "message": f"unknown action: {action}"}
                    )
                if should_close:
                    break
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
        await background.cancel_and_wait()
        async with session_lock:
            if token and session.recover_pending_messenger_replies():
                try:
                    await _save_session(token, session)
                except Exception as exc:
                    logger.error("Failed to recover canceled messenger replies: %s", exc)
