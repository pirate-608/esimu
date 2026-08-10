# Roadmap

For setup and handoff, start with `quickstart.md` and `agent-handoff.md`. For
new simulator projects, use `new-project-bootstrap.md`.

## Phase 0: Lab Bootstrap

- Create this isolated workspace.
- Define theme pack boundaries.
- Keep all work separate from the ZJU main game.

## Phase 1: Reference Copy

- Copy selected backend modules and frontend components from ZJUers Simulator
  into `simulator-core/`.
- Rename deployment identifiers, ports, volumes, and storage keys.
- Get one local build running with the ZJU reference theme.

## Phase 2: Theme Manifest

- Add a loader for `themes/<theme_id>/theme.json`.
- Replace hardcoded UI terms with theme terms.
- Bind frontend generated metadata to the selected theme.

Progress:

- Core world-data loaders now resolve `game_balance.json`, `items.json`, and
  `stat_definitions.json` through the active theme world directory.
- The copied ZJU world data is available under `themes/zju/world/`.
- Core validation and stat metadata scripts operate on the active theme.
- `theme.json` is validated by a core loader and generated into the reference
  frontend as `theme.generated.ts`.
- `story.json` is validated by a core loader and generated into the reference
  frontend as `story.generated.ts`.
- `prompts.json` is validated by a core loader and used by backend content
  generation to replace theme-visible ZJU/CC98/DingTalk prompt context.
- First-pass frontend shell terms now come from `themeTerm()`; remaining ZJU
  text is mostly world data, docs links, and test fixtures.

## Phase 3: ZJU As First Theme

- Move copied world data under `themes/zju/world/`.
- Preserve behavior while proving the theme boundary.
- Document every intentional divergence from the main game.

Progress:

- The first pure gameplay rules have moved into
  `simulator-core/backend/esimu_core/domain/`.
- The core package is named `esimu-core`; imports use `esimu_core.*`.
- `semester.py` covers deterministic course settlement, term GPA, cumulative
  GPA, legacy GPA fallback, and period recovery.
- `effects.py` covers bounded stat deltas, feedback changes, and relax overflow
  transfer.
- `actions.py` covers pause/runtime action gating without depending on
  WebSocket or Redis.
- These rules are tested independently from Redis/FastAPI so the future engine
  can become an adapter over framework logic instead of a copied monolith.
- The ZJU reference engine now calls the pure semester rules for exam/GPA and
  new-period recovery, the pure effects rules for relax overflow, and the pure
  actions rules for paused-state mutation gates through the installed
  `esimu-core` package.
- Runtime orchestration has started moving into `esimu_core.runtime`: tick
  timing, adapter-facing action decisions, `tick/init` payload assembly, and
  target-level background task tracking.
- Runtime state boundaries are now explicit: the reference adapter converts
  Redis/Pydantic data into `RuntimeSnapshot`, and core helpers compute
  cooldowns plus `tick`, `init`, and `new_semester` payloads from plain data.

## Phase 4: Demo Campus

- Build a tiny second theme with minimal courses, events, items, achievements,
  and characters.
- Use it to catch hidden ZJU assumptions.

Progress:

- `themes/demo-campus/world/` now contains a minimal valid world pack for
  loader and validation checks.
- `themes/demo-campus/prompts.json` validates the content-generation prompt
  boundary without carrying ZJU visible terms.
- `validate_world_data.py` can validate this theme with
  `SIMULATOR_THEME=demo-campus` without overwriting the ZJU reference frontend
  generated metadata.
- `test_demo_theme_smoke.py` starts a fresh Python process with
  `SIMULATOR_THEME=demo-campus` and verifies theme, story, prompts, world data,
  items, and runtime `init/tick` payload assembly do not fall back to ZJU data.
- `esimu_core.world.catalog` now owns majors, course plans, achievements,
  event libraries, and forum-library path resolution for active themes.
- The ZJU reference backend `WorldService`, achievement loading, and local
  event/forum library reads now use the catalog instead of hardcoded `/app/world`
  or copied-repo world paths.
