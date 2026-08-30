# AGENTS.md

This file is the handoff guide for AI agents working in this simulator project.
Fill in the placeholders before using it in a real project.

## Project Snapshot

- Project name: `<project-name>`
- Project root: `<absolute-project-root>`
- Active theme ID: `<theme-id>`
- Core package: `esimu-core`
- Python import namespace: `esimu_core`
- Reference or app backend: `<backend-path>`
- Frontend: `<frontend-path>`
- Theme pack: `<theme-path>`

## Prime Directive

Protect the production game and user data. Do not modify unrelated repositories,
production secrets, deployment workflows, databases, or generated files unless
the user explicitly asks for that scope.

## Startup Checklist

```powershell
cd <absolute-project-root>
git status --short
```

Before editing:

- Confirm you are in the intended project root.
- Read dirty diffs before touching modified files.
- Confirm the task belongs to this project and not a source/reference project.
- Identify whether the change belongs in core, adapter, theme data, frontend,
  docs, or deployment config.

## Architecture Boundary

- `esimu_core.world` loads theme and world data.
- `esimu_core.domain` owns pure gameplay rules.
- `esimu_core.runtime` owns pure runtime orchestration.
- The app backend owns I/O: web framework, Redis, database, WebSocket, admin,
  save service, and LLM clients.
- The frontend consumes generated theme/story/stat metadata where available.

Core modules must not import app services, web framework objects, Redis,
SQLAlchemy, OpenAI clients, or WebSocket objects.

## Theme Rules

Theme packs own:

```text
theme.json
story.json
prompts.json
world/
assets/
```

Use `theme.json` for short structural terms, `story.json` for long narrative
copy, and `prompts.json` for model-facing context. Do not hardcode theme nouns
inside core logic.

## Compatibility Rules

List any legacy protocol IDs, save keys, or public contracts that must not be
renamed casually:

```text
<compatibility-id-1>
<compatibility-id-2>
```

## Useful Commands

Installed core and theme checks:

```powershell
<python> -c "import esimu_core; print(esimu_core.__version__)"
esimu validate --root . --theme <theme-id>
esimu doctor --root . --theme <theme-id>
esimu sync --root . --theme <theme-id>
esimu dev --root . --theme <theme-id>
esimu reload --root . --theme <theme-id>
esimu build --root . --theme <theme-id>
```

Backend checks:

```powershell
<python> -m pytest <backend-tests-path>
<python> -m ruff check <backend-app-path> <backend-tests-path>
```

Frontend checks:

```powershell
cd <frontend-path>
corepack pnpm install --frozen-lockfile
corepack pnpm typecheck
corepack pnpm build
```

Docs-only checks:

```powershell
git diff --check
```

## Review Priorities

1. Does the change preserve public HTTP/WebSocket/save contracts?
2. Does reusable core code remain free of app-specific I/O?
3. Does theme data stay in theme files instead of core or adapter code?
4. Are generated files updated only through their source scripts?
5. Are unrelated dirty changes preserved?
