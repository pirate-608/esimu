# Contributing

Use Python 3.11–3.13, Node 22, and pnpm 9. Before opening a pull request:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest packages\esimu-core\tests
python -m pytest apps\starter\backend\tests
python -m ruff check packages\esimu-core\esimu_core packages\esimu-core\scripts packages\esimu-core\tests apps\starter\backend\app apps\starter\backend\tests
cd apps\starter\frontend
corepack pnpm install --frozen-lockfile
corepack pnpm typecheck
corepack pnpm test
corepack pnpm build
```

Reusable pure rules belong in `packages/esimu-core`. FastAPI, SQLite,
WebSocket, and UI integration belong in `apps/starter`. Visible world content
belongs in `themes/<theme_id>`.