- The reference frontend has a focused theme-helper test proving visible labels
  and storage keys come from generated theme metadata rather than hardcoded ZJU
  copy.
- Runtime browser storage in the reference frontend now goes through
  `storageKeys.ts`, so login tokens, save selection, guide state, prologue state,
  and console-theme preferences are scoped by the active theme prefix.
- `esimu_core.content` now maps legacy `cc98`/`dingtalk` IDs to framework
  `forum`/`messenger` concepts and owns local event/forum/message payload
  normalization for both ZJU and demo-campus validation paths.

## Framework Completion Roadmap

The remaining roadmap turns esimu from a research lab into a basically complete
single-theme simulator framework. "Basically complete" means a new project can
start from esimu, define a theme/world pack, run the starter backend/frontend,
and customize gameplay content without copying ZJU-specific product code.

Each phase should still become a smaller implementation plan before coding
starts. The ZJU main game remains the primary product and should not be changed
as part of this roadmap unless explicitly requested.

### Phase 4A: Demo Campus Runnable Reference

Goal: prove `SIMULATOR_THEME=demo-campus` can drive the reference app beyond
loader smoke.

Progress:

- `test_demo_campus_reference_smoke.py` starts a fresh reference-backend process
  with `SIMULATOR_THEME=demo-campus`, then verifies `/api/majors`, character
  initialization, WebSocket-equivalent `init` and `tick` payloads, local event
  and forum library reads, item catalog payloads, and achievement details.

Remaining work:

- Run the reference backend with demo theme and verify `/api/majors`, character
  initialization, WebSocket `init`, one `tick`, one local event, one local forum
  post, item catalog payload, and achievement detail loading against an actual
  local server when the app runner/Compose shape is ready.
- Fix only blocking ZJU assumptions found in this path; keep `cc98` and
  `dingtalk` as legacy internal IDs.
- Document any demo-campus fields that are still placeholders rather than full
  game content.

### Phase 4B: Frontend Theme Runtime Boundary

Goal: make the copied frontend more clearly theme-driven while keeping it a
reference skin, not a framework package yet.

- Audit visible ZJU nouns in `apps/zju-reference/zjus-frontend/src` and replace
  runtime copy with generated theme/story/stat metadata where safe.
- Keep generated metadata as the build/startup-time theme boundary; do not add
  runtime multi-theme switching.
- Add focused tests for entrance copy, prologue copy, end-screen copy, storage
  keys, and major/item labels under a mocked demo theme.
- Record any remaining ZJU terms as world data, legacy protocol IDs, or test
  fixtures.

Progress:

- Loading, course, item, transcript, save/exit, WebSocket status, and first-play
  guide copy now use theme terms where safe.
- `themeRuntime.spec.js` mocks `demo-campus` metadata and verifies App startup,
  loading copy, course labels, item labels, and theme-scoped storage behavior.
- Remaining runtime `simlab_*` browser keys were replaced by
  `src/utils/storageKeys.ts`; fixed storage keys should now be limited to test
  fixtures or explicit legacy assertions.

### Phase 4C: Core Lifecycle Contracts

Goal: define the reusable contracts before moving more engine code.

- Introduce plain core DTOs for player identity, initial character assignment,
  semester transition result, achievement details, and content-library result.
- Move non-I/O normalization logic from reference services into `esimu-core`
  where it can be tested against both ZJU and demo-campus themes.
- Keep Redis, PostgreSQL, FastAPI, WebSocket, and LLM clients in the reference
  adapter.
- Avoid moving the full `GameEngine` until these contracts have stable tests.

Deliverables:

- `esimu_core.lifecycle` or equivalent module containing plain DTOs and helpers
  for player identity, initial stats, major assignment, semester transition,
  achievements, and content result normalization.
- Reference backend adapters that call these helpers instead of duplicating
  normalization and payload shaping.
- Tests that run the same lifecycle helpers against `zju` and `demo-campus`
  world data.

Completion criteria:

- Character initialization, semester transition, achievement detail lookup, and
  local content result shaping can be tested without Redis, SQLAlchemy, FastAPI,
  WebSocket, or OpenAI clients.
