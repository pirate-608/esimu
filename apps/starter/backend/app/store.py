"""Session stores for the esimu starter backend.

Copyright (c) 2026 pirate-608. Licensed under the MIT License.

The starter defaults to in-memory sessions but exposes a tiny persistence seam
for downstream prototypes. The file store is intentionally simple and aimed at
local development, not production durability.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Protocol

from app.session import StarterGameSession


class SessionStore(Protocol):
    """Persistence protocol used by the starter FastAPI adapter."""

    def get(self, token: str) -> StarterGameSession | None:
        """Return an existing session or ``None``."""

    def set(self, token: str, session: StarterGameSession) -> None:
        """Persist or replace one session."""

    def pop(self, token: str) -> None:
        """Delete a session if present."""


class MemorySessionStore:
    """Process-local session store used by default."""

    def __init__(self) -> None:
        self._sessions: dict[str, StarterGameSession] = {}

    def get(self, token: str) -> StarterGameSession | None:
        """Return a process-local session."""
        return self._sessions.get(token)

    def set(self, token: str, session: StarterGameSession) -> None:
        """Store a process-local session."""
        self._sessions[token] = session

    def pop(self, token: str) -> None:
        """Remove a process-local session."""
        self._sessions.pop(token, None)


class FileSessionStore:
    """JSON-file session store for local starter development."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def get(self, token: str) -> StarterGameSession | None:
        """Load a session from disk."""
        path = self._path(token)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return StarterGameSession.from_state(data)

    def set(self, token: str, session: StarterGameSession) -> None:
        """Atomically write a session JSON file."""
        path = self._path(token)
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(
            json.dumps(session.export_state(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(tmp_path, path)

    def pop(self, token: str) -> None:
        """Delete a session JSON file."""
        self._path(token).unlink(missing_ok=True)

    def _path(self, token: str) -> Path:
        safe = "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in token)
        return self.directory / f"{safe}.json"


def build_session_store() -> SessionStore:
    """Create the configured starter session store.

    ``ESIMU_STARTER_SESSION_STORE=file`` enables a local JSON store. Any other
    value keeps the memory-only default.
    """
    if os.getenv("ESIMU_STARTER_SESSION_STORE", "memory").lower() == "file":
        data_dir = Path(os.getenv("ESIMU_STARTER_DATA_DIR", "data/starter-sessions"))
        return FileSessionStore(data_dir)
    return MemorySessionStore()
