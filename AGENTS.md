# AGENTS.md

This file is the handoff guide for the independent esimu framework repository.

## Prime Directive

esimu and ZJUers Simulator are separate products. Do not modify the ZJU game
while working here, and do not introduce parent-workspace paths or runtime
dependencies. The historical extraction is preserved by `esimu-lab-final`.

## Current Beta State

- Package: `packages/esimu-core`, distribution `esimu-core`, import
  `esimu_core`, current version `0.2.0b1`.
- Starter: `apps/starter`, FastAPI/WebSocket backend plus Vue 3/Pinia frontend.
- Default theme: `themes/demo-campus`.
- Persistence: SQLite by default, memory for tests, JSON file as a temporary
  Beta compatibility adapter.
- Contracts: theme schema, state schema, and WebSocket protocol are version 1.
- Docs: Zensical under `docs/`, published at `https://esimu.67656.fun/`.

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
`ESIMU_FRONTEND_*_OUTPUT`. Old `SIMULATOR_*` names are read only for the 0.2
Beta compatibility window and must not appear in new docs or generated files.

Public CLI:

```powershell
esimu new <target>
esimu validate --root . --theme <theme-id>
esimu version
```

`esimu-validate-world` remains a temporary compatibility alias.

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
- Run the external `esimu-beta-example` trial before publishing `0.2.0b1`.

Preserve unrelated dirty files. Do not reset or delete work that you did not
create. Update this file and relevant bilingual docs when contracts, layout,
commands, or release behavior change.