- The reference backend still exposes the same player HTTP/WebSocket contracts.

Do not:

- Move database persistence or WebSocket connection management into core.
- Rename legacy protocol/action IDs during this phase.

Progress:

- `esimu_core.lifecycle` now provides pure helpers for fresh-character state,
  new-semester reset state, achievement detail payloads, and local event/forum
  result normalization.
- The ZJU reference `GameService` calls lifecycle helpers for character
  initialization and semester course reset while keeping Redis and PostgreSQL
  persistence in the adapter.
- The ZJU reference engine uses lifecycle achievement-detail normalization.
- `test_lifecycle_contracts.py` covers these helpers with demo-campus world
  data and compatibility-style fallback cases.

Remaining work:

- Extract player identity DTOs and auth/session-facing normalization.
- Move achievement condition evaluation into core once behavior thresholds are
  represented as data instead of reference-engine branches.
- Extract player identity DTOs and auth/session-facing normalization.
- Move achievement condition evaluation into core once behavior thresholds are
  represented as data instead of reference-engine branches.

### Phase 4D: Content And Message Contracts

Goal: make events, forum posts, and messenger conversations theme-neutral at the
contract layer while keeping legacy IDs compatible.

- Define core result shapes for local event entries, forum posts, message
  contacts, message rounds, reply options, and stat/gold effects.
- Add a terminology mapper so `forum` and `messenger` are the framework-facing
  concepts, while `cc98` and `dingtalk` remain legacy adapter IDs for the ZJU
  reference app.
- Move local-library selection and fallback result normalization into core where
  it can be tested against both themes.
- Keep actual LLM calls, Redis content pools, and WebSocket emission in the
  reference adapter.

Deliverables:

- Core contracts for event/feed/forum/messenger payloads.
- Reference adapter mapping from legacy `cc98`/`dingtalk` actions to
  framework-level `forum`/`messenger` concepts.
- Demo-campus smoke that triggers at least one local event, one forum entry, one
  messenger contact, and one reply option without ZJU-visible terms.

Completion criteria:

- Adding a non-ZJU theme no longer requires accepting `CC98` or DingTalk as
  visible labels.
- Existing ZJU save/WebSocket compatibility remains intact.

Progress:

- `esimu_core.content` now defines framework-facing `feed`/`forum`/`messenger`
  concepts plus compatibility mapping for legacy reference IDs `cc98` and
  `dingtalk`.
- Local random-event and forum-post selection now lives in core; the reference
  `event_library.py` keeps active-theme JSON caching and delegates selection
  plus fallback normalization to core.
- Messenger opening payloads, contact IDs, reply options, replyable-role
  aliases, and settlement-effect clamping now have pure core helpers while the
  reference adapter keeps DingTalk-compatible Pydantic save/WebSocket schemas.
- `test_content_contracts.py` covers concept mapping, local event/forum
  selection, message payload normalization, reply fallbacks, and effect clamps.
- The demo-campus smoke now triggers one local event, one local forum post, and
  one messenger payload without ZJU-visible terms.

Remaining work:

- Define a fuller message-round state contract before moving persisted
  DingTalk-compatible inbox state out of the reference schema layer.
- Move reusable contact selection/compaction into core once the message state
  DTO is stable.
- Keep LLM calls, Redis content pools, and WebSocket emissions in the adapter
  until the starter app shape is decided.

### Phase 4E: Starter App Shape

Goal: decide what a new simulator project should copy.

- Compare two starter shapes: reference-app fork versus minimal starter app that
  depends on `esimu-core`.
- Identify which files from `apps/zju-reference` are adapter boilerplate,
  ZJU-specific product code, or candidates for future frontend/core extraction.
- Expand `templates/` only after the copy boundary is clear.
- Produce a concrete recommendation before Phase 5.

Deliverables:

- A written decision record in `docs/` explaining the chosen starter strategy.
- A file classification list for `apps/zju-reference`: keep as adapter, copy to
  starter, move into core, or leave as ZJU-specific reference.
