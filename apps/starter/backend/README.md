# esimu Starter Backend

This is the first minimal non-ZJU backend adapter. It is intentionally small:
state is kept in memory by default, the default theme is `demo-campus`, and all
reusable game rules come from `esimu-core`.

Run locally:

```powershell
cd esimu-lab\apps\starter\backend
python -m uvicorn app.main:app --reload --port 18001
```

Smoke checks:

```powershell
python -m pytest tests
```

The starter is not a production persistence model. It exists to show what a new
project can copy before deciding whether to add Redis, PostgreSQL, admin pages,
or mandatory model calls. The optional framework AI adapter is available but
defaults to local `library` mode.

Optional file-backed development sessions:

```powershell
$env:ESIMU_STARTER_SESSION_STORE='file'
$env:ESIMU_STARTER_DATA_DIR='data/starter-sessions'
python -m uvicorn app.main:app --reload --port 18001
```

The file store writes JSON state per token and is meant as an extension point,
not as production storage.

Optional AI example:

```powershell
$env:ESIMU_CONTENT_MODE='hybrid'
$env:ESIMU_LLM_PROVIDER='ollama'
$env:ESIMU_LLM_MODEL='qwen3:8b'
python -m uvicorn app.main:app --reload --port 18001
```

See `docs/ai-integration.md` for cloud providers, MiniMax M2-her, security
boundaries, and fallback semantics.
