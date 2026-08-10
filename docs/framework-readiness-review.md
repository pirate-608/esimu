# Framework Readiness Review

Date: 2026-07-04

## Verdict

esimu is ready to be treated as a basically complete **alpha framework for
single-theme simulator prototypes**.

The recommended shape is:

```text
esimu-core + starter app + theme pack
```

It is not yet a stable public framework and should not be published to PyPI
until at least one external simulator project has used the starter path and
reported what was missing.
- The artifact-to-consumer path now passes locally, but the first matching Git
  tag has not been pushed; generated default dependencies are not externally
  installable until that release step is complete.

## What Is Ready

- `esimu-core` is an installable Python package with version metadata, typed
  package marker, changelog, release policy, and CI coverage.
- Core code owns reusable theme/world loaders, pure domain rules, runtime
  orchestration helpers, lifecycle setup/transition helpers, and content/message
  normalization.
- Core modules avoid app-specific I/O. The optional `esimu_core.ai` extra owns
  an OpenAI-compatible transport, while FastAPI, Redis, SQLAlchemy, WebSocket,
  credentials, caches, and persistence remain adapter concerns.
- Theme packs have a documented contract and a strict validation gate through
  `scripts/validate_world_data.py`.
- `demo-campus` validates the non-ZJU path and exercises local event, forum,
  messenger, item, achievement, story, prompt, and runtime payload contracts.
- `apps/starter` provides a memory-only FastAPI/WebSocket backend and a tiny
  Vite/TypeScript frontend skin.
- `scripts/new_project.py` can generate a standalone starter project with a
  selected theme ID, storage prefix, generated frontend metadata, README,
  `.env.example`, and agent handoff.
- `scripts/scaffold_world_data.py` and `scripts/scaffold_game_stat.py` reduce
  repetitive world-data authoring for items, achievements, events, courses,
  prompts, and stats.

## What Is Not Yet Stable

- Runtime multi-theme deployments are intentionally unsupported. The framework
  remains one deployment, one selected theme.
- The starter backend is memory-only by default, with a local JSON-file
  development store. Redis/PostgreSQL/save-slot adapters remain reference-app
  examples rather than starter features.
- The starter frontend is a skin, not a reusable frontend package. It now has a
  pnpm lockfile and CI type/build coverage, but no shared component packaging.
- `cc98` and `dingtalk` remain legacy internal compatibility IDs in the ZJU
  reference adapter. New themes can hide them through visible terms, but the
  protocol migration is still future work.
- The reference app remains a compatibility-rich adapter, not the default base
  for new projects.
- AI generation is available as an optional core/starter module. Admin editors,
  production Docker, persistent content caches, embeddings, and deployment
  hardening remain project-specific or reference-app features.

## Readiness Matrix

| Area | Status | Evidence |
| --- | --- | --- |
| Core package | Ready for alpha use | `esimu_core.__version__`, dynamic package metadata, `py.typed`, package metadata test |
| Theme contract | Ready | `theme_contract` validation, default and demo theme validation |
| Starter backend | Ready for prototypes | In-memory FastAPI adapter, file-dev session store, expanded smoke tests |
| Starter frontend | Prototype-ready | Minimal Vite/TypeScript skin, generated metadata, pnpm lockfile, type/build CI |
| Bootstrap tooling | Ready for alpha use | `new_project.py` smoke generates and validates a temp project |
| Reference adapter | Useful regression target | Demo-campus reference smoke and game-state tests pass |
| Persistence | Not starter-ready | Redis/PostgreSQL exist only in the reference app |
| Public release | Release candidate | Wheel/install smoke passes; first matching Git tag and remote CI remain pending |
| Non-ZJU proof | Minimal but sufficient | `demo-campus` validates and runs smoke paths, but is not full content |

## Validation Run

Phase 9 validation completed with:

```text
Core tests: 65 passed
Core ruff: passed
Default theme validation: passed
demo-campus validation: passed
Starter backend tests: 6 passed
Starter backend ruff: passed
Starter frontend typecheck/build: passed
Reference backend smoke/game-state tests: 28 passed
```

The hardcoded-name scan found only compatibility/documentation references for
`CC98`/DingTalk in core/starter-facing paths; no ZJU product copy was found in
the starter app or reusable core runtime logic.

## Recommendation

Keep esimu as a **library plus starter app**.

Do not turn it into a template-only repository, because `esimu-core` now has
useful package boundaries and independent tests. Do not treat it as a fully
stable public framework yet, because production persistence adapters, reusable
frontend packaging, and real external-project feedback are still missing.

The next sensible milestone is a `0.2.0` alpha focused on one of:

- production-grade optional persistence adapters,
- starter frontend reusable packaging,
- neutral messenger/forum protocol IDs beyond the starter surface,
- or a real second non-ZJU simulator built from `new_project.py`.

## Release Guidance

The current release channel should remain Git tags such as:

```text
esimu-core-v0.1.0
```

PyPI or GitHub Packages should wait until:

- a generated project has been used outside the lab,
- starter frontend reuse strategy is settled,
- and at least one upgrade across `esimu-core` versions has been documented.

## Independence Guidance

The framework is alpha-ready, but the repository is not fully independent from
the ZJU parent workspace yet.

The practical next steps are:

- Phase 10: remove parent-path and parent-venv assumptions so a fresh clone of
  `pirate-608/esimu-lab` works anywhere.
- Phase 11: make the ZJU reference app optional instead of part of the default
  framework path.
- Phase 12: harden the starter app enough for real downstream prototypes.
- Phase 13: choose a formal release channel.
- Phase 14: prove the framework with a real external non-ZJU simulator.

Do not describe esimu as a formally independent framework until at least Phase
12 is complete. After Phase 10 it can be described as an independently cloned
lab; after Phase 14 it can be described as a framework proven by an external
simulator.