- A minimal `templates/agent/AGENTS.md` plus starter checklist that matches the
  chosen strategy.

Completion criteria:

- A future project maintainer can tell which directories to copy and which are
  reference-only.
- The starter strategy does not require editing the ZJU reference theme.

Progress:

- `docs/starter-app-shape.md` now records the Phase 4E decision: use
  `apps/zju-reference/` as a short-term runnable adapter when necessary, but do
  not treat it as the long-term starter template.
- The reference app has file-area classification guidance covering backend API,
  engine, services, repositories, schemas, content adapters, frontend skin,
  generated metadata, docs, deployment, and agent workflows.
- `docs/new-project-bootstrap.md`, `docs/agent-handoff.md`, and `README.md`
  now point maintainers to the starter-shape decision before they copy
  reference-app files.

Remaining work:

- Phase 5 should harden theme schemas before any clean starter is generated.
- Phase 6 should introduce `apps/starter/` as the preferred new-project base.
- Advanced reference features should be copied into future projects only after
  the starter exposes the minimal full game loop.

### Phase 5: Theme Contract Hardening

Goal: turn the current theme pack convention into a stable framework contract.

- Write JSON Schema or schema-equivalent validators for `theme.json`,
  `story.json`, `prompts.json`, and major world files.
- Make `validate_world_data.py` the canonical CI gate for new themes.
- Document field semantics, defaults, compatibility guarantees, and common
  migration patterns.
- Add fixtures for both `zju` and `demo-campus` so schema changes are tested
  against a full theme and a minimal theme.

Deliverables:

- Machine-checkable theme schemas or Pydantic models with clear error messages.
- `docs/theme-pack-contract.md` updated from descriptive notes into a real
  authoring contract.
- A "new theme checklist" that includes metadata generation, validation, smoke
  tests, and known legacy-ID caveats.

Completion criteria:

- A malformed theme fails validation before runtime.
- A minimal valid theme can be created without reading ZJU-specific source code.

Progress:

- `esimu_core.world.theme_contract` now provides schema-equivalent theme pack
  validation for required files plus majors, courses, achievements, event
  libraries, forum libraries, characters, items, balance, and graduation
  comments.
- `scripts/validate_world_data.py` calls the theme contract validator, making
  it the default CI/local gate for active-theme world data.
- `docs/theme-pack-contract.md` has been rewritten as an authoring contract
  with file requirements, field semantics, validation commands, and a new-theme
  checklist.
- `test_theme_contract.py` verifies that both `zju` and `demo-campus` satisfy
  the contract and that malformed themes fail before runtime.

Remaining work:

- Decide whether to emit standalone JSON Schema files in addition to the
  Python/Pydantic validation layer.
- Extend validation for optional theme assets, legal links, and future starter
  frontend route metadata when those contracts become stable.

### Phase 6: Minimal Starter App

Goal: create the first non-ZJU starter app that depends on `esimu-core`.

- Add `apps/starter/` or equivalent minimal backend/frontend pair.
- Use `demo-campus` as the default starter theme.
- Keep starter backend as an adapter: FastAPI/WebSocket/Redis/Postgres may live
  there, but game rules and world loading should come from `esimu-core`.
- Keep starter frontend as a skin/template, not a heavy frontend framework
  package yet.

Deliverables:

- A runnable starter backend with basic auth placeholder, character creation,
  WebSocket init/tick, one relax action, one event, one forum entry, one
  messenger round, one item buy/sell path, semester settlement, and end screen.
- A minimal starter frontend that consumes generated theme/story/stat metadata.
- Local run instructions and smoke tests for the starter app.

Completion criteria:

- A new simulator can be bootstrapped from `apps/starter` without importing or
  editing `apps/zju-reference`.
- ZJU reference behavior still passes its existing tests.

Progress:

- `apps/starter/backend` now provides a minimal FastAPI adapter using
  `demo-campus` by default and keeping session state in memory.
- The starter backend calls `esimu-core` lifecycle, runtime, content, effects,
  items, catalog, and semester helpers for character setup, init/tick payloads,
  relax effects, event/forum/messenger payloads, item buy/sell, and final exam
  settlement.
