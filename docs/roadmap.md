# Roadmap

esimu is an independent, theme-driven framework for single-theme narrative
simulators. This roadmap records current product milestones rather than the
archived extraction task list.

## Completed Milestones

### Extraction And Independence

- The original ZJU extraction is preserved by `esimu-lab-final`.
- esimu has an independent repository, package, docs site, license, CI, and
  release workflows; ZJUers Simulator is not a runtime dependency.
- `packages/esimu-core`, `apps/starter`, and `themes/demo-campus` are the
  canonical framework/core/app/theme boundaries.

### Public Beta 0.2

- `esimu-core 0.2.0b5` is available from PyPI and GitHub Releases.
- Wheel-owned `esimu new` creates a standalone FastAPI + Vue/Pinia project.
- Theme schema v1, SQLite persistence, optional AI, strict world validation,
  and an external generated-project trial are established.

### Public Beta 0.3

- `esimu-core 0.3.0b2` is published on PyPI and GitHub Releases after
  TestPyPI and independent generated-project Docker validation.
- State and WebSocket protocol v2 retain v1 migration/client compatibility.
- Persistent cooldowns, automatic event/messenger scheduling, declarative
  achievements, Game Over, content modes, and ordered save/exit close the
  runtime loop.
- Messenger replies are two-phase and non-blocking, with unread state, contact
  diversity/reuse, and three-reply settlement.
- Installed `doctor`, `inspect`, `sync`, and `add` commands provide project
  diagnostics and atomic theme authoring.
- The canonical Starter frontend exposes the complete runtime behavior.

### Phase 16: Publish 0.3 Beta

- Passed the clean-checkout Python, Starter, frontend, and documentation matrix.
- Exercised the wheel in `esimu-beta-example`, including CLI authoring and
  Docker Compose startup without an esimu source checkout.
- Superseded the TestPyPI-only b1 after its generated-theme defect, then
  validated and published immutable `0.3.0b2` artifacts.
- Published matching Zensical 0.0.57 documentation.

Completed: an external project can install the package, generate a simulator,
edit and sync a theme, persist/recover state, and complete the configured game
without an esimu source checkout.

## Phase 17: Adapter Ecosystem

- Specify optional production identity and multi-save extension contracts.
- Prove at least one PostgreSQL or Redis-backed `SessionStore` downstream
  adapter without importing those dependencies into core.
- Design an optional operational world-data editor around the same validators
  and atomic publication rules used by `esimu add`.
- Document observability, backup, migration, and deployment patterns.

## Phase 18: Reuse And Stability

- Decide whether stable frontend pieces justify a separately versioned npm
  package; keep the generated Starter canonical until proven otherwise.
- Add schema migration tooling before changing theme schema v1 or protocol v2.
- Test multiple coherent non-campus themes to expose remaining domain nouns.
- Define the path from Beta compatibility to a stable 1.0 contract.

## Deliberately Out Of Scope

- Runtime multi-theme switching in one deployment.
- Redis, PostgreSQL, production identity, or admin dependencies in core.
- Reintroducing ZJU-specific protocol IDs or product copy into Starter.
