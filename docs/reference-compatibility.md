# Reference Compatibility

`apps/zju-reference/` is kept as an optional compatibility-rich adapter. It is
not part of the default framework path.

Use it when a change needs evidence against the original ZJUers Simulator
surface area: Redis-backed saves, SQLAdmin editors, DingTalk-compatible
messenger behavior, CC98-compatible forum behavior, or the copied production
frontend shell.

## Default Path

For ordinary framework work, validate only:

```text
esimu-core + apps/starter + theme pack + docs
```

That path is what new simulator projects should learn first. It should continue
to work even if `apps/zju-reference/` is ignored.

## When To Run Reference Checks

Run reference checks when touching:

- legacy `cc98` or `dingtalk` internal IDs,
- reference backend adapters,
- reference frontend metadata/runtime code,
- Redis/PostgreSQL save compatibility,
- admin world-data editors,
- content-generation fallback behavior copied from ZJUers Simulator.

## Commands

Reference backend:

```powershell
cd esimu-lab\apps\zju-reference\zjus-backend
python -m pytest tests\unit\test_demo_campus_reference_smoke.py
python -m pytest tests\unit\test_game_state.py tests\unit\test_dingtalk_state.py
python -m ruff check app tests\unit
```

Reference frontend:

```powershell
cd esimu-lab\apps\zju-reference\zjus-frontend
npx vitest run src\utils\theme.spec.ts
npx vitest run src\components\themeRuntime.spec.js
npx vue-tsc --noEmit
```

CI exposes these checks as an optional manual workflow path. The required CI
jobs are core, starter, and docs.
