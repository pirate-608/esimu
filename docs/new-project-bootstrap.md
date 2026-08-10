# New Project Bootstrap

This checklist starts a simulator that can run independently after generation.
The generator copies the small Starter app and one theme; it does not copy the
ZJU reference product.

## Generate The Project

From an esimu-lab checkout:

```powershell
cd simulator-core\backend
python scripts\new_project.py D:\projects\my-simulator `
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
scripts/scaffold_game_stat.py
scripts/scaffold_world_data.py
docs/scaffold-checklist.md
.env.example
AGENTS.md
README.md
```

The backend requirement defaults to the Git tag matching the generator's
`esimu_core.__version__`. That tag must exist remotely before another developer
can install it. For unreleased development, pass an explicit dependency:

```powershell
python scripts\new_project.py D:\projects\my-simulator `
  --core-dependency "-e D:\projects\esimu-lab\simulator-core\backend[ai]"
```

A wheel URL is preferred when testing the exact release artifact.

## Install And Validate Independently

After the tagged core is available:

```powershell
cd D:\projects\my-simulator
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r apps\starter\backend\requirements.txt
esimu-validate-world --root . --theme my-simulator
```

The installed command resolves the generated project's own `themes/` directory.
It does not need `validate_world_data.py` or any path back to esimu-lab.

## Run The App

Backend:

```powershell
cd apps\starter\backend
python -m uvicorn app.main:app --reload --port 18001
```

Frontend in a second terminal:

```powershell
cd apps\starter\frontend
corepack pnpm install --frozen-lockfile
corepack pnpm dev
```

Open `http://127.0.0.1:15175`. The checked-in Vite proxy connects both HTTP and
WebSocket traffic to the backend. See `starter-contract.md` for split-origin and
reverse-proxy deployment.

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
$env:SIMULATOR_LAB_ROOT=(Get-Location).Path
$env:SIMULATOR_THEME='my-simulator'
python scripts\scaffold_game_stat.py add focus --label Focus --show-in-hud
python scripts\scaffold_world_data.py item focus_card --name "Focus Card"
python scripts\scaffold_world_data.py achievement first_win --name "First Win"
python scripts\scaffold_world_data.py event campus_moment --title "Campus Moment"
esimu-validate-world --root . --theme my-simulator
```

Review output before adding `--write`.

## Choose Persistence And AI Deliberately

Starter defaults to memory persistence and library content. File persistence is
available for local development. Production Redis/PostgreSQL, admin editors,
shared caches, credentials, billing, and telemetry remain adapter concerns.

Enable the optional `esimu_core.ai` transport only after reviewing
`ai-integration.md` and filling the generated `.env.example` values.

Use `apps/zju-reference/` only as a compatibility reference when a project
immediately needs its heavier production shape. It is not a required dependency.