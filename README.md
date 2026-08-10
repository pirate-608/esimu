# Simulator Framework Lab

[English](README.md) | [简体中文](README.zh-CN.md)

`esimu` is an experimental lab for extracting a reusable narrative-simulator
framework from ZJUers Simulator without disturbing the live ZJU game.

This repository is an alpha release candidate: its core, Starter, generator,
and isolated wheel-install smoke are runnable, but no version is externally
released until the matching Git tag is pushed. The framework shape is:

```text
esimu-core + starter app + a selected theme pack
```

## Current Status

- `apps/starter/` is the first minimal non-ZJU starter app, using
  `demo-campus` by default and keeping backend state in memory. This is the
  default app path for new projects.
- `apps/zju-reference/` is an optional compatibility-rich reference adapter,
  copied and isolated from the main ZJUers Simulator workspace. It is useful
  for regression checks, but it is not required to run esimu.
- `simulator-core/backend/` contains the installable Python package
  `esimu-core`, imported as `esimu_core.*`.
- `esimu_core.ai` provides optional OpenAI-compatible and MiniMax M2-her
  generation with theme prompts, output validation, and local degradation.
- `themes/zju/` is the first full reference theme.
- `themes/demo-campus/` is a tiny validation theme used to catch hidden ZJU
  assumptions.
- `docs/` contains the architecture notes, roadmap, theme contract, quickstart,
  release policy, readiness review, and project-bootstrap guide.
- `mkdocs.yml` configures the Zensical documentation site for this framework.

ZJUers Simulator remains the main product. Mature improvements from this lab
must be reviewed and intentionally cherry-picked back; the main game must never
depend on this lab by accident.

## 10 Minute Quickstart

Start here when opening the lab for the first time:

```powershell
git clone https://github.com/pirate-608/esimu-lab.git
cd esimu-lab
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements-dev.txt
git status --short
```

Then read:

1. `AGENTS.md` for workspace rules and agent handoff notes.
2. `docs/quickstart.md` for setup and validation commands.
3. `docs/architecture.md` for the current core/theme/adapter boundary.
4. `docs/new-project-bootstrap.md` when starting a new simulator theme or app.
5. `docs/starter-app-shape.md` before copying the reference app.
6. `docs/starter-contract.md` for the starter HTTP/WebSocket and persistence surface.
7. `docs/release-policy.md` before tagging `esimu-core`.
8. `docs/framework-readiness-review.md` for the current framework verdict.
9. `docs/ai-integration.md` for optional model integration and security boundaries.

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
python -m pytest tests
python -m ruff check esimu_core scripts tests
python scripts\validate_world_data.py
$env:SIMULATOR_THEME='demo-campus'; python scripts\validate_world_data.py
```

Optional reference backend checks from `apps/zju-reference/zjus-backend/`:

```powershell
python -m pytest tests\unit
python -m ruff check app tests\unit
```

Optional reference frontend checks from `apps/zju-reference/zjus-frontend/`:

```powershell
npx vue-tsc --noEmit
npx vitest run
npx vite build
```

These reference checks are optional compatibility checks. They are intentionally
separate from the default core/starter/docs path.

See `docs/quickstart.md` for install notes, editable-package fallback, and
theme metadata generation commands.

Starter frontend checks from `apps/starter/frontend/`:

```powershell
corepack pnpm install --frozen-lockfile
corepack pnpm typecheck
corepack pnpm build
```

Release-candidate and docs checks from the lab root:

```powershell
python simulator-core\backend\scripts\release_smoke.py
zensical build
```

The release smoke builds a wheel, installs it into a disposable venv, generates
a standalone simulator, validates its theme, and exercises its Starter API.

## Repository Layout

```text
apps/
  starter/            # Minimal non-ZJU starter backend/frontend.
  zju-reference/      # Optional compatibility-rich reference adapter.
simulator-core/
  backend/            # esimu-core Python package, scripts, and tests.
  frontend/           # Future extracted Vue/runtime frontend pieces.
themes/
  zju/                # Full ZJU reference theme.
  demo-campus/        # Minimal portability validation theme.
docs/
  index.md
  quickstart.md
  new-project-bootstrap.md
  starter-app-shape.md
  starter-contract.md
  release-policy.md
  framework-readiness-review.md
  agent-handoff.md
  architecture.md
  roadmap.md
  theme-pack-contract.md
templates/
  agent/AGENTS.md     # Copyable starter handoff template.
mkdocs.yml            # Zensical-compatible documentation site config.
requirements-dev.txt  # Fresh-clone development dependency entry point.
```

## Starting A New Simulator

Use `docs/new-project-bootstrap.md` as the main checklist. The short version is:

1. Generate a starter project with `simulator-core/backend/scripts/new_project.py`.
2. Edit the generated `theme.json`, `story.json`, `prompts.json`, and `world/`.
3. Run world-data validation for the generated theme.
4. Continue from the generated `apps/starter/` shell, or read
   `docs/starter-app-shape.md` before choosing the full reference adapter.
5. Keep ZJU-specific protocol IDs such as `cc98` and `dingtalk` as compatibility
   IDs until the roadmap explicitly migrates them.

Example:

```powershell
cd esimu-lab\simulator-core\backend
python scripts\new_project.py <target-project> --project-name "My Simulator" --theme-id my-simulator
cd <target-project>
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r apps\starter\backend\requirements.txt
esimu-validate-world --root . --theme my-simulator
```

The final install commands require the Git tag matching `esimu_core.__version__`
to have been pushed. Use `--core-dependency` with a local wheel or editable path
while testing unreleased framework work.

## Naming

- Framework shorthand: `esimu`
- Core package name: `esimu-core`
- Python import namespace: `esimu_core`

Do not introduce old temporary framework-core names except in historical notes.

## Releases

`esimu-core` uses Git tags in the independent `esimu-lab` repository as its
intended alpha release channel. The version source is
`simulator-core/backend/esimu_core/__init__.py`; a version becomes externally
installable only after the matching `esimu-core-v<version>` tag is pushed and
tag CI passes. See `docs/release-policy.md` for the exact gate.
