# Quickstart

This is the shortest verified path from a fresh clone to a running esimu
starter and a standalone generated simulator.

## 1. Clone And Install esimu

```powershell
git clone https://github.com/pirate-608/esimu.git
cd esimu
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements-dev.txt
```

The repository is self-contained. Do not point imports, validation commands, or
generated files at a ZJUers Simulator checkout.

## 2. Verify Core And Theme Data

```powershell
cd packages\esimu-core
python -m pytest tests
python -m ruff check esimu_core scripts tests
python scripts\validate_world_data.py
$env:ESIMU_THEME='demo-campus'
python scripts\validate_world_data.py
Remove-Item Env:ESIMU_THEME
```

The repository validator also checks checked-in frontend metadata. Downstream
projects use the installed project-local commands:

```powershell
esimu validate --root <project-root> --theme <theme-id>
esimu doctor --root <project-root> --theme <theme-id>
esimu inspect --root <project-root> --theme <theme-id>
esimu sync --root <project-root> --theme <theme-id>
```

## 3. Run The Starter Backend

```powershell
cd apps\starter\backend
python -m pytest tests
python -m ruff check app tests
python -m uvicorn app.main:app --reload --port 18001
```

Readiness is available at `http://127.0.0.1:18001/healthz`. The starter defaults
to SQLite at `data/esimu.sqlite3` and the `demo-campus` theme; tests select the
memory adapter explicitly.

## 4. Run The Starter Frontend

In a second terminal:

```powershell
cd apps\starter\frontend
corepack pnpm install --frozen-lockfile
corepack pnpm typecheck
corepack pnpm dev
```

Open `http://127.0.0.1:15175`. During development, Vite proxies `/api`,
`/config`, `/healthz`, and `/ws` to `http://127.0.0.1:18001`, so browser HTTP
and WebSocket traffic remain same-origin.

For a split-origin deployment, create `apps/starter/frontend/.env` from its
`.env.example` and set:

```dotenv
VITE_ESIMU_API_BASE=https://api.example.com
VITE_ESIMU_WS_BASE=wss://api.example.com
```

Allow that frontend origin on the backend:

```dotenv
ESIMU_CORS_ORIGINS=https://game.example.com
```

For same-origin production behind a reverse proxy, leave both `VITE_*` values
empty and route `/api`, `/config`, `/healthz`, and `/ws` to the backend.

## 5. Generate A Standalone Simulator

Install the exact Beta from PyPI, then generate the project:

```powershell
python -m pip install "esimu-core[ai]==0.3.0b2"
```

Then run:

```powershell
esimu new D:\projects\my-simulator `
  --project-name "My Simulator" `
  --theme-id my-simulator
```

The generated project contains its own Starter app, theme, assets, compatibility
helpers, README, environment template, and agent handoff. Its backend dependency
pins the exact `esimu-core` package version matching the generator.

Install and run entirely from the generated project:

```powershell
cd D:\projects\my-simulator
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r apps\starter\backend\requirements.txt
esimu validate --root . --theme my-simulator
esimu doctor --root . --theme my-simulator
cd apps\starter\backend
python -m uvicorn app.main:app --reload --port 18001
```

Framework contributors testing an unreleased version can pass
`--core-dependency` with an editable path or wheel URL.

## 6. Scaffold World Data

Installed authoring commands default to read-only previews and checks:

```powershell
cd D:\projects\my-simulator
esimu add stat focus --root . --theme my-simulator --label 专注 --show-in-hud
esimu add item focus_card --root . --theme my-simulator --name 专注卡
esimu add achievement first_win --root . --theme my-simulator --name 第一次胜利
esimu sync --root . --theme my-simulator
esimu validate --root . --theme my-simulator
```

Review generated JSON before repeating a command with `--write`. Writes are
atomic, synchronize frontend metadata, validate the theme, and roll back on
failure.

## 7. Run The Release-Candidate Gate

Maintainers should run the isolated installation smoke before tagging:

```powershell
cd esimu
python packages\esimu-core\scripts\release_smoke.py
```

It builds an sdist and wheel, generates a disposable simulator, creates a new
venv, installs `esimu-core[ai]` from the wheel, validates the copied theme, and
exercises the generated FastAPI starter. CI runs the same gate from a clean
checkout and checks that `esimu-core-v<version>` matches package metadata on tag
builds.

## 8. Build The Docs

```powershell
cd esimu
zensical build
```

Use `zensical serve` for local browsing. The generated `site/` directory is
ignored.

The documentation toolchain is pinned to Zensical 0.0.57 in
`docs/requirements.txt`.
