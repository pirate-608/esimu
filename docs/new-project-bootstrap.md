# New Project Bootstrap

This checklist starts a simulator that can run independently after generation.
The generator copies the canonical Starter app and one theme into a standalone
project.

The default source theme is `zju-simplified`, a compact, self-contained
adaptation with neutral `forum` and `messenger` protocol IDs. Add
`--source-theme demo-campus` when starting from fully neutral content.

## Generate The Project

With `esimu-core==0.4.0b2` installed:

```powershell
esimu new D:\projects\my-simulator `
  --project-name "My Simulator" `
  --theme-id my-simulator `
  --institution "Star Academy" `
  --institution-short "Star"
```

Generated shape:

```text
apps/starter/backend/
apps/starter/frontend/
themes/my-simulator/
scripts/
docs/scaffold-checklist.md
.env.example
AGENTS.md
README.md
```

The generated scripts are Beta compatibility wrappers. Prefer installed
`esimu add` and `esimu sync` commands for new automation.

The backend requirement pins the exact package version matching the generator's
`esimu_core.__version__`. That version must exist on the selected package index
before another developer can install it. For unreleased development, pass an
explicit dependency:

```powershell
esimu new D:\projects\my-simulator `
  --core-dependency "-e D:\projects\esimu\packages\esimu-core[ai]"
```

A wheel URL is preferred when testing the exact release artifact.

## Install And Validate Independently

After the package version is available:

```powershell
cd D:\projects\my-simulator
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r apps\starter\backend\requirements.txt
esimu validate --root . --theme my-simulator
esimu doctor --root . --theme my-simulator
```

The installed command resolves the generated project's own `themes/` directory.
It does not need `validate_world_data.py` or any path back to esimu.

## Run And Build The App

```powershell
esimu dev --root . --theme my-simulator
```

In another terminal:

```powershell
esimu reload --root . --theme my-simulator
esimu build --root . --theme my-simulator
```

Open `http://127.0.0.1:15175`. The checked-in Vite proxy connects both HTTP and
WebSocket traffic to the backend. See `starter-contract.md` for split-origin and
reverse-proxy deployment. `reload` synchronizes metadata and validates the
theme before restarting both services; `build` produces the frontend `dist/`.

## Edit The Theme

Keep the deployment single-theme for now. Edit:

```text
themes/my-simulator/theme.json
themes/my-simulator/story.json
themes/my-simulator/prompts.json
themes/my-simulator/world/
themes/my-simulator/assets/
```

Recommended order:

1. stats and balance,
2. items and economy,
3. majors and courses,
4. achievements and characters,
5. event/forum/message libraries,
6. story assets and model prompts.

Use `theme.json` for short structural terms, `story.json` for narrative copy,
and `prompts.json` for model-facing context.

## Use The Copied Scaffold Helpers

```powershell
cd D:\projects\my-simulator
$env:ESIMU_PROJECT_ROOT=(Get-Location).Path
$env:ESIMU_THEME='my-simulator'
esimu add stat focus --root . --theme my-simulator --label Focus --show-in-hud
esimu add item focus_card --root . --theme my-simulator --name "Focus Card"
esimu add achievement first_win --root . --theme my-simulator --name "First Win"
esimu add event campus_moment --root . --theme my-simulator --title "Campus Moment"
esimu sync --root . --theme my-simulator
esimu validate --root . --theme my-simulator
```

Review output before adding `--write`.

## Choose Persistence And AI Deliberately

Starter defaults to SQLite persistence and library content. File persistence is
available for local development. Production Redis/PostgreSQL, admin editors,
shared caches, credentials, billing, and telemetry remain adapter concerns.

Enable the optional `esimu_core.ai` transport only after reviewing
`ai-integration.md` and filling the generated `.env.example` values.

Add production identity or distributed persistence as project-owned adapters;
they are intentionally not copied by the Beta generator.
