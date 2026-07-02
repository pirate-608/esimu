# Agent Handoff

This page is for future agents taking over esimu lab work.

## First Move

```powershell
cd D:\projects\simulator-framework-lab
git status --short
```

Do not assume the worktree is clean. The lab frequently contains extraction
work that has not yet been committed.

If you see modified files under both `simulator-core/` and `apps/zju-reference/`,
read the diff before touching either side. The reference app is often being
adapted to call newly extracted core helpers.

## Hard Boundary

Do not modify `D:\projects\ZJUers_simulator` unless the user explicitly requests
a cross-repository change.

The ZJU main game is the primary product. This lab is allowed to copy and
experiment, but it must not silently change the main game or depend on files in
the main game working tree.

## Current Extraction State

The backend extraction is currently split like this:

- `esimu_core.world`: active theme path resolution plus loaders for balance,
  stat definitions, items, theme manifests, story data, and prompt fragments.
- `esimu_core.domain`: pure gameplay rules for semester settlement, effects,
  stat bounds, relax overflow, and action gates.
- `esimu_core.runtime`: reusable runtime orchestration for clock math, action
  decisions, snapshot payloads, cooldown calculations, runtime DTOs, and
  background-task bookkeeping.
- `apps/zju-reference/zjus-backend`: adapter code that owns Redis, FastAPI,
  SQLAlchemy, WebSocket, save services, admin pages, and LLM clients.
- `apps/zju-reference/zjus-frontend`: copied frontend shell that consumes
  generated theme, story, and stat metadata.

Core modules must not import Redis, FastAPI, SQLAlchemy, OpenAI, WebSocket
objects, or reference-app services.

## Where To Put Work

- Add or tune world content in `themes/<theme_id>/world/`.
- Add display terms, storage prefixes, and theme assets in `theme.json`.
- Add long narrative copy in `story.json`.
- Add model-facing prompt context in `prompts.json`.
- Add pure stat/effect/semester/rules code in `simulator-core/backend/esimu_core/domain/`.
- Add pure tick/action/snapshot/task orchestration in `simulator-core/backend/esimu_core/runtime/`.
- Keep external I/O and compatibility glue in `apps/zju-reference/`.
- Update `docs/` whenever an extraction boundary or startup workflow changes.

## What Not To Do

- Do not reintroduce `sys.path` bridge code in the reference backend.
- Do not rename `cc98` or `dingtalk` internal IDs casually; they still appear in
  WebSocket payloads, Redis keys, saves, and tests.
- Do not add runtime multi-theme switching before single-theme startup is
  stable.
- Do not copy production secrets, deployment workflows, registry names, or
  database volumes from the ZJU main game.
- Do not use the lab to patch the main game by stealth. Cherry-pick mature
  improvements back only after review.

## Useful Validation Paths

Core from `simulator-core/backend/`:

```powershell
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe -m pytest tests
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe -m ruff check esimu_core scripts tests
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe scripts\validate_world_data.py
$env:SIMULATOR_THEME='demo-campus'; D:\projects\ZJUers_simulator\.venv\Scripts\python.exe scripts\validate_world_data.py
```

Reference backend from `apps/zju-reference/zjus-backend/`:

```powershell
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe -m pytest tests\unit
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe -m ruff check app tests\unit
```

Reference frontend from `apps/zju-reference/zjus-frontend/`:

```powershell
npx vue-tsc --noEmit
npx vitest run
npx vite build
```

For docs-only changes, prefer:

```powershell
git diff --check
```

Then manually confirm all linked `docs/*.md` paths exist.

## New Project Hand-off

When creating a new simulator project from this lab:

1. Start from `docs/new-project-bootstrap.md`.
2. Copy `templates/agent/AGENTS.md` into the new project.
3. Fill in project-specific roots, commands, theme IDs, and deployment limits.
4. Keep esimu package names exact: package `esimu-core`, import namespace
   `esimu_core`.
