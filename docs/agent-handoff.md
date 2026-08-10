# Agent Handoff

This page is for future agents taking over esimu lab work.

## First Move

```powershell
cd esimu-lab
git status --short
```

Do not assume the worktree is clean. The lab frequently contains extraction
work that has not yet been committed.

If you see modified files under both `simulator-core/` and `apps/zju-reference/`,
read the diff before touching either side. The reference app is optional
compatibility evidence; ordinary framework work should still start from
`simulator-core/`, `apps/starter/`, `themes/`, and `docs/`.

## Hard Boundary

Do not modify the ZJUers Simulator product repository unless the user explicitly
requests a cross-repository change.

The ZJU main game is the primary product. This lab is allowed to copy and
experiment, but it must not silently change the main game or depend on files in
the main game working tree.

## Current Extraction State

The backend extraction is currently split like this:

- `esimu_core.world`: active theme path resolution plus loaders for balance,
  stat definitions, items, theme manifests, story data, prompt fragments, and
  the static world catalog for majors/courses/achievements/local libraries.
  `esimu_core.world.theme_contract` is the strict authoring-time validator
  invoked by `validate_world_data.py`.
- `esimu_core.domain`: pure gameplay rules for semester settlement, effects,
  stat bounds, relax overflow, and action gates.
- `esimu_core.runtime`: reusable runtime orchestration for clock math, action
  decisions, snapshot payloads, cooldown calculations, runtime DTOs, and
  background-task bookkeeping.
- `esimu_core.lifecycle`: pure setup/transition contracts for fresh-character
  state, semester reset state, and achievement detail payloads.
- `esimu_core.content`: pure event/forum/messenger payload contracts, legacy
  `cc98`/`dingtalk` concept mapping, local-library selection, reply options,
  and settlement-effect normalization.
- `esimu_core.ai`: optional OpenAI-compatible transport, model configuration,
  theme-aware event/forum/messenger/graduation generation, M2-her role messages,
  defensive output parsing, and content-mode degradation policy.
- `apps/starter`: default minimal non-ZJU app path. Its backend is a memory-only
  FastAPI adapter over `esimu-core`; its frontend is a small Vite/TypeScript
  skin generated for `demo-campus`.
- `apps/zju-reference/zjus-backend`: optional compatibility adapter code that owns Redis, FastAPI,
  SQLAlchemy, WebSocket, save services, admin pages, content pools, vector
  retrieval, and deployment/player credential policy.
- `apps/zju-reference/zjus-frontend`: copied frontend shell that consumes
  generated theme, story, and stat metadata. Browser persistence should use
  `src/utils/storageKeys.ts`, not fixed `simlab_*` keys.
- `docs/starter-app-shape.md`: Phase 4E decision record for whether a new
  project should copy the reference app or wait for the future starter.
- `docs/release-policy.md`: package versioning, tag naming, compatibility, and
  release checklist for `esimu-core`.
- `docs/framework-readiness-review.md`: Phase 9 verdict; esimu is an alpha
  library-plus-starter framework, not a stable public framework yet.
- `mkdocs.yml` plus `docs/requirements.txt`: Zensical documentation site entry
  point. The generated `site/` directory is ignored and should not be committed.
- `simulator-core/backend/scripts/new_project.py`: Phase 8 bootstrap command for
  generating a new starter project from `apps/starter` and a source theme.
- simulator-core/backend/scripts/release_smoke.py: mandatory pre-tag gate that
  builds and installs a wheel in a disposable generated project.
- `simulator-core/backend/scripts/scaffold_world_data.py`: small snippet helper
  for items, achievements, courses, events, and prompt fragments.

Core modules must not import Redis, FastAPI, SQLAlchemy, WebSocket objects, or
reference-app services. `esimu_core.ai.transport` is the deliberate exception
for the optional OpenAI SDK extra; importing the base package must not require
that extra.

## Where To Put Work

