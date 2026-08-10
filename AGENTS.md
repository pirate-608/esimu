# AGENTS.md

This file is the handoff guide for AI agents working in Simulator Framework Lab.

## Prime Directive

Do not modify files outside this `esimu-lab` Git worktree unless the user
explicitly asks for a cross-repository change. When this repository is checked
out as `ZJUers_simulator/labs/esimu`, the parent ZJUers Simulator remains the
main game and must not receive incidental edits.

## Startup Checklist

Run these checks before changing files:

```powershell
git rev-parse --show-toplevel
git status --short
```

Confirm all three facts:

- The reported root is this `esimu-lab` repository, whether standalone or under
  `ZJUers_simulator/labs/esimu`.
- Any dirty worktree entries are understood and preserved.
- The task belongs to the lab. If it belongs to the ZJU main game, stop and ask
  for explicit cross-repository permission.

The lab may have in-progress extraction work. Do not assume the worktree is
clean; read the current diff before editing files that are already modified.

## Workspace Boundary

- Lab root: the result of `git rev-parse --show-toplevel`
- Parent/main game: outside this Git worktree; do not modify it implicitly
- Reference app: `apps/zju-reference/`
- Core package: `simulator-core/backend/`
- Theme packs: `themes/`

Code may be copied from the main game only as a deliberate step. When copying,
record the source path and commit or note the copied version.

Treat `apps/zju-reference/` as a runnable adapter and extraction baseline, not
as the final framework layout.

## Isolation Rules

- Use lab-specific Docker Compose project names, database names, Redis volumes,
  ports, and localStorage keys.
- Do not reuse ZJU production image names, domains, secrets, or deployment
  workflows.
- Do not let the lab depend on files in the ZJU working tree through relative
  imports.
- Reference backend code must import reusable rules/loaders from the local
  `esimu-core` package (`esimu_core.*`), not through temporary `sys.path`
  bridges.
- If a fix belongs in the main game, implement it in the main game separately
  after review instead of silently patching the lab copy only.

## Naming Rules

- Framework shorthand: `esimu`
- Core package name: `esimu-core`
- Python import namespace: `esimu_core`

Do not introduce old temporary framework-core names except in historical
migration notes.

## Task Routing

- Theme content, nouns, story, prompts, world JSON, and assets belong in
  `themes/<theme_id>/`.
- Reusable backend rules and loaders belong in `simulator-core/backend/esimu_core/`.
- Redis, FastAPI, WebSocket, SQLAlchemy, and save-service integration stay in
  concrete apps. Reusable model configuration, transport, generation, output
  validation, and fallback policy live in `esimu_core.ai`; app-specific model
  caches, credentials, vector retrieval, billing, and telemetry stay in adapters.
- Project-level learning, roadmap, and startup instructions belong in `docs/`.
- Reusable handoff templates belong in `templates/`.

When in doubt, push reusable pure rules downward into `esimu_core`, and keep I/O
and compatibility glue in the reference app.

## Architecture Direction

Prefer a build-time selected theme first:

```text
SIMULATOR_THEME=zju
SIMULATOR_THEME=demo-campus
```

Runtime multi-theme switching is a later experiment. It should not be introduced
before the single-theme extraction is stable.

Theme packs own `theme.json`, `story.json`, `prompts.json`, `world/`, and
`assets/`. `prompts.json` changes model-visible campus/forum/messenger context;
legacy internal IDs such as `cc98` and `dingtalk` remain compatibility IDs until
a deliberate protocol migration happens.

`esimu_core.domain` owns pure gameplay rules such as semester settlement, GPA,
effect handling, and action gates. It must not import Redis, FastAPI,
SQLAlchemy, OpenAI, or reference-app services.

`esimu_core.runtime` owns reusable runtime orchestration. Core helpers may
calculate tick timing, action decisions, payload dictionaries, runtime DTOs,
cooldown values, and background-task bookkeeping. `RuntimeSnapshot` is the
plain-data DTO between storage/schema adapters and core payload helpers.
Runtime modules must not import Redis, FastAPI, SQLAlchemy, OpenAI, or
reference-app services; adapters perform all I/O and emit returned
decisions/payloads.

`esimu_core.ai` is an optional core layer. The base package must remain usable
without OpenAI installed; construct `OpenAICompatibleTransport` only through the
`[ai]` extra or inject another `ChatTransport`. Platform credentials may use a
shared transport, while player-provided credentials must use an uncached
session transport and must never populate shared content pools.

## Current Entry Documents

- `README.md`: human-facing project overview and first links.
- `docs/quickstart.md`: local setup and validation path.
- `docs/new-project-bootstrap.md`: start a new simulator or theme from esimu.
- `docs/agent-handoff.md`: current extraction state and agent operating notes.
- `docs/architecture.md`: core/theme/adapter architecture.
- `docs/roadmap.md`: phase progress and next extraction direction.
- `docs/theme-pack-contract.md`: current theme file contract.

## Recommended Checks

Core checks from `simulator-core/backend/`:

```powershell
python -m pytest tests
python -m ruff check esimu_core scripts tests
python scripts\validate_world_data.py
$env:SIMULATOR_THEME='demo-campus'; python scripts\validate_world_data.py
```

Starter checks:

```powershell
cd apps\starter\backend
python -m pytest tests
python -m ruff check app tests
cd ..\frontend
corepack pnpm install --frozen-lockfile
corepack pnpm typecheck
corepack pnpm build
```

Release candidate and docs checks from the repository root:

```powershell
python simulator-core\backend\scripts\release_smoke.py
zensical build
```

`release_smoke.py` is mandatory before tagging. It builds the wheel, installs it
in a disposable venv, generates a standalone project, validates it through the
installed CLI, and exercises the generated Starter API. The default generated
Git dependency becomes usable only after the matching `esimu-core-v<version>`
tag is pushed.

The core `dev` extra intentionally includes FastAPI and HTTPX because the
bootstrap test starts a generated Starter application through `TestClient`.
In CI, install pnpm before enabling pnpm-aware caching; `setup-node` queries the
package manager while the action itself is initializing.

For documentation-only changes, `git diff --check` plus link/path review is
usually enough.

## Review Priorities

1. Does the change keep the ZJU main project untouched?
2. Does the lab remain isolated from ZJU ports, volumes, storage keys, and
   deployment names?
3. Does reusable code avoid app-specific I/O dependencies?
4. Does the theme pack boundary become clearer?
5. Does copied code still run with tests, or is it only documentation/scaffold?
