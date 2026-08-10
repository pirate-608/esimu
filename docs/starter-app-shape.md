# Starter App Shape

Phase 4E decides what a new simulator project should copy today, and what
should wait for the future minimal starter app.

## Decision

Use `apps/starter/` as the default new-project base. Keep the ZJU reference app
as the rich compatibility adapter and regression target.

For a new simulator today:

1. Create or copy a theme pack.
2. Validate the theme through `esimu-core`.
3. Start from `apps/starter/` for the first runnable product shell.
4. Rename visible product surfaces through theme/story/prompt metadata first.
5. Reuse `apps/zju-reference/` only when the project needs its save/admin,
   Redis/PostgreSQL, vector retrieval, or legacy compatibility behavior.

For the framework roadmap:

- Phase 5 should harden theme/world contracts.
- Phase 6 created `apps/starter/` as the first minimal non-ZJU app.
- `apps/zju-reference/` remains a compatibility-rich reference adapter and
  regression target.

This keeps esimu useful now without making every future project inherit ZJU's
full production history, admin surface, deployment shape, and legacy naming.

## Rationale

The reference app is valuable because it already has a working FastAPI backend,
WebSocket loop, save service, Redis/PostgreSQL persistence, admin editors,
content fallback policy, and Vue game console. It is also heavy: it carries ZJU
product copy, DingTalk/CC98 compatibility IDs, production deployment choices,
and many tests built around the original game.

A new simulator needs a reliable path to "something runs" before it needs a
perfect framework. The least risky route is therefore:

- copy themes first,
- reuse the reference app as an adapter while the core keeps shrinking,
- then extract a clean starter only after contracts are stable enough.

## Current Copy Guidance

Use this table when deciding whether a file from `apps/zju-reference/` belongs
in a new project.

| Area | Current role | New project guidance |
| --- | --- | --- |
| `zjus-backend/app/api/` | HTTP and WebSocket entry adapters | Copy only for a runnable fork; later starter should simplify auth/save flows. |
| `zjus-backend/app/game/engine.py` | Main reference runtime adapter | Do not treat as framework code; keep extracting pure rules into core before copying broadly. |
| `zjus-backend/app/services/` | Adapter services for world, saves, admin publish, game transitions | Copy for runnable fork; identify smaller starter services in Phase 6. |
| `zjus-backend/app/repositories/` | Redis persistence adapter | Copy only if the new app also uses Redis with the same save/live-state model. |
| `zjus-backend/app/models/` | SQLAlchemy persistence models | Copy for PostgreSQL-based fork; a starter may offer simpler persistence. |
| `zjus-backend/app/schemas/` | Reference save/WebSocket payload schemas | Copy for compatibility; future starter should rename public concepts while preserving core shapes. |
| `zjus-backend/app/content/` | Local library cache plus core selection adapter | Copy for now; keep local selection rules in `esimu_core.content`. |
| `zjus-backend/app/core/llm.py` | Redis-cached compatibility adapter over reusable AI contracts | Prefer `esimu_core.ai`; copy only reference cache/key policy when required. |
| `zjus-backend/app/core/dingtalk_llm.py` | MiniMax RP compatibility adapter with vector selection | Prefer neutral `esimu_core.ai` M2-her support; copy only pgvector/cache integration when required. |
| `zjus-backend/app/admin.py` and admin services | Operational editors for world files | Copy if useful, but rename visible terms and keep file publishing theme-aware. |
| `zjus-frontend/src/components/` | Full game console and onboarding skin | Copy for runnable fork; future starter should keep a smaller component set. |
| `zjus-frontend/src/utils/theme.ts` and `storageKeys.ts` | Theme/runtime helpers | Good starter candidates; keep generated metadata boundary. |
| `zjus-frontend/src/data/*.generated.ts` | Generated theme/story/stat metadata | Regenerate for the active theme; never hand-edit. |
| `zjus-frontend/src/types/api.generated.ts` | Generated API types for the reference backend | Regenerate only from the chosen backend OpenAPI contract. |
| `docs/`, `.agents/`, `.codex/`, `.claude/` under reference app | ZJU product docs and agent workflows | Do not copy wholesale; start from `templates/agent/AGENTS.md` and write project docs. |
| `docker-compose*.yml`, `nginx/`, `.github/` | Reference deployment shape | Copy only after reviewing ports, image names, domains, and production security boundaries. |

## Candidate Future Extractions

These pieces are likely to move closer to framework or starter code later:

- theme metadata consumption in frontend components,
- storage-key derivation,
- generic WebSocket client/store message dispatch,
- basic game console layout primitives,
- save-slot UI shell,
- item and achievement display widgets,
- neutral messenger/forum adapters,
- minimal FastAPI/WebSocket adapter skeleton,
- admin file-publish pattern for theme world data.

These pieces should remain reference-only unless a later phase deliberately
generalizes them:

- ZJU invitation/login policy,
- ZJU-specific prologue and graduation writing,
- ZJU-specific MiniMax/DingTalk cache, pgvector, and legacy payload details,
- CC98/DingTalk visible copy and legacy compatibility tests,
- production Docker image names, domains, and Nginx rules,
- ZJU docs and deployment guidance.

## Recommended Starter Strategy

1. Prefer `apps/starter/` for new games.
2. Use `apps/zju-reference/` as a regression-rich example, not a default
   template.
3. Copy only the specific advanced features the starter lacks.
4. Keep `esimu-core` as an explicit dependency.
5. Keep theme content in `themes/<theme_id>/`, not in adapter code.

## Phase 4E Completion Criteria

Phase 4E is complete when:

- the starter decision is documented,
- reference app files have clear copy/classification guidance,
- new-project bootstrap points to this decision,
- agent handoff explains where starter-shape work belongs,
- no code contract is changed before Phase 5/6.
