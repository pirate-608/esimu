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
- `domain`: effects, action gates, GPA, and semester rules;
- `runtime`: timing, snapshots, cooldowns, and task bookkeeping;
- `lifecycle`: character and semester state construction;
- `content`: neutral event, forum, and messenger contracts;
- `ai`: optional provider configuration, transport, parsing, and degradation;
- `scaffold`: the wheel-owned Starter template used by `esimu new`.

Core does not import FastAPI, SQLite, Redis, SQLAlchemy, WebSocket, or Vue.

## Starter Adapter

`apps/starter/backend` owns FastAPI, WebSocket lifecycle, serialized sends,
real-time tick tasks, and asynchronous persistence. SQLite with WAL is the
single-node default; memory is used for tests.

`apps/starter/frontend` is a Vue 3/Pinia application generated with theme,
story, and stat metadata. It implements onboarding, the game console, courses,
events, forum, messenger, items, semesters, and endings.

Public Starter actions use neutral `forum` and `messenger` IDs. Version-one
theme, state, and WebSocket contracts are independent and included in payloads.

