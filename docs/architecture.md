# Architecture

esimu uses three explicit layers:

```text
theme pack -> esimu-core -> application adapter
```

## Theme Pack

`themes/<theme_id>` owns visible terms, story, prompts, assets, stats, balance,
items, majors, courses, events, forum content, characters, achievements, and
graduation text. One deployment selects one theme through `ESIMU_THEME`.

## esimu-core

`packages/esimu-core/esimu_core` contains only reusable Python logic:

- `world`: paths, loaders, Pydantic contracts, and validation;
- `domain`: effects, action gates, declarative achievements, GPA, and semester rules;
- `runtime`: timing, snapshots, cooldowns, automatic scheduling, and task bookkeeping;
- `lifecycle`: character and semester state construction;
- `content`: neutral event, forum, and messenger contracts;
- `ai`: optional provider configuration, transport, parsing, and degradation;
- `scaffold`: the wheel-owned Starter template used by `esimu new`;
- `authoring`: installed doctor/inspect/sync/add operations and atomic writes;
- `project`: standard-library dev supervision, reload triggers, and validated
  build orchestration. It executes adapter tools without importing them.

Core does not import FastAPI, SQLite, Redis, SQLAlchemy, WebSocket, or Vue.
Visible ZJU copy in the default template belongs to `themes/zju-simplified`
and generated metadata, never reusable protocol or application logic.

## Starter Adapter

`apps/starter/backend` owns FastAPI, WebSocket lifecycle, serialized sends,
real-time tick tasks, and asynchronous persistence. SQLite with WAL is the
single-node default; memory is used for tests. Slow content generation stays
outside the session lock and uses per-target background-task deduplication.

`apps/starter/frontend` is a Vue 3/Pinia application generated with theme,
story, and stat metadata. It implements onboarding, the game console, courses,
events, forum, messenger, items, semesters, and endings.

Public Starter actions use neutral `forum` and `messenger` IDs. Theme schema is
v1; state and WebSocket protocol are v2, with additive state-v1 migration and
protocol-v1 client compatibility.

