# esimu Starter App

`apps/starter/` is the canonical Beta application built from `esimu-core` and
a theme pack, without product-specific dependencies.

Current scope:

- `backend/`: FastAPI/WebSocket adapter with SQLite persistence by default.
- `frontend/`: Vue 3/Pinia console driven by generated theme, story, and stat metadata.
- Default theme: `demo-campus`.
- State/protocol v2 with state-v1 and protocol-v1 compatibility.
- Persistent cooldowns, achievements, automatic content, two-phase messenger
  replies, save/exit lifecycle, and distinct failure/graduation outcomes.
- Memory sessions for tests and temporary file compatibility through the 0.3 Beta.

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

Backend dev server:

```powershell
python -m uvicorn app.main:app --reload --port 18001
```

Frontend dev server:

```powershell
cd esimu\apps\starter\frontend
corepack pnpm install --frozen-lockfile
corepack pnpm dev
```

Frontend checks:

```powershell
corepack pnpm typecheck
corepack pnpm test
corepack pnpm build
```
