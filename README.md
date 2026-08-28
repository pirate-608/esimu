# esimu

[English](README.md) | [简体中文](README.zh-CN.md)

esimu is a theme-driven framework for campus, career, and life simulators.
Its Beta shape is:

```text
esimu-core + generated Starter app + one theme pack
```

`esimu-core 0.3.0b1` provides typed world loaders, theme validation, gameplay
rules, runtime payload helpers, optional AI generation, and a self-contained
project CLI. The generated Starter includes a Vue 3/Pinia console, FastAPI and
WebSocket adapter, real-time ticks, events, forum and messenger flows, items,
semester settlement, cooldowns, declarative achievements, automatic content,
distinct endings, and SQLite persistence.

## Quick Start

Until `0.3.0b1` is published, install the candidate from a source checkout:

```powershell
python -m pip install -e ".\packages\esimu-core[ai]"
esimu new D:\projects\my-simulator `
  --project-name "My Simulator" `
  --theme-id my-simulator `
  --institution "Star Academy"
cd D:\projects\my-simulator
python -m pip install -r apps\starter\backend\requirements.txt
esimu validate --root . --theme my-simulator
esimu doctor --root . --theme my-simulator
```

Run the backend:

```powershell
cd apps\starter\backend
python -m uvicorn app.main:app --reload --port 18001
```

Run the frontend in another terminal:

```powershell
cd apps\starter\frontend
corepack pnpm install --frozen-lockfile
corepack pnpm dev
```

Open `http://127.0.0.1:15175`.

## Repository

```text
packages/esimu-core/    Installable Python core and CLI
apps/starter/           Canonical FastAPI + Vue Starter
themes/demo-campus/     Neutral two-semester example theme
templates/              Generated-project handoff templates
docs/                   English and Chinese Zensical documentation
```

The old ZJU extraction reference was archived in the `esimu-lab-final` tag and
is not part of the formal Beta branch. ZJUers Simulator remains a separate
product and is not a runtime dependency.

## Development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pytest packages\esimu-core\tests
python -m pytest apps\starter\backend\tests
python packages\esimu-core\scripts\sync_scaffold_bundle.py
zensical build
```

Frontend checks:

```powershell
cd apps\starter\frontend
corepack pnpm install --frozen-lockfile
corepack pnpm typecheck
corepack pnpm test
corepack pnpm build
```

See the [Quickstart](docs/quickstart.md), [theme contract](docs/theme-pack-contract.md),
[architecture](docs/architecture.md), [Beta support policy](docs/beta-support.md),
and [release policy](docs/release-policy.md).

## Compatibility

- Distribution: `esimu-core`
- Import namespace: `esimu_core`
- CLI: `esimu new`, `validate`, `doctor`, `inspect`, `sync`, `add`, and `version`
- Theme schema: version `1`
- Starter state schema: version `2` with automatic v1 migration
- Starter WebSocket protocol: version `2` with v1 client compatibility
- License: MIT

The Beta intentionally does not provide runtime multi-theme switching,
production identity, Redis/PostgreSQL adapters, or a separate npm package.
