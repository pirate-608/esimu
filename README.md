# Simulator Framework Lab

`esimu` is an experimental lab for extracting a reusable narrative-simulator
framework from ZJUers Simulator without disturbing the live ZJU game.

This repository is not a finished framework yet. It is a controlled workspace
for proving that the ZJU game can become:

```text
esimu-core + a reference adapter + a selected theme pack
```

## Current Status

- `apps/zju-reference/` is the first runnable reference app, copied and
  isolated from the main ZJUers Simulator workspace.
- `simulator-core/backend/` contains the installable Python package
  `esimu-core`, imported as `esimu_core.*`.
- `themes/zju/` is the first full reference theme.
- `themes/demo-campus/` is a tiny validation theme used to catch hidden ZJU
  assumptions.
- `docs/` contains the architecture notes, roadmap, theme contract, quickstart,
  and project-bootstrap guide.

ZJUers Simulator remains the main product. Mature improvements from this lab
must be reviewed and intentionally cherry-picked back; the main game must never
depend on this lab by accident.

## 10 Minute Quickstart

Start here when opening the lab for the first time:

```powershell
cd D:\projects\simulator-framework-lab
git status --short
```

Then read:

1. `AGENTS.md` for workspace rules and agent handoff notes.
2. `docs/quickstart.md` for setup and validation commands.
3. `docs/architecture.md` for the current core/theme/adapter boundary.
4. `docs/new-project-bootstrap.md` when starting a new simulator theme or app.

The active theme is selected at build/startup time:

```powershell
$env:SIMULATOR_THEME='zju'
$env:SIMULATOR_THEME='demo-campus'
```

Runtime multi-theme switching is intentionally out of scope for the current
lab phase.

## Common Commands

Core checks from `simulator-core/backend/`:

```powershell
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe -m pytest tests
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe -m ruff check esimu_core scripts tests
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe scripts\validate_world_data.py
$env:SIMULATOR_THEME='demo-campus'; D:\projects\ZJUers_simulator\.venv\Scripts\python.exe scripts\validate_world_data.py
```

Reference backend checks from `apps/zju-reference/zjus-backend/`:

```powershell
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe -m pytest tests\unit
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe -m ruff check app tests\unit
```

Reference frontend checks from `apps/zju-reference/zjus-frontend/`:

```powershell
npx vue-tsc --noEmit
npx vitest run
npx vite build
```

See `docs/quickstart.md` for install notes, editable-package fallback, and
theme metadata generation commands.

## Repository Layout

```text
apps/
  zju-reference/      # Runnable copied app and first adapter.
simulator-core/
  backend/            # esimu-core Python package, scripts, and tests.
  frontend/           # Future extracted Vue/runtime frontend pieces.
themes/
  zju/                # Full ZJU reference theme.
  demo-campus/        # Minimal portability validation theme.
docs/
  quickstart.md
  new-project-bootstrap.md
  agent-handoff.md
  architecture.md
  roadmap.md
  theme-pack-contract.md
templates/
  agent/AGENTS.md     # Copyable starter handoff template.
```

## Starting A New Simulator

Use `docs/new-project-bootstrap.md` as the main checklist. The short version is:

1. Copy `themes/demo-campus/` to a new `themes/<theme_id>/`.
2. Edit `theme.json`, `story.json`, `prompts.json`, and `world/`.
3. Run world-data validation for the new theme.
4. Reuse `apps/zju-reference/` as the first adapter only if you need a runnable
   app immediately.
5. Keep ZJU-specific protocol IDs such as `cc98` and `dingtalk` as compatibility
   IDs until the roadmap explicitly migrates them.

## Naming

- Framework shorthand: `esimu`
- Core package name: `esimu-core`
- Python import namespace: `esimu_core`

Do not introduce old temporary framework-core names except in historical notes.
