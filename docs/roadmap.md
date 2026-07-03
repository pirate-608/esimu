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

### Phase 7: Packaging And Versioning

Goal: make `esimu-core` consumable as a real dependency instead of a lab-only
editable package.

- Finalize Python package metadata, extras, and supported Python versions.
- Add changelog/version policy for `esimu-core`.
- Decide whether releases are Git tags only, GitHub packages, or a future PyPI
  package.
- Add CI checks for core tests, starter smoke, demo theme validation, and
  reference adapter compatibility.

Deliverables:

- Versioned `esimu-core` package.
- Release checklist and compatibility policy.
- CI matrix covering `esimu-core`, `apps/starter`, and `apps/zju-reference`.

Completion criteria:

- A downstream project can pin an esimu-core version and upgrade intentionally.
- Breaking changes to theme/world contracts are documented and tested.

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

## Framework Decision

The decision point remains open until Phase 9. esimu may become:

- a reusable internal framework,
- a template repository,
- a library plus starter app,
- or remain a research branch with cherry-picked improvements.

Supporting handoff work now lives in:

- `quickstart.md`: local setup and validation path.
- `new-project-bootstrap.md`: new theme/app startup checklist.
- `agent-handoff.md`: current extraction state for future agents.
- `theme-pack-contract.md`: active theme pack contract.