- `apps/starter/frontend` now provides a tiny Vite/TypeScript skin that
  consumes generated theme, story, and stat metadata and talks to the starter
  backend over HTTP/WebSocket.
- `apps/starter/backend/tests/test_starter_smoke.py` verifies the minimal loop
  through direct session calls, HTTP routes, and WebSocket actions.

Remaining work:

- Decide whether the starter should gain optional Redis/PostgreSQL adapters or
  remain memory-only while downstream projects add persistence themselves.
- Add frontend build/typecheck coverage once starter frontend dependencies are
  installed in CI/local workflow.
- Expand starter docs with a copy-and-rename checklist after the first external
  simulator project uses it.

### Phase 7: Packaging And Versioning

Goal: make `esimu-core` consumable as a real dependency instead of a lab-only
editable package.

- Finalize Python package metadata, extras, and supported Python versions.
- Add changelog/version policy for `esimu-core`.
- Decide whether releases are Git tags only, GitHub packages, or a future PyPI
  package.
- Add CI checks for core tests, starter smoke, demo theme validation, and
  optional reference adapter compatibility.

Deliverables:

- Versioned `esimu-core` package.
- Release checklist and compatibility policy.
- CI matrix covering required `esimu-core` and `apps/starter` checks, plus
  optional `apps/zju-reference` compatibility checks.

Completion criteria:

- A downstream project can pin an esimu-core version and upgrade intentionally.
- Breaking changes to theme/world contracts are documented and tested.

Progress:

- `esimu-core` now exposes `esimu_core.__version__` as the runtime version
  source, and `pyproject.toml` reads it dynamically through setuptools.
- Package metadata now declares README, license, Python version classifiers,
  project URLs, typed package data, and a small `dev` extra.
- `CHANGELOG.md` records the initial `0.1.0` baseline and Semantic Versioning
  expectations.
- `docs/release-policy.md` defines Git tags as the current release channel,
  tag naming, compatibility policy, and a release checklist.
- Root CI now covers core tests/lint, default and demo theme validation,
  starter backend smoke/lint, docs build, and optional focused ZJU reference
  backend compatibility.
- `test_package_metadata.py` verifies import-time and installed package
  metadata versions stay in sync.

Remaining work:

- Decide after Phase 9 whether to publish to PyPI, GitHub Packages, or keep
  Git tags as the only release channel.
- Add frontend starter build/typecheck to CI once dependencies and lockfile
  strategy are finalized.

### Phase 8: Project Bootstrap Tooling

Goal: reduce the cost of creating a new simulator from the framework.

- Add a small bootstrap script or CLI after the starter app shape is stable.
- Generate a new project skeleton with selected theme ID, storage prefix,
  package names, docs, and agent handoff files.
- Provide scaffold helpers for stats, items, achievements, courses, events, and
  prompt fragments.
- Keep the CLI small; prefer validation and generated checklists over magical
  source rewrites.

Deliverables:

- `scripts/new_project.py` or equivalent command.
- Theme/world scaffolding commands or documented templates.
- Bootstrap smoke that creates a temporary project and runs validation.

Completion criteria:

- A new project can be generated, validated, and started locally in a predictable
  workflow.
- The generated project contains no ZJU product names unless the user selects
  the ZJU theme.

Progress:

- `scripts/new_project.py` now generates a starter project from
  `apps/starter/` plus a source theme, rewrites the theme ID, storage prefix,
  institution/forum/messenger terms, generated frontend metadata, starter
  backend default theme, frontend package name, README, `.env.example`, and
  project `AGENTS.md`.
- Generated projects copy story image assets into the theme asset directory when
  the source lab has matching images, so standalone validation does not depend
  on `apps/zju-reference`.
- `scripts/scaffold_world_data.py` drafts or appends reviewable item,
  achievement, event, course, and prompt fragments. It complements
  `scaffold_game_stat.py` for stat definitions.
- `test_project_bootstrap.py` creates a temporary project, validates it through
  the existing world-data validator using `SIMULATOR_LAB_ROOT`, and checks the
  world-data scaffolding output.
