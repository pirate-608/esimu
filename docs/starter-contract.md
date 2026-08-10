# Starter Contract

`apps/starter/` is the default app base for new esimu simulator prototypes. It
is intentionally smaller than the ZJU reference adapter and should remain easy
to copy, delete, or replace.

## Scope

The starter promises:

- a minimal FastAPI backend,
- a tiny Vite/TypeScript frontend,
- in-memory sessions by default,
- optional local JSON-file sessions for development,
- theme/story/stat metadata generated from a theme pack,
- neutral public actions for forum and messenger surfaces,
- no Redis, PostgreSQL, SQLAdmin, production Docker, or mandatory LLM client.

The starter installs the optional AI transport and exposes it through
environment configuration, but defaults to `ESIMU_CONTENT_MODE=library`.
See `ai-integration.md` for model providers, M2-her, and degradation behavior.

Use the ZJU reference adapter only when a project needs those heavier features
immediately.

## Backend HTTP Surface

The starter backend exposes a deliberately small surface:

| Route | Purpose |
| --- | --- |
| `GET /healthz` | Return dependency-light process readiness. |
| `GET /config` | Return active theme, story, and stat metadata. |
| `POST /api/auth` | Create a placeholder in-memory session token. |
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
| `relax` | `feedback` |
| `event` | `event` |
| `event_choice` | `feedback` |
| `forum` | `forum_post` |
| `messenger` | `messenger_round` |
| `item_buy` | `items_state` |
| `item_sell` | `items_state` |
| `exam` | `semester_summary` |
| `ending` | `ending` |

Legacy IDs such as `cc98` and `dingtalk` belong in the ZJU reference adapter or
compatibility mappers, not in starter public naming.

## Persistence

Default:

```text
ESIMU_STARTER_SESSION_STORE=memory
```

Development file store:

```text
ESIMU_STARTER_SESSION_STORE=file
ESIMU_STARTER_DATA_DIR=data/starter-sessions
```

The file store writes one JSON file per token and exists only as a local
development extension point. Production projects should replace the
`SessionStore` protocol with their chosen persistence layer.

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
