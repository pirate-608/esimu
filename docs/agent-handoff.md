# Agent Handoff

Read root `AGENTS.md` first. Work only in the independent esimu repository.
Core changes belong in `packages/esimu-core`, adapter/UI changes in
`apps/starter`, and visible content in `themes/<theme_id>`.

Before handoff, run core and Starter tests, Ruff, frontend type/test/build,
theme validation, scaffold freshness, Zensical build, and release smoke. Update
English and Chinese docs whenever a public command or contract changes.

Documentation dependencies are pinned in `docs/requirements.txt`; the current
toolchain is Zensical 0.0.57. Keep `mkdocs.yml` navigation free of missing or
archived pages and run the strict build after every docs change.

Current candidate is `0.3.0b2`: theme schema v1, state/protocol v2, additive
state-v1 migration, and protocol-v1 client compatibility. Prefer installed
`esimu doctor/inspect/sync/add` commands; source scripts are compatibility
wrappers. Slow event/forum/messenger AI work must stay outside the session lock
and use target-deduplicated background tasks.