- `new-project-bootstrap.md`, `quickstart.md`, `agent-handoff.md`, and the core
  README now document the bootstrap workflow.

Remaining work:

- Decide whether `new_project.py` should become an installed console script
  after the release channel moves beyond Git tags.
- Add frontend starter build/typecheck coverage for generated projects once the
  dependency/lockfile strategy is finalized.
- Consider richer project templates only after the first external simulator
  uses the minimal starter and reports what was missing.

### Phase 9: Framework Readiness Review

Goal: decide whether esimu is ready to be treated as a basically complete
framework.

- Run a full audit across core, starter, reference adapter, docs, and theme
  contracts.
- Build a second small non-ZJU theme beyond demo-campus, or expand demo-campus
  enough to prove the framework supports real content authoring.
- Review performance boundaries: tick loop, content generation, storage I/O,
  LLM timeouts, and background task de-duplication.
- Review UX boundaries: onboarding, save/load, theme terms, prologue/endings,
  item and achievement feedback.

Deliverables:

- Framework readiness report.
- Remaining-blockers list, if any.
- Recommendation for one of:
  - internal reusable framework,
  - library plus starter app,
  - template repository,
  - research lab only.

Completion criteria:

- A new simulator can be created without copying ZJU-specific code.
- A theme author can add world data and assets through documented contracts.
- Core behavior is covered by tests independent of FastAPI/Redis/Postgres.
- The starter app can run a minimal full game loop.
- ZJU reference behavior remains protected by tests and can cherry-pick mature
  framework improvements intentionally.

Progress:

- `docs/framework-readiness-review.md` records the Phase 9 verdict: esimu is
  ready as a basically complete alpha framework for single-theme simulator
  prototypes.
- The recommended shape is `esimu-core + starter app + theme pack`.
- Validation evidence includes core tests, theme validation for `zju` and
  `demo-campus`, starter backend smoke, reference backend smoke/game-state
  tests, ruff checks, and hardcoded-name scanning.
- The review recommends keeping Git tags as the release channel for now and
  deferring PyPI/GitHub Packages until external starter-project feedback,
  starter frontend dependency policy, and at least one version upgrade path are
  proven.
- Remaining gaps are explicitly tracked: optional persistence adapters, starter
  frontend build/typecheck CI, legacy `cc98`/`dingtalk` protocol IDs, and a real
  second non-ZJU simulator beyond the minimal `demo-campus` theme.

## Framework Decision

Phase 9 chooses **library plus starter app**.

esimu should continue as:

- `esimu-core`: versioned Python package for reusable rules, loaders,
  validation, runtime helpers, lifecycle contracts, and content contracts.
- `apps/starter`: minimal app shell for new single-theme simulator prototypes.
- `themes/<theme_id>`: project-owned theme/world/story/prompt data.
- `apps/zju-reference`: compatibility-rich reference adapter and regression
  target, not the default project template.

It should not yet be published as a stable public framework. The current
release channel remains Git tags.

Supporting handoff work now lives in:

- `quickstart.md`: local setup and validation path.
- `new-project-bootstrap.md`: new theme/app startup checklist.
- `agent-handoff.md`: current extraction state for future agents.
- `theme-pack-contract.md`: active theme pack contract.
- `framework-readiness-review.md`: Phase 9 verdict and residual gaps.

## Independence Roadmap

The next roadmap turns esimu from a lab nested under the ZJU main repository
into an independent framework repository.

There are two different finish lines:

- **Repository independence**: `pirate-608/esimu-lab` can be cloned, tested,
  documented, and released without the ZJU parent workspace.
- **Framework formality**: esimu is polished enough to present as a real alpha
  framework project, with clear starter guarantees, versioned docs, CI, and a
  migration path for downstream simulators.

Repository independence should be achievable in Phase 10-11. Framework
formality needs Phase 12-14.

### Phase 10: Remove Parent-Workspace Assumptions

Goal: make a fresh clone of `pirate-608/esimu-lab` work without the ZJU mother
repository.

