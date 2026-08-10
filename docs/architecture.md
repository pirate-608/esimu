# Architecture Sketch

The lab starts from the current ZJUers Simulator shape but separates the system
into three explicit layers.

Start with `quickstart.md` if you are setting up the lab, and use
`new-project-bootstrap.md` when creating a new simulator or theme from this
architecture.

## 1. esimu-core

Core owns behavior that should survive theme changes:

- Pure domain rules for semester settlement, GPA, period recovery, stat bounds,
  and effect feedback.
- World-data loaders for balance, stat definitions, items, theme manifests,
  story content, and prompt fragments.
- Optional AI contracts for OpenAI-compatible transport, theme-aware content
  generation, M2-her role messages, output validation, and fallback policy.
- Eventually: auth/session entry pattern, game loop, pause/resume state machine,
  saves, event/message dispatch, and admin editors.

## 2. Theme Pack

A theme pack owns world-specific nouns, data, and assets:

- `theme.json`
- balance, stat definitions, items, achievements, characters, event libraries
- prologue and ending text
- prompt fragments for LLM-backed events, forum posts, messages, and graduation
  summaries
- image, video, audio, and icon assets
- terminology such as forum name, messenger name, campus name, and player label

## 3. Frontend Skin

The skin layer maps core UI surfaces to theme terminology and visual treatment.
The first lab iteration should use build-time theme selection so that frontend
types and assets stay simple.

## Starter App

`apps/starter/` is the first minimal non-ZJU app shape. Its backend is an
in-memory FastAPI adapter over `esimu-core`, and its frontend is a small
Vite/TypeScript skin that consumes generated theme/story/stat metadata. The
starter is intentionally smaller than `apps/zju-reference/`: it excludes
Redis, PostgreSQL, admin editors, production Docker, persistent model caches,
and vector retrieval so new projects can add those decisions deliberately.

The starter now includes an optional `esimu_core.ai` adapter, but remains in
local `library` mode unless model environment variables are configured.

## Initial Constraint

Do not support multiple active themes in one running deployment yet. The first
stable target is one deployment, one selected theme.

## Active Theme Resolution

Core backend loaders use `SIMULATOR_THEME`, defaulting to `zju`, and read world
data from:

```text
themes/<theme_id>/world/
```

For unusual runs, `SIMULATOR_LAB_ROOT` can point at the lab root and
`SIMULATOR_WORLD_DIR` can point directly at a world directory. Generated frontend
stat metadata writes to the reference app by default, or to
`SIMULATOR_FRONTEND_STAT_OUTPUT` when set.

Current core loaders already routed through the active theme path:

- `game_balance.json`
- `items.json`
- `stat_definitions.json`
- majors, course plans, achievements, event libraries, and forum libraries
  through `esimu_core.world.catalog`

Authoring-time theme validation lives in `esimu_core.world.theme_contract` and
is invoked by `scripts/validate_world_data.py`. Runtime loaders remain
tolerant where useful; the contract validator is the stricter pre-runtime gate
for missing files and malformed theme/world data.

Theme manifests are also loaded through core and generated into the reference
frontend:

```text
themes/<theme_id>/theme.json
apps/zju-reference/zjus-frontend/src/data/theme.generated.ts
```

The reference frontend uses `src/utils/theme.ts` for high-frequency shell terms
such as product title, campus feed, messenger name, forum name, and exit/login
copy. Browser persistence uses `src/utils/storageKeys.ts`, which derives
localStorage keys from `theme.json`'s `storage.prefix`; do not add fixed
`simlab_*` keys to runtime code.

The reference backend keeps `app.services.world_service.WorldService` as an
async/cache adapter, but the actual static world directory contract now lives in
`esimu_core.world.catalog`. Reference app code should not add new `/app/world`
or copied-repo path fallbacks when a theme-owned file can be resolved through
the catalog.

Long-form story content is loaded separately:

```text
themes/<theme_id>/story.json
apps/zju-reference/zjus-frontend/src/data/story.generated.ts
```

`story.json` currently owns the first-visit prologue and end-screen narrative
copy, including diary pages, scene image mappings, failure notes, GPA-branched
graduation lines, fallback graduation summary text, and graduation background
images. This keeps `theme.json` small and leaves longer writing in an editable
theme-owned file.

LLM prompt context is loaded separately:

```text
themes/<theme_id>/prompts.json
```

`prompts.json` owns short model-facing fragments such as campus context, forum
name, messenger name, random-event instruction, private-chat instruction, and
graduation-summary instruction. It does not rename legacy protocol IDs.

## Pure Domain Rules

The first behavior extracted from the ZJU reference app lives under:

```text
simulator-core/backend/esimu_core/domain/
```

Current modules:

- `semester.py`: deterministic exam score calculation, GPA aggregation,
  cumulative GPA migration fallback, and new-period recovery toward baseline.
- `effects.py`: stat bounds, feedback payload formatting, relax-only positive
  overflow detection, and overflow transfer to useful stats.
- `actions.py`: runtime, paused, and post-exam action gates.

These modules deliberately avoid Redis, SQLAlchemy, FastAPI, random state, and
theme-specific names. Runtime adapters should pass in resolved balance values,
stat bounds, labels, and random deltas. This lets the eventual engine/state
machine depend on stable rules instead of re-implementing calculations.

The package name is `esimu-core`; Python imports use the `esimu_core.*`
namespace. The copied ZJU reference backend consumes it as a local editable
development dependency and no longer uses a `sys.path` bridge. Current adapter
calls cover final-exam score calculation, GPA aggregation, new-semester energy
recovery, pause/action gating, relax overflow transfer, active theme loaders,
story data, and prompt fragments.

## Lifecycle Contracts

Reusable setup and transition payload shaping lives under:

```text
simulator-core/backend/esimu_core/lifecycle/
```

Current helpers build fresh-character state fragments, new-semester reset
fragments, and achievement detail payloads.
They return plain dictionaries/dataclasses and deliberately avoid reference-app
schemas or storage clients. The reference backend still owns username safety,
Redis writes, PostgreSQL persistence, WebSocket emission, and LLM calls.

## Content And Message Contracts

Theme-neutral content payload shaping lives under:

```text
simulator-core/backend/esimu_core/content/
```

Current helpers define framework-facing concepts (`feed`, `forum`,
`messenger`) while mapping reference compatibility IDs (`cc98`, `dingtalk`) at
adapter boundaries. They normalize local random events, forum posts, messenger
contacts, reply options, and stat/gold settlement effects. Local-library
selection for events and forum posts now lives in core; the reference adapter
still owns JSON caching, LLM fallbacks, Redis content pools, WebSocket emission,
and persisted DingTalk-compatible state schemas.

## Runtime Orchestration

The next extracted layer lives under:

```text
simulator-core/backend/esimu_core/runtime/
```

Current modules:

- `clock.py`: converts configured tick intervals and speed multipliers into
  real-time sleep and virtual elapsed-time increments.
- `actions.py`: wraps pure action gates in adapter-facing decisions.
- `snapshot.py`: builds existing `tick` and `init` payload dictionaries from
  already-read state, including remaining semester time and derived efficiency.
- `state.py`: defines plain runtime state DTOs that adapters can build from
  their storage or schema models before calling core helpers.
- `cooldowns.py`: calculates remaining cooldown seconds from timestamps and
  action cooldown configuration.
- `tasks.py`: tracks background tasks and de-duplicates long-running work by
  target key.

Runtime helpers still avoid Redis, FastAPI, SQLAlchemy, OpenAI, and WebSocket
objects. The reference app reads/writes external systems, then passes plain
values into `esimu_core.runtime` and emits the returned payloads. In the ZJU
reference adapter, `_runtime_snapshot_from_repo()` is the current seam between
Redis/Pydantic snapshots and `RuntimeSnapshot`.

## Optional AI Layer

Reusable AI generation lives under `esimu_core.ai`. The base package does not
import the OpenAI SDK until an application constructs
`OpenAICompatibleTransport`; the SDK is distributed through the `[ai]` extra.
Prompt assembly, structured-output parsing, event-effect validation, M2-her
role messages, and library/hybrid/AI fallback decisions belong to core.

Applications still own credentials, Redis/database caches, embeddings,
moderation, billing, WebSocket emission, and persistence. This preserves a
small deterministic core while making the original simulator's AI behavior a
reusable framework module.

## Compatibility IDs

The lab currently keeps `dingtalk` and `cc98` as internal protocol/action IDs
because they flow through WebSocket payloads, Redis keys, save data, and legacy
tests. User-facing labels should come from theme terms (`messenger`, `forum`).
Renaming those IDs is a later compatibility migration, not part of the current
adapter-extraction phase.

## Related Documents

- `quickstart.md`: setup and validation commands.
- `theme-pack-contract.md`: current theme file contract.
- `new-project-bootstrap.md`: checklist for a new simulator/theme.
- `starter-app-shape.md`: decision record for what a new project should copy.
- `release-policy.md`: package versioning and tag-based release process.
- `framework-readiness-review.md`: Phase 9 framework readiness verdict.
- `agent-handoff.md`: current agent operating notes.
- `roadmap.md`: extraction phases and current progress.

