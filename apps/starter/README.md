# esimu Starter App

`apps/starter/` is the first minimal non-ZJU app shape. It exists to prove that
a new simulator can start from `esimu-core` and a theme pack without importing
or editing `apps/zju-reference/`.

Current scope:

- `backend/`: FastAPI adapter with in-memory session state.
- `frontend/`: tiny Vite/TypeScript skin that consumes generated theme, story,
  and stat metadata.
- Default theme: `demo-campus`.
- Optional local file sessions through `ESIMU_STARTER_SESSION_STORE=file`.

The starter deliberately omits Redis, PostgreSQL, SQLAdmin, and production
Docker. It includes the optional `esimu_core.ai` adapter but stays in local
`library` mode until `ESIMU_CONTENT_MODE` and model environment variables are
configured. See `docs/ai-integration.md`.

See `docs/starter-contract.md` for the public starter surface.

Backend smoke:

```powershell
cd esimu-lab\apps\starter\backend
python -m pytest tests
```

Backend dev server:

```powershell
python -m uvicorn app.main:app --reload --port 18001
```

Frontend dev server:

```powershell
cd esimu-lab\apps\starter\frontend
corepack pnpm install --frozen-lockfile
corepack pnpm dev
```

Frontend checks:

```powershell
corepack pnpm typecheck
corepack pnpm build
```
