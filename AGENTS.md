# AGENTS.md

This file is the handoff guide for AI agents working in Simulator Framework Lab.

## Prime Directive

Do not modify `D:\projects\ZJUers_simulator` while working in this lab unless the
user explicitly asks for a cross-repository change. ZJUers Simulator is the main
game. This workspace is an experiment.

## Workspace Boundary

- Lab root: `D:\projects\simulator-framework-lab`
- Main game root: `D:\projects\ZJUers_simulator`

Code may be copied from the main game only as a deliberate step. When copying,
record the source path and commit or note the copied version.

The first copied reference app lives at `apps/zju-reference/`. Treat it as a
runnable baseline for extraction experiments, not as the final framework layout.

## Isolation Rules

- Use lab-specific Docker Compose project names, database names, Redis volumes,
  ports, and localStorage keys.
- Do not reuse ZJU production image names, domains, secrets, or deployment
  workflows.
- Do not let the lab depend on files in the ZJU working tree through relative
  imports.
- Reference backend code must import reusable rules/loaders from the local
  `esimu-core` package (`esimu_core.*`), not through temporary `sys.path`
  bridges.
- If a fix belongs in the main game, implement it in the main game separately
  after review instead of silently patching the lab copy only.

## Architecture Direction

Prefer a build-time selected theme first:

```text
SIMULATOR_THEME=zju
SIMULATOR_THEME=demo-campus
```

Runtime multi-theme switching is a later experiment. It should not be introduced
before the single-theme extraction is stable.

## Naming Rules

- Framework shorthand: `esimu`
- Core package name: `esimu-core`
- Python import namespace: `esimu_core`

Do not introduce old temporary framework-core names except in historical
migration notes.

Theme packs own `theme.json`, `story.json`, `prompts.json`, `world/`, and
`assets/`. `prompts.json` changes model-visible campus/forum/messenger context;
legacy internal IDs such as `cc98` and `dingtalk` remain compatibility IDs until
a deliberate protocol migration happens.

`esimu_core.runtime` is the boundary for reusable runtime orchestration. Core
helpers may calculate tick timing, action decisions, payload dictionaries, and
background-task bookkeeping. They must not import Redis, FastAPI, SQLAlchemy,
OpenAI, or reference-app services; adapters perform all I/O and emit returned
decisions/payloads.

## Review Priorities

1. Does the change keep the ZJU main project untouched?
2. Does the lab remain isolated from ZJU ports, volumes, storage keys, and
   deployment names?
3. Does the theme pack boundary become clearer?
4. Does copied code still run with tests, or is it only documentation/scaffold?
