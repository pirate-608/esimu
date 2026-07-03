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

## Next Planned Phases

These phases are intentionally broad. Each should become a smaller
implementation plan before coding starts.

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

### Phase 4D: Starter App Shape

Goal: decide what a new simulator project should copy.

- Compare two starter shapes: reference-app fork versus minimal starter app that
  depends on `esimu-core`.
- Identify which files from `apps/zju-reference` are adapter boilerplate,
  ZJU-specific product code, or candidates for future frontend/core extraction.
- Expand `templates/` only after the copy boundary is clear.
- Produce a concrete recommendation before Phase 5.

## Phase 5: Framework Decision

Decide whether the lab should become:

- a reusable internal framework,
- a template repository,
- a library plus starter app,
- or remain a research branch with cherry-picked improvements.

Supporting handoff work now lives in:

- `quickstart.md`: local setup and validation path.
- `new-project-bootstrap.md`: new theme/app startup checklist.
- `agent-handoff.md`: current extraction state for future agents.
- `theme-pack-contract.md`: active theme pack contract.

