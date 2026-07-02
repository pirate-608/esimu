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
- The reference frontend has a focused theme-helper test proving visible labels
  and storage keys come from generated theme metadata rather than hardcoded ZJU
  copy.

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

