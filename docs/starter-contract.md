# Starter Contract

`apps/starter/` is the default app base for new esimu simulator prototypes. It
is intentionally smaller than production-specific downstream adapters and should remain easy
to copy, delete, or replace.

## Scope

The starter promises:

- a minimal FastAPI backend,
- a Vue 3/Pinia Vite/TypeScript console,
- SQLite sessions by default, with memory sessions for tests,
- local JSON-file sessions as a temporary Beta compatibility adapter,
- theme/story/stat metadata generated from a theme pack,
- neutral public actions for forum and messenger surfaces,
- persistent cooldowns, achievements, content modes, and ending state,
- automatic event/messenger scheduling and non-blocking model work,
- no Redis, PostgreSQL, SQLAdmin, production Docker, or mandatory LLM client.

The starter installs the optional AI transport and exposes it through
environment configuration, but defaults to `ESIMU_CONTENT_MODE=library`.
See `ai-integration.md` for model providers, M2-her, and degradation behavior.

Downstream projects can replace the adapter when they need distributed storage,
production identity, or an operational admin surface.

## Backend HTTP Surface

The starter backend exposes a deliberately small surface:

| Route | Purpose |
| --- | --- |
| `GET /healthz` | Return dependency-light process readiness. |
| `GET /config` | Return active theme, story, and stat metadata. |
| `POST /api/auth` | Create or restore an opaque local-profile token. |
| `GET /api/majors` | Return active-theme majors. |
| `POST /api/init_character` | Initialize one in-memory character. |
| `WS /ws` | Run a small action protocol for smoke flows. |

These routes are a starter contract, not the final API contract for every
downstream game.

## Browser Connectivity

The frontend defaults to same-origin requests. In local development,
`vite.config.ts` proxies `/api`, `/config`, `/healthz`, and `/ws` to
`ESIMU_DEV_BACKEND_URL`, defaulting to `http://127.0.0.1:18001`.

Same-origin production should forward those paths through its reverse proxy.
Split-origin deployments set `VITE_ESIMU_API_BASE` and `VITE_ESIMU_WS_BASE` at
frontend build time, then list allowed browser origins in backend
`ESIMU_CORS_ORIGINS` as a comma-separated value. Do not use wildcard CORS for
credential-bearing production APIs.

## WebSocket Actions

The starter uses neutral action names:

| Action | Response |
| --- | --- |
| `start` / `get_state` | `tick` |
| `ping` | `pong` |
| `pause` / `resume` / `set_speed` | `tick` |
| `set_mode` | `mode_changed` |
| `relax` | `feedback` |
| `event` | `event` |
| `event_choice` | `feedback` |
| `forum` | `forum_post` |
| `messenger` | `messenger_update` (`messenger_round` for protocol v1) |
| `messenger_reply` | immediate player `messenger_update`, then background NPC update |
| `messenger_mark_read` | `messenger_update` |
| `item_buy` | `items_state` |
| `item_sell` | `items_state` |
| `exam` | `semester_summary` |
| `next_semester` | `new_semester` |
| `ending` | `ending` |
| `save_game` | `save_result` |
| `save_and_exit` | `save_result`, `exit_confirmed`, close code 1000 |
| `exit_without_save` | `exit_confirmed`, close code 1000 |

Protocol v2 is current. Protocol-v1 clients are accepted and receive legacy
`messenger_round`/`messenger_reply` response names. Legacy product IDs such as
`cc98` and `dingtalk` do not appear in Starter public naming.

## Persistence

Default single-node store:

```text
ESIMU_STARTER_SESSION_STORE=sqlite
ESIMU_STARTER_DATABASE_PATH=data/esimu.sqlite3
```

SQLite uses WAL, transaction writes, hashed token lookup, and JSON state v2.
State-v1 payloads receive additive defaults during load; the SQLite schema
remains at user_version 1 because state is stored as a versioned JSON document.

Tests can select `ESIMU_STARTER_SESSION_STORE=memory`.

Development file store:

```text
ESIMU_STARTER_SESSION_STORE=file
ESIMU_STARTER_DATA_DIR=data/starter-sessions
```

The file store writes one JSON file per hashed token and remains only for the
0.4 Beta compatibility window. Distributed deployments should implement the
asynchronous `SessionStore` protocol in the downstream application.

## Runtime Behavior

- Relax cooldown timestamps persist and remaining seconds are included in
  `init` and `tick`.
- Event and messenger checks use the interval/probability values in
  `game_balance.json`; they stop while paused, settling, or ended.
- A messenger round settles after three player replies. Player messages are
  saved and emitted before optional AI generation starts.
- Achievement conditions are theme-owned declarative `all`/`any` predicates.
- Game Over thresholds come from `game_balance.json`; graduation and failure
  share the theme-owned ending copy but remain distinct outcomes.

## Frontend Dependencies

The starter frontend uses pnpm and commits `pnpm-lock.yaml`. CI should run:

```powershell
cd apps\starter\frontend
corepack pnpm install --frozen-lockfile
corepack pnpm typecheck
corepack pnpm build
```

Keep the frontend skin small until a downstream project proves a reusable
component package is worth extracting.
