# esimu Starter Backend

This is the Beta FastAPI/WebSocket adapter. SQLite is the default persistence,
`demo-campus` is the default theme, and reusable rules come from `esimu-core`.
The v2 runtime persists cooldowns, achievements, content mode, ending state,
and messenger rounds while loading v1 state automatically.

Run locally:

```powershell
cd esimu\apps\starter\backend
python -m uvicorn app.main:app --reload --port 18001
```

Smoke checks:

```powershell
python -m pytest tests
```

SQLite targets single-node Beta deployments. Distributed persistence,
production identity, and mandatory model calls remain downstream concerns.

Optional file-backed development sessions:

```powershell
$env:ESIMU_STARTER_SESSION_STORE='file'
$env:ESIMU_STARTER_DATA_DIR='data/starter-sessions'
python -m uvicorn app.main:app --reload --port 18001
```

The file store writes JSON state per token and is meant as an extension point,
not as production storage.

Event, forum, and messenger AI calls use target-deduplicated background tasks.
Player messages are persisted before the NPC reply starts generating, so Tick
and unrelated actions stay responsive.

Optional AI example:

```powershell
$env:ESIMU_CONTENT_MODE='hybrid'
$env:ESIMU_LLM_PROVIDER='ollama'
$env:ESIMU_LLM_MODEL='qwen3:8b'
python -m uvicorn app.main:app --reload --port 18001
```

See `docs/ai-integration.md` for cloud providers, MiniMax M2-her, security
boundaries, and fallback semantics.
