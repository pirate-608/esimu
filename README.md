# esimu

[English](README.md) | [简体中文](README.zh-CN.md)

esimu is a theme-driven framework for campus, career, and life simulators.
Its Beta shape is:

```text
esimu-core + generated Starter app + one theme pack
```

The latest public PyPI release remains `0.3.0b2`; `dev`, `reload`, `build`, and
the new default template are being prepared on `main` for `0.4.0b1`.

The current source candidate `esimu-core 0.4.0b1` provides typed world loaders,
theme validation, gameplay
rules, runtime payload helpers, optional AI generation, and a self-contained
project CLI. The generated Starter includes a Vue 3/Pinia console, FastAPI and
WebSocket adapter, real-time ticks, events, forum and messenger flows, items,
semester settlement, cooldowns, declarative achievements, automatic content,
distinct endings, and SQLite persistence.

## Quick Start

Clone the source candidate to use the new lifecycle commands:

```powershell
git clone https://github.com/pirate-608/esimu.git
cd esimu
python -m pip install -e ".\packages\esimu-core[ai]"
esimu new D:\projects\zju-lite `
  --project-name "ZJUers Simulator Lite" `
  --theme-id zju-lite `
  --institution "Zhejiang University"
cd D:\projects\zju-lite
python -m pip install -r apps\starter\backend\requirements.txt
esimu validate --root . --theme zju-lite
esimu doctor --root . --theme zju-lite
esimu dev --root . --theme zju-lite
```

From another terminal, request a synchronized full restart:

```powershell
esimu reload --root . --theme zju-lite
```

Build a production frontend:

```powershell
esimu build --root . --theme zju-lite
```

Open `http://127.0.0.1:15175`.

Pass `--source-theme demo-campus` to `esimu new` for a fully neutral template.

## Repository

```text
packages/esimu-core/    Installable Python core and CLI
apps/starter/           Canonical FastAPI + Vue Starter
themes/demo-campus/     Neutral two-semester example theme
themes/zju-simplified/  Default compact ZJU adaptation
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

See the [Quickstart](docs/quickstart.md), [CLI reference](docs/cli.md),
[theme contract](docs/theme-pack-contract.md), [architecture](docs/architecture.md),
[Beta support policy](docs/beta-support.md), and [release policy](docs/release-policy.md).

## Compatibility

- Distribution: `esimu-core`
- Import namespace: `esimu_core`
- CLI: `esimu new`, `validate`, `doctor`, `inspect`, `sync`, `add`, `dev`,
  `reload`, `build`, and `version`
- Theme schema: version `1`
- Starter state schema: version `2` with automatic v1 migration
- Starter WebSocket protocol: version `2` with v1 client compatibility
- License: MIT

The Beta intentionally does not provide runtime multi-theme switching,
production identity, Redis/PostgreSQL adapters, or a separate npm package.
