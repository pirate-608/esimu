# Changelog

All notable changes to esimu are recorded here.

This project follows a lightweight Semantic Versioning policy for `esimu-core`:

- `MAJOR`: incompatible Python API or theme/world contract changes.
- `MINOR`: new reusable core APIs, optional contract fields, or starter
  capabilities that remain backward compatible.
- `PATCH`: bug fixes, documentation clarifications, and validation improvements
  that do not break existing valid themes.

## 0.3.0b2 - Unreleased

- Superseded the TestPyPI-only `0.3.0b1` candidate after external generation
  exposed hardcoded `demo-campus` defaults in AI and backend environment setup;
  generated projects now resolve their active theme consistently.
- Updated the documentation toolchain to Zensical 0.0.57 and synchronized the
  bilingual site with the current runtime, CLI, persistence, and release state.
- Added persistent relax cooldowns, automatic event/messenger scheduling,
  declarative achievements, configurable Game Over, and richer ending payloads.
- Added session-scoped library/hybrid/AI modes and non-blocking two-phase
  messenger replies with unread state, contact reuse, and three-reply rounds.
- Added protocol v2 save/exit, heartbeat, mode, achievement, messenger-update,
  and Game Over messages while retaining protocol-v1 client responses.
- Added state v2 with automatic v1 JSON migration and no SQLite table change.
- Added installed `esimu doctor`, `inspect`, `sync`, and `add` authoring commands
  with JSON output, explicit writes, atomic publication, validation, and rollback.

## 0.2.0b5 - 2026-08-26

- Formalized esimu as an independent Beta framework and bumped `esimu-core` to
  `0.2.0b5` with version-one theme, state, and WebSocket contracts.
- Replaced the source-dependent generator with wheel-packaged `esimu new`,
  retained `esimu validate`, and added artifact-to-consumer release coverage.
- Upgraded the canonical Starter to a Vue 3/Pinia game console, real-time tick
  loop, neutral forum/messenger actions, and asynchronous SQLite persistence.
- Archived and removed the copied ZJU reference application and theme from the
  formal branch; the final extraction baseline remains tagged `esimu-lab-final`.
- Added MIT licensing, security/contribution policies, TestPyPI/PyPI trusted
  publishing workflows, and public Beta support documentation.
- Renamed the primary branch from `master` to `main` and aligned first-party
  CI, documentation deployment, release instructions, and agent handoff notes.
- Fixed clean-runner CI by declaring the FastAPI TestClient dependencies used
  by project bootstrap tests and installing pnpm before frontend cache setup.
- Added the Starter and ZJU reference generated theme metadata to source
  control, and made the Ruff version and lint baseline explicit across local
  and CI runs.
- Added a reproducible Starter backend development dependency set and local
  Ruff configuration for generated projects.
- Updated first-party GitHub Actions to their Node 24-based v7 releases.
- Updated the documentation toolchain from Zensical 0.0.46 to 0.0.53 and
  enabled configuration-level strict builds.
- Added `esimu-validate-world`, an installed CLI that validates a generated
  project's own theme without retaining an esimu-lab source path.
- Added an artifact-to-consumer release smoke that builds sdist/wheel, installs
  into a disposable venv, generates a simulator, validates it, and exercises
  the Starter API.
- Added Starter readiness/CORS configuration, same-origin Vite HTTP/WebSocket
  proxying, configurable production API/WS bases, and visible connection errors.
- Made generated projects discover their own root before importing eager
  world/AI loaders and copy world-data scaffold helpers locally.
- Added clean-checkout CI coverage for release tags and exact package/tag
  version matching.
- Added project bootstrap tooling with `scripts/new_project.py`.
- Added world-data scaffolding for items, achievements, events, courses, and
  prompt fragments.
- Added Phase 9 framework readiness review and selected the
  `esimu-core + starter app + theme pack` direction for alpha usage.
- Added optional `esimu_core.ai` configuration, OpenAI-compatible transport,
  M2-her role messages, structured content generation, effect validation, and
  library/hybrid/AI fallback policy.
- Connected starter event, forum, messenger, and graduation actions to the
  optional AI adapter while preserving network-free library defaults.

## 0.1.0 - 2026-07-04

Initial lab package baseline.

- Added `esimu-core` as an installable Python package under the
  `esimu_core.*` namespace.
- Added active-theme world loaders for stat definitions, balance, items, theme
  manifests, story content, prompt fragments, and world catalog data.
- Added pure domain helpers for semester settlement, effects, and action gates.
- Added runtime helpers for clock math, snapshots, cooldowns, and background
  task tracking.
- Added lifecycle helpers for character initialization, semester reset, and
  achievement payloads.
- Added content contracts for event, forum, and messenger payloads.
- Added strict theme-pack validation and the first minimal `apps/starter/`.
