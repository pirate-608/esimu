# esimu Starter App

`apps/starter/` is the canonical Beta application built from `esimu-core` and
a theme pack, without product-specific dependencies.

Current scope:

- `backend/`: FastAPI/WebSocket adapter with SQLite persistence by default.
- `frontend/`: Vue 3/Pinia console driven by generated theme, story, and stat metadata.
- Default theme: `zju-simplified`; use `demo-campus` for a neutral example.
- State/protocol v2 with state-v1 and protocol-v1 compatibility.
- Persistent cooldowns, achievements, automatic content, two-phase messenger
  replies, save/exit lifecycle, and distinct failure/graduation outcomes.
- Memory sessions for tests and temporary file compatibility through the 0.4 Beta.

The starter deliberately omits Redis, PostgreSQL, SQLAdmin, and production
Docker. It includes the optional `esimu_core.ai` adapter but stays in local
`library` mode until `ESIMU_CONTENT_MODE` and model environment variables are
configured. See `docs/ai-integration.md`.

See `docs/starter-contract.md` for the public starter surface.

Backend smoke:

```powershell
cd esimu\apps\starter\backend
python -m pytest tests
```

Run both development servers from the project root:

```powershell
esimu dev --root . --theme zju-simplified
```

Request a synchronized full restart from another terminal:

```powershell
esimu reload --root . --theme zju-simplified
```

Build the production frontend:

```powershell
esimu build --root . --theme zju-simplified
```
