"""Asynchronous persistence adapters for the esimu Starter backend."""

from __future__ import annotations

import asyncio
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Protocol

import aiosqlite

from esimu_core import STATE_VERSION

from app.session import StarterGameSession


class SessionStoreError(RuntimeError):
    """Base error for unreadable or incompatible persisted state."""


class SessionStateVersionError(SessionStoreError):
    """Raised when persisted state is newer than this Starter understands."""


class SessionStore(Protocol):
    """Asynchronous persistence protocol used by the Starter adapter."""

    async def initialize(self) -> None:
        """Prepare storage and apply schema migrations."""

    async def health(self) -> bool:
        """Return whether the backing store is available."""

    async def get(self, token: str) -> StarterGameSession | None:
        """Return an existing session or None."""

    async def set(self, token: str, session: StarterGameSession) -> None:
        """Persist or replace one session."""

    async def pop(self, token: str) -> None:
        """Delete a session if present."""

    async def close(self) -> None:
        """Release backing resources."""


def _restore_state(raw: str) -> StarterGameSession:
    try:
        state = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SessionStoreError("persisted session contains invalid JSON") from exc
    if not isinstance(state, dict):
        raise SessionStoreError("persisted session must be a JSON object")
    version = int(state.get("state_version", 0) or 0)
    if version > STATE_VERSION:
        raise SessionStateVersionError(
            f"session state version {version} is newer than supported {STATE_VERSION}"
        )
    if version == 0:
        state["state_version"] = STATE_VERSION
    return StarterGameSession.from_state(state)


class MemorySessionStore:
    """Process-local asynchronous session store used by tests."""

    def __init__(self) -> None:
        self._sessions: dict[str, StarterGameSession] = {}
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        return None

    async def health(self) -> bool:
        return True

    async def get(self, token: str) -> StarterGameSession | None:
        async with self._lock:
            return self._sessions.get(token)

    async def set(self, token: str, session: StarterGameSession) -> None:
        async with self._lock:
            self._sessions[token] = session

    async def pop(self, token: str) -> None:
        async with self._lock:
            self._sessions.pop(token, None)

    async def close(self) -> None:
        return None


class FileSessionStore:
    """Legacy JSON-file session store retained for the 0.2 beta cycle."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory

    async def initialize(self) -> None:
        await asyncio.to_thread(self.directory.mkdir, parents=True, exist_ok=True)

    async def health(self) -> bool:
        try:
            await self.initialize()
        except OSError:
            return False
        return True

    async def get(self, token: str) -> StarterGameSession | None:
        path = self._path(token)
        if not await asyncio.to_thread(path.exists):
            return None
        raw = await asyncio.to_thread(path.read_text, encoding="utf-8")
        return _restore_state(raw)

    async def set(self, token: str, session: StarterGameSession) -> None:
        await self.initialize()
        path = self._path(token)
        tmp_path = path.with_suffix(".tmp")
        payload = json.dumps(session.export_state(), ensure_ascii=False, indent=2)
        await asyncio.to_thread(tmp_path.write_text, payload, encoding="utf-8")
        await asyncio.to_thread(os.replace, tmp_path, path)

    async def pop(self, token: str) -> None:
        await asyncio.to_thread(self._path(token).unlink, missing_ok=True)

    async def close(self) -> None:
        return None

    def _path(self, token: str) -> Path:
        return self.directory / f"{_token_hash(token)}.json"


class SQLiteSessionStore:
    """Single-node SQLite store with WAL and versioned schema migrations."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._initialized = False
        self._initialize_lock = asyncio.Lock()
        self._write_lock = asyncio.Lock()

    async def initialize(self) -> None:
        if self._initialized:
            return
        async with self._initialize_lock:
            if self._initialized:
                return
            self.path.parent.mkdir(parents=True, exist_ok=True)
            async with aiosqlite.connect(self.path) as database:
                await database.execute("PRAGMA journal_mode=WAL")
                await database.execute("PRAGMA foreign_keys=ON")
                cursor = await database.execute("PRAGMA user_version")
                row = await cursor.fetchone()
                version = int(row[0] if row else 0)
                if version > 1:
                    raise SessionStoreError(
                        f"SQLite schema version {version} is newer than supported 1"
                    )
                if version == 0:
                    await database.execute(
                        """
                        CREATE TABLE IF NOT EXISTS sessions (
                            token_hash TEXT PRIMARY KEY,
                            token_hint TEXT NOT NULL,
                            theme_id TEXT NOT NULL,
                            state_version INTEGER NOT NULL,
                            state_json TEXT NOT NULL,
                            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                        )
                        """
                    )
                    await database.execute("PRAGMA user_version=1")
                await database.commit()
            self._initialized = True

    async def health(self) -> bool:
        try:
            await self.initialize()
            async with aiosqlite.connect(self.path) as database:
                await database.execute("SELECT 1")
            return True
        except (OSError, aiosqlite.Error, SessionStoreError):
            return False

    async def get(self, token: str) -> StarterGameSession | None:
        await self.initialize()
        async with aiosqlite.connect(self.path) as database:
            cursor = await database.execute(
                "SELECT state_json FROM sessions WHERE token_hash = ?",
                (_token_hash(token),),
            )
            row = await cursor.fetchone()
        return _restore_state(str(row[0])) if row else None

    async def set(self, token: str, session: StarterGameSession) -> None:
        await self.initialize()
        payload = json.dumps(
            session.export_state(), ensure_ascii=False, separators=(",", ":")
        )
        async with self._write_lock:
            async with aiosqlite.connect(self.path) as database:
                await database.execute("BEGIN IMMEDIATE")
                await database.execute(
                    """
                    INSERT INTO sessions (
                        token_hash, token_hint, theme_id, state_version, state_json
                    ) VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(token_hash) DO UPDATE SET
                        theme_id=excluded.theme_id,
                        state_version=excluded.state_version,
                        state_json=excluded.state_json,
                        updated_at=CURRENT_TIMESTAMP
                    """,
                    (
                        _token_hash(token),
                        token[-4:] if token else "",
                        session.theme_id,
                        STATE_VERSION,
                        payload,
                    ),
                )
                await database.commit()

    async def pop(self, token: str) -> None:
        await self.initialize()
        async with self._write_lock:
            async with aiosqlite.connect(self.path) as database:
                await database.execute(
                    "DELETE FROM sessions WHERE token_hash = ?",
                    (_token_hash(token),),
                )
                await database.commit()

    async def close(self) -> None:
        return None


def _token_hash(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def build_session_store() -> SessionStore:
    """Create the configured store; SQLite is the Beta default."""
    mode = os.getenv("ESIMU_STARTER_SESSION_STORE", "sqlite").lower()
    if mode == "memory":
        return MemorySessionStore()
    if mode == "file":
        directory = Path(
            os.getenv("ESIMU_STARTER_DATA_DIR", "data/starter-sessions")
        )
        return FileSessionStore(directory)
    if mode != "sqlite":
        raise ValueError(f"unsupported ESIMU_STARTER_SESSION_STORE: {mode}")
    database_path = Path(
        os.getenv("ESIMU_STARTER_DATABASE_PATH", "data/esimu.sqlite3")
    )
    return SQLiteSessionStore(database_path)