- Add or tune world content in `themes/<theme_id>/world/`.
- Add display terms, storage prefixes, and theme assets in `theme.json`.
- Add long narrative copy in `story.json`.
- Add model-facing prompt context in `prompts.json`.
- Add reusable static-world file shape compatibility in
  `simulator-core/backend/esimu_core/world/catalog.py`.
- Add theme authoring validation in
  `simulator-core/backend/esimu_core/world/theme_contract.py`.
- Add pure stat/effect/semester/rules code in `simulator-core/backend/esimu_core/domain/`.
- Add pure tick/action/snapshot/task orchestration in `simulator-core/backend/esimu_core/runtime/`.
- Add pure character setup, semester transition, and achievement detail
  contracts in `simulator-core/backend/esimu_core/lifecycle/`.
- Add pure event/forum/messenger contracts in
  `simulator-core/backend/esimu_core/content/`.
- Add reusable model configuration, prompt assembly, transports, parsing, and
  fallback policy in `simulator-core/backend/esimu_core/ai/`; keep caches,
  credentials, embeddings, billing, and WebSocket effects in app adapters.
- Add starter-shape decisions and reference-app file classification in
  `docs/starter-app-shape.md`.
- Add minimal starter backend/frontend code in `apps/starter/`; keep it smaller
  than `apps/zju-reference/` and avoid Redis/PostgreSQL unless Phase 6+ asks
  for optional persistence adapters.
- Add package metadata, CI, changelog, and release-process changes in
  `simulator-core/backend/pyproject.toml`, `.github/workflows/`, `CHANGELOG.md`,
  and `docs/release-policy.md`.
- Add new-project bootstrap or world-data scaffold helpers in
  `simulator-core/backend/scripts/`, with smoke tests under
  `simulator-core/backend/tests/`.
- Add documentation-site navigation or styling in `mkdocs.yml`,
  `docs/index.md`, or `docs/assets/`; build with Zensical before handoff.
- Keep external I/O and compatibility glue in the concrete app adapter. For new
  projects that means `apps/starter/` or a generated app; use
  `apps/zju-reference/` only for legacy-rich compatibility checks.
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
python -m pytest tests
python -m pytest tests\test_world_catalog.py
python -m pytest tests\test_demo_theme_smoke.py
python -m pytest tests\test_lifecycle_contracts.py
python -m pytest tests\test_content_contracts.py
python -m pytest tests\test_theme_contract.py
python -m pytest tests\test_package_metadata.py
python -m pytest tests\test_project_bootstrap.py
python -m ruff check esimu_core scripts tests
python scripts\validate_world_data.py
$env:SIMULATOR_THEME='demo-campus'; python scripts\validate_world_data.py
```

Starter backend from `apps/starter/backend/`:

```powershell
python -m pytest tests
python -m ruff check app tests
```

Optional reference backend from `apps/zju-reference/zjus-backend/`:

```powershell
python -m pytest tests\unit\test_demo_campus_reference_smoke.py
python -m pytest tests\unit
python -m ruff check app tests\unit
```

Optional reference frontend from `apps/zju-reference/zjus-frontend/`:

```powershell
npx vitest run src\utils\theme.spec.ts
npx vitest run src\components\themeRuntime.spec.js
npx vue-tsc --noEmit
npx vitest run
npx vite build
```

For docs-only changes, prefer:

```powershell
git diff --check
zensical build
```

Then manually confirm all linked `docs/*.md` paths exist.

## New Project Hand-off

When creating a new simulator project from this lab:

1. Start from `docs/new-project-bootstrap.md`.
2. Read `docs/starter-app-shape.md` before copying `apps/zju-reference/`.
3. Prefer `apps/starter/` for new games unless the project needs the full ZJU
   reference adapter immediately.
4. Prefer `scripts/new_project.py` to copy the starter, theme pack, generated
   metadata, and a filled `AGENTS.md`.
5. Fill in project-specific roots, commands, theme IDs, and deployment limits.
6. Keep esimu package names exact: package `esimu-core`, import namespace
   `esimu_core`.
