# esimu Starter Frontend

This deliberately small Vite/TypeScript skin consumes generated theme, story,
and stat metadata and calls the Starter HTTP/WebSocket contract.
It renders cooldowns, unread messenger contacts, achievements, content modes,
save status, and distinct failure/graduation outcomes from protocol v2.

## Local Development

Start the backend on `127.0.0.1:18001`, then run:

```powershell
corepack pnpm install --frozen-lockfile
corepack pnpm dev
```

Open `http://127.0.0.1:15175`. Vite proxies `/api`, `/config`, `/healthz`, and
`/ws` to the backend. Change the proxy target with
`ESIMU_DEV_BACKEND_URL=http://127.0.0.1:<port>`.

## Deployment

The production build defaults to same-origin API and WebSocket paths. A reverse
proxy should forward `/api`, `/config`, `/healthz`, and `/ws` to the backend.
For split-origin deployment, copy `.env.example` to `.env` and set
`VITE_ESIMU_API_BASE` and `VITE_ESIMU_WS_BASE`; configure the same browser
origin in backend `ESIMU_CORS_ORIGINS`.

## Checks

```powershell
corepack pnpm typecheck
corepack pnpm test
corepack pnpm build
```
