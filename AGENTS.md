# AGENTS.md

This file is the handoff guide for the independent esimu framework repository.

## Prime Directive

esimu and ZJUers Simulator are separate products. Do not modify the ZJU game
while working here, and do not introduce parent-workspace paths or runtime
dependencies. The historical extraction is preserved by `esimu-lab-final`.

## Current Beta State

- Package: `packages/esimu-core`, distribution `esimu-core`, import
  `esimu_core`, current released Beta `0.4.0b2`.
- Starter: `apps/starter`, FastAPI/WebSocket backend plus Vue 3/Pinia frontend.
- Default theme: `themes/zju-simplified`; `themes/demo-campus` remains the
  neutral scaffold alternative.
- Persistence: SQLite by default, memory for tests, JSON file as a temporary
  Beta compatibility adapter.
- Contracts: theme schema is version 1; state and WebSocket protocol are version 2.
  State v1 is migrated on load and protocol-v1 clients remain accepted.
- Docs: Zensical 0.0.57 under `docs/`, published at
  `https://esimu.67656.fun/`.

## Architecture Boundaries

- Pure loaders, validation, rules, runtime DTOs, lifecycle helpers, content
  normalization, optional AI transport, and scaffold CLI belong in
  `packages/esimu-core/esimu_core`.
- FastAPI, SQLite, WebSocket lifecycle, credentials, and UI integration belong
  in `apps/starter` or downstream applications.
- User-visible nouns, story, prompts, stats, items, courses, events, characters,
  achievements, and assets belong in `themes/<theme_id>`.
- Core must not import FastAPI, Redis, SQLAlchemy, application stores, or Vue.
- Starter public actions use neutral `forum` and `messenger` IDs.

## Environment And CLI

Use `ESIMU_PROJECT_ROOT`, `ESIMU_THEME`, `ESIMU_WORLD_DIR`, and
`ESIMU_FRONTEND_*_OUTPUT`. Old `SIMULATOR_*` names remain read-only compatibility
inputs through the 0.4 Beta and must not appear in new docs or generated files.

Public CLI:

```powershell
esimu new <target>
esimu validate --root . --theme <theme-id>
esimu doctor --root . --theme <theme-id>
esimu inspect --root . --theme <theme-id>
esimu sync --root . --theme <theme-id>
esimu add <stat|item|achievement|event|course|prompt> <id> --root . --theme <theme-id>
esimu dev --root . --theme <theme-id>
esimu reload --root . --theme <theme-id>
esimu build --root . --theme <theme-id>
esimu version
```

`esimu-validate-world` remains a temporary compatibility alias.

## Runtime Contracts

- Relax cooldowns, action counts, achievements, content mode, ending state, and
  complete messenger contacts persist in state v2.
- Achievement conditions are theme-owned `all`/`any` predicates over
  `stat/action/session`; never evaluate arbitrary expression strings.
- Automatic event/messenger work uses balance intervals/probabilities and must
  stop while paused, settling, or ended.
- Player messenger replies are saved/emitted before AI work. Model calls run
  outside the session lock through per-target deduplicated tasks.
- `save_and_exit` sends `save_result`, then `exit_confirmed`, then closes with
  code 1000. Do not reorder this lifecycle.
- `esimu add` and `sync` are check/preview-only without `--write`; writes are
  atomic and validation failures must restore source and generated files.
- `esimu dev` supervises backend/frontend children in the foreground;
  `reload` synchronizes and validates the active theme before requesting a full
  restart, and `build` writes metadata before creating the frontend bundle.

## Required Checks

```powershell
python -m pytest packages\esimu-core\tests
python -m pytest apps\starter\backend\tests
python -m ruff check packages\esimu-core\esimu_core packages\esimu-core\scripts packages\esimu-core\tests apps\starter\backend\app apps\starter\backend\tests
python packages\esimu-core\scripts\validate_world_data.py
python packages\esimu-core\scripts\sync_scaffold_bundle.py
python packages\esimu-core\scripts\release_smoke.py
zensical build
```

Frontend checks from `apps/starter/frontend`:

```powershell
corepack pnpm install --frozen-lockfile
corepack pnpm typecheck
corepack pnpm test
corepack pnpm build
```

Before release, verify a wheel-only installation can run `esimu new`, validate
the generated theme, start the Starter, persist/reload SQLite state, and finish
both demo semesters without an esimu source checkout.

## Release Rules

- Version source: `packages/esimu-core/esimu_core/__init__.py`.
- Tag: `esimu-core-v<version>`.
- TestPyPI uses `.github/workflows/release-candidate.yml`.
- PyPI and GitHub prerelease use `.github/workflows/release.yml` with trusted
  publishing; never add a long-lived PyPI token.
- Run an external generated-project trial before every release; `0.3.0b2` was
  validated in `pirate-608/esimu-beta-example` before publication, as was
  `0.4.0b2`.

Preserve unrelated dirty files. Do not reset or delete work that you did not
create. Update this file and relevant bilingual docs when contracts, layout,
commands, or release behavior change.