Status: complete for the core/starter/docs path. Reference-app compatibility
work remains optional and continues in Phase 11.

Key work:

- Replace hardcoded parent-workspace commands in README, docs, generated
  checklist examples, and tests with repository-relative commands.
- Add a root-level `.python-version` or documented Python version matrix, plus
  a bootstrap command that creates/uses a local `.venv` inside the esimu repo.
- Update `docs/quickstart.md` so the first path is:

```powershell
git clone https://github.com/pirate-608/esimu-lab.git
cd esimu-lab
```

- Ensure `docs/requirements.txt`, starter backend requirements, and core dev
  extras are enough to install everything in a clean clone.
- Stop relying on parent repo images for story validation. Theme assets required
  by `zju` and `demo-campus` must live under `themes/<theme_id>/assets/`, or
  validation must clearly mark reference-only assets as optional.
- Update tests that assume the lab lives inside the ZJU parent repository.

Deliverables:

- Clean-clone quickstart.
- Root bootstrap instructions for Python, docs, core checks, starter checks,
  and theme validation.
- No required command in docs points at the ZJU parent venv or parent path.

Completion criteria:

- In a directory outside the ZJU repo, a fresh clone can run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest simulator-core\backend\tests
.\.venv\Scripts\python.exe simulator-core\backend\scripts\validate_world_data.py
.\.venv\Scripts\zensical.exe build
```

Progress:

- Root `requirements-dev.txt` now gives a clean-clone dependency entry point.
- Quickstart and README now start from `git clone`, a local `.venv`, and
  repository-relative commands.
- Story image validation now requires theme-owned assets rather than falling
  back to the ZJU reference frontend public image directory.
- The `zju` and `demo-campus` themes now carry the story images they reference.
- `new_project.py` validates that copied source themes already contain required
  story assets instead of borrowing files from the reference frontend.

### Phase 11: Split Reference App From Framework Core

Goal: prevent the copied ZJU reference app from being perceived as required for
the framework.

Key work:

- Decide whether `apps/zju-reference/` remains in the independent repo as a
  compatibility fixture, moves to a separate archival branch, or becomes an
  optional test fixture downloaded only in CI.
- If it stays, mark it clearly as `reference-only` and remove it from the
  default quickstart path.
- Make `apps/starter/` the only app path required by docs and CI defaults.
- Move ZJU-heavy docs to an appendix or archival section.
- Make hardcoded-name scans part of CI for `esimu_core`, `apps/starter`, and
  docs landing pages.

Deliverables:

- Default docs and homepage explain esimu without needing the ZJU reference app.
- CI has separate jobs: required core/starter/docs jobs, optional reference
  compatibility job.
- New-project generation no longer mentions ZJU paths or reference app unless
  advanced docs are opened.

Completion criteria:

- A new maintainer can understand and run esimu without reading any ZJU
  reference source.
- Removing or ignoring `apps/zju-reference/` does not break core, starter,
  docs, theme validation, or bootstrap tooling.

Progress:

- `apps/starter/` is now documented as the default app path in README,
  quickstart, handoff notes, and release checks.
- The default CI path runs required core, starter, and docs jobs. The
  ZJU reference backend job is manual-only through `workflow_dispatch` with
  `run-reference=true`.
- CI includes a guard that rejects ZJU-specific visible names in `apps/starter`
  and the docs landing pages.
- Reference checks moved to a maintainer appendix:
  `docs/reference-compatibility.md`.

### Phase 12: Starter App Hardening

Goal: make starter strong enough for real downstream prototypes.

Key work:

- Add starter frontend dependency lock strategy and CI build/typecheck.
- Provide optional persistence adapters:
  - memory-only default,
  - file-based/dev persistence,
  - optional Redis/PostgreSQL example if still useful.
- Expand starter smoke to cover a full browser-like flow: auth, character
  creation, init/tick, event, forum, messenger, item buy/sell, exam, ending.
- Add neutral public IDs for forum/messenger while preserving compatibility
  mappers for legacy `cc98`/`dingtalk` in reference-only code.
- Improve generated project checklist and starter README from actual usage.

Deliverables:

- Starter backend/frontend CI.
- Optional persistence module or documented persistence extension point.
- Realistic starter smoke tests.
- Public starter contract document.

Completion criteria:

- A downstream project can keep starter as its app base for more than a toy
  prototype without immediately copying ZJU reference code.

Progress:

- Starter backend now has a `SessionStore` protocol, memory default, and a
  local JSON-file development store behind `ESIMU_STARTER_SESSION_STORE=file`.
- Starter WebSocket smoke covers a browser-like loop: init, relax, event,
  event choice, forum, messenger, item buy/sell, exam, and ending.
- Starter public actions use neutral `forum` and `messenger` names; legacy
  `cc98`/`dingtalk` names stay in reference compatibility space.
- Starter frontend now commits a pnpm lockfile and has CI typecheck/build
  commands.
- `docs/starter-contract.md` records the starter HTTP/WebSocket surface,
  persistence extension point, and frontend dependency policy.
- The original simulator's reusable AI path now lives in `esimu_core.ai`:
  OpenAI-compatible configuration/transport, M2-her role messages, structured
  event/forum/messenger/graduation generation, output validation, effect
  clamps, and library/hybrid/AI degradation policy.
- Starter actions can opt into AI through `ESIMU_CONTENT_MODE` and
  `ESIMU_LLM_*`/`ESIMU_RP_*`; default library mode remains network-free.
- ZJU reference AI code reuses the core provider table, JSON parser, and
  M2-her role contract while retaining Redis pools, vector retrieval, and
  player-key policy in the compatibility adapter.

### Phase 13: Release Channel Decision

Goal: choose the official package distribution story.

Key work:

- Decide between Git tags only, GitHub Packages, or PyPI for `esimu-core`.
- Add build artifacts and release workflow if publishing beyond Git tags.
- Version docs and publish the Zensical site from the independent repo.
- Define compatibility guarantees for:
  - Python APIs,
  - theme/world contract,
  - starter app behavior,
  - scaffold CLI output.
- Add an upgrade guide template for breaking changes.

Deliverables:

- Release workflow.
- Versioned docs publishing workflow.
- Compatibility policy promoted from alpha notes into a formal document.

Completion criteria:

- A downstream project can pin `esimu-core`, read matching docs, and upgrade
  intentionally.

Progress:

- Added the installed `esimu-validate-world` command and removed generated
  project validation dependence on an esimu-lab path.
- Added package artifact smoke: build sdist/wheel, generate a project, create a
  clean venv, install `esimu-core[ai]`, validate the theme, and call Starter API.
- Added tag-triggered CI with exact `esimu-core-v<version>` validation.
- Added browser HTTP/WebSocket proxy smoke and configurable split-origin
  frontend/backend deployment settings.
- Remaining before Phase 13 is complete: commit and push the release candidate,
  create the first matching Git tag, and verify its CI from the remote checkout.

### Phase 14: First External Simulator Trial

Goal: prove independence with a real non-ZJU simulator generated from esimu.

Key work:

- Use `new_project.py` to create a second non-ZJU simulator outside the esimu
  repo.
- Replace demo-campus placeholder content with a small but coherent playable
  theme.
- Record every missing hook, unclear contract, hardcoded assumption, and
  bootstrap pain point.
- Feed framework-worthy fixes back into esimu.

Deliverables:

- External simulator trial report.
- Starter/framework improvement backlog.
- Recommendation: keep alpha, publish beta, or revise architecture.

Completion criteria:

- The external simulator can run without copying ZJU-specific product code.
- Its changes to esimu are framework improvements, not one-off patches.
- Phase 13 release story has been exercised by a real downstream project.

## Independence Milestone Recommendation

Do not call esimu a fully independent formal framework until Phase 12 is done.

Use these labels:

- After Phase 10: **independent clone works**.
- After Phase 11: **framework repo no longer depends on ZJU reference by
  default**.
- After Phase 12: **starter is suitable for real prototypes**.
- After Phase 13: **versioned framework release is credible**.
- After Phase 14: **framework has been proven by an external simulator**.

