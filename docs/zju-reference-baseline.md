# ZJU Reference Baseline

This document records the first code-copy baseline for the framework lab.

## Source

- Source workspace: `D:\projects\ZJUers_simulator`
- Destination workspace: `D:\projects\simulator-framework-lab\apps\zju-reference`
- Source commit at verification time: `53cb7d176bb68094beb30979eff70fd15aa6220e`
- Copy time: `2026-07-01T19:33:51+08:00`
- Source worktree after copy verification: clean

## Copy Strategy

The first lab app is a full working reference copy. It is intentionally not the
final framework shape. The copy exists so framework extraction can begin from a
known runnable game instead of rebuilding glue code from scratch.

## Excluded From Copy

- `.git`
- `.env` and `.env.*`
- dependency directories such as `node_modules`
- build outputs such as `dist`
- Python caches and test caches
- temporary pytest/release-health folders
- runtime logs
- `nginx/ssl`

## First Isolation Edits

- Docker image/container/volume names use the `simlab` prefix.
- Local backend port is `127.0.0.1:18000:8000`.
- Local Postgres port is `127.0.0.1:25432:5432`.
- Local Redis port is `127.0.0.1:16379:6379`.
- Local Nginx HTTP port is `18080`.
- Vite dev server port is `15173`.
- Vite proxy points to `127.0.0.1:18000`.
- Frontend browser storage keys use the `simlab_` prefix.

