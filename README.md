# Simulator Framework Lab

This workspace is an experimental extraction lab for a reusable narrative
simulator framework inspired by ZJUers Simulator.

## Relationship To ZJUers Simulator

ZJUers Simulator remains the main product and the highest priority. This lab is
allowed to copy ideas and selected code, but it must not become a dependency of
the main ZJU game until an extracted piece is mature, tested, and intentionally
cherry-picked back.

## Goal

Build a reusable lightweight strategy narrative simulator with replaceable
theme packs:

- A core simulation loop for time, state, saves, events, messages, items, and
  achievements.
- Theme packs for campus or non-campus worlds.
- A frontend skin layer that can rename concepts and swap visuals without
  rewriting gameplay logic.

## Non-Goals For The Lab Bootstrap

- Do not migrate the live ZJUers Simulator project in place.
- Do not share production databases, Redis volumes, Docker names, ports, or
  browser storage keys with the ZJU project.
- Do not deploy lab images to the ZJU production registry.
- Do not chase a fully generic engine before the first `core + zju theme pack`
  experiment runs.

## Initial Layout

```text
apps/
  zju-reference/ # Full copied app used as the first runnable reference.
simulator-core/
  backend/       # esimu-core Python package and backend contracts.
  frontend/      # Future extracted Vue components, stores, and theme loader.
themes/
  zju/           # First reference theme, copied deliberately from ZJU later.
  demo-campus/   # Tiny validation theme for portability tests.
docs/
  architecture.md
  roadmap.md
  theme-pack-contract.md
```

## First Milestone

Prove that a single theme can be selected at build/startup time and that the
copied ZJU reference behavior can be represented as:

```text
esimu-core + apps/zju-reference + themes/zju
```

Only after that should the lab attempt a second theme.

See `docs/zju-reference-baseline.md` for the first full-copy baseline.

## Naming

- Framework shorthand: `esimu`
- Core package name: `esimu-core`
- Python import namespace: `esimu_core`

The lab previously used temporary names during extraction. New code and docs
should use `esimu` naming, except when historical notes explicitly describe the
old migration path.
