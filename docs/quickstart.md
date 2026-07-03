# Quickstart

This page is the shortest path from a fresh checkout to a useful esimu lab
session.

## 1. Open The Lab

```powershell
cd D:\projects\ZJUers_simulator\labs\esimu
git status --short
```

If the worktree is dirty, read the diff before editing the same files. This lab
often keeps extraction work in progress between sessions.

The lab is a submodule under `D:\projects\ZJUers_simulator\labs\esimu`. Do not
modify the main ZJU game outside `labs/esimu` unless the user explicitly asks
for a cross-repository change.

## 2. Know The Four Moving Parts

```text
simulator-core/backend/   # esimu-core Python package.
apps/zju-reference/       # Runnable adapter copied from ZJUers Simulator.
themes/zju/               # Full reference theme.
themes/demo-campus/       # Minimal portability theme.
```

`esimu-core` is installed as a Python package and imported as `esimu_core.*`.
The reference app should not use temporary `sys.path` bridges.

## 3. Pick A Python Runtime

The lab currently reuses the ZJU development virtual environment:

```powershell
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe --version
```

From `apps/zju-reference/zjus-backend/`, the editable requirement should point
back to the local core package:

```text
-e ../../../simulator-core/backend
```

If editable install support is unavailable in an offline Windows environment, a
local `.pth` file pointing at
`D:\projects\ZJUers_simulator\labs\esimu\simulator-core\backend` is acceptable
for development. Do not add bridge code to the reference backend or point the
venv at the old standalone lab path.

## 4. Validate Core And Theme Data

Run these from `simulator-core/backend/`:

```powershell
cd D:\projects\ZJUers_simulator\labs\esimu\simulator-core\backend
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe -m pytest tests
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe -m pytest tests\test_world_catalog.py
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe -m pytest tests\test_demo_theme_smoke.py
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe -m pytest tests\test_lifecycle_contracts.py
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe -m pytest tests\test_content_contracts.py
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe -m ruff check esimu_core scripts tests
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe scripts\validate_world_data.py
$env:SIMULATOR_THEME='demo-campus'; D:\projects\ZJUers_simulator\.venv\Scripts\python.exe scripts\validate_world_data.py
```

The first validation uses the default `zju` theme. The second confirms that the
minimal `demo-campus` theme still catches portability issues. The
`test_demo_theme_smoke.py` smoke starts a fresh Python process with
`SIMULATOR_THEME=demo-campus` so singleton loaders cannot accidentally reuse the
default ZJU theme.

## 5. Regenerate Theme Metadata When Needed

Run these from `simulator-core/backend/` after changing theme, story, or stat
definitions:

```powershell
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe scripts\sync_theme_metadata.py --write
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe scripts\sync_story_metadata.py --write
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe scripts\sync_stat_definitions.py --write
```

Then run validation again.

## 6. Check The Reference Backend

Run these from `apps/zju-reference/zjus-backend/`:

```powershell
cd D:\projects\ZJUers_simulator\labs\esimu\apps\zju-reference\zjus-backend
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe -m pytest tests\unit\test_demo_campus_reference_smoke.py
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe -m pytest tests\unit
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe -m ruff check app tests\unit
```

The reference backend is the adapter layer. It may use Redis, FastAPI,
SQLAlchemy, WebSocket, and OpenAI-compatible clients. The core package should
not. The demo-campus smoke starts a fresh process so active-theme singletons are
loaded in the same order as a real app startup.

## 7. Check The Reference Frontend

Run these from `apps/zju-reference/zjus-frontend/`:

```powershell
cd D:\projects\ZJUers_simulator\labs\esimu\apps\zju-reference\zjus-frontend
npx vue-tsc --noEmit
npx vitest run src\utils\theme.spec.ts
npx vitest run src\components\themeRuntime.spec.js
npx vitest run
npx vite build
```

`themeRuntime.spec.js` is the quick smoke for mocked `demo-campus` frontend
metadata. It checks that App startup copy and browser storage keys follow the
generated theme manifest instead of fixed ZJU/simlab values.

If a command fails only because an agent sandbox cannot spawn esbuild, treat it
as an execution-environment issue and rerun outside the sandbox. Do not add fake
environment variables or wrapper scripts for esbuild.

## 8. Where To Read Next

- `architecture.md`: current core/theme/adapter split.
- `theme-pack-contract.md`: required theme files and fields.
- `new-project-bootstrap.md`: how to start a new simulator from esimu.
- `agent-handoff.md`: current agent operating notes.
