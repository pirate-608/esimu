# Backend Core

Backend extraction begins with pure domain rules and world-data loaders before
copying the FastAPI app shell.

The first extracted pieces from ZJUers Simulator are now normalized into the
`esimu_core.*` namespace instead of preserving their source `app.game.*` paths.

Do not copy production Docker, secrets, or deployment workflows during the first
pass.

## Current Bootstrap Copy

The first low-coupling world loaders have been placed under
`esimu_core/world/`:

- `stat_definitions.py`
- `items.py`
- `balance.py`
- `theme.py`
- `story.py`
- `prompts.py`
- `theme_paths.py`
- `catalog.py`
- `scripts/validate_world_data.py`
- `scripts/sync_stat_definitions.py`
- `scripts/scaffold_game_stat.py`
- `scripts/sync_theme_metadata.py`
- `scripts/sync_story_metadata.py`

The first pure gameplay rules are now under `esimu_core/domain/`:

- `semester.py`: final-exam score calculation, term/cumulative GPA, legacy GPA
  fallback, and new-period stat recovery.
- `effects.py`: bounded stat changes, feedback entries, relax overflow
  detection, and overflow transfer.
- `actions.py`: runtime action gating for running, paused, and post-exam states.

These modules intentionally avoid Redis, SQLAlchemy, FastAPI, random state, and
theme-specific names. They are the first step toward making the copied engine an
adapter over a reusable simulator core.

The first runtime orchestration helpers are now under `esimu_core/runtime/`:

- `clock.py`: tick sleep and elapsed-time arithmetic.
- `actions.py`: adapter-facing action decisions.
- `state.py`: plain runtime DTOs for stats, course state, and session snapshot.
- `cooldowns.py`: remaining-cooldown calculations from timestamps and config.
- `snapshot.py`: `tick`/`init`/`new_semester` payload assembly from plain state
  values.
- `tasks.py`: background task tracking and target-level de-duplication.

Runtime helpers may know about simulator concepts, but they must not import
Redis, FastAPI, SQLAlchemy, OpenAI, or reference-app services.

`esimu_core.world.catalog` owns the static world-directory contract for majors,
course plans, achievements, event libraries, forum-library JSON, and optional
query embeddings. Reference apps may wrap it with async caching or API-specific
schemas, but they should not reintroduce their own `/app/world` path resolver.

## Package Boundary

The Python package is installed as `esimu-core` and imported as
`esimu_core.*`. The reference backend should depend on it explicitly, normally
through the editable requirement in `apps/zju-reference/zjus-backend/requirements.txt`:

```text
-e ../../../simulator-core/backend
```

If an offline Windows venv cannot build editable installs because `setuptools`
is unavailable, a local `.pth` file pointing at `D:\projects\simulator-framework-lab\simulator-core\backend`
is an acceptable development fallback. Do not reintroduce `sys.path` bridge code
inside the reference backend.

## Active Theme Path

The copied loaders now use `esimu_core.world.theme_paths`:

```text
SIMULATOR_THEME=zju
themes/zju/world/
```

Validation commands from this directory:

```powershell
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe -m py_compile esimu_core\world\theme_paths.py esimu_core\world\theme.py esimu_core\world\story.py esimu_core\world\prompts.py esimu_core\world\balance.py esimu_core\world\items.py esimu_core\world\stat_definitions.py esimu_core\world\catalog.py esimu_core\domain\semester.py esimu_core\domain\effects.py esimu_core\domain\actions.py esimu_core\runtime\clock.py esimu_core\runtime\actions.py esimu_core\runtime\state.py esimu_core\runtime\cooldowns.py esimu_core\runtime\snapshot.py esimu_core\runtime\tasks.py
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe -m pytest tests
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe -m pytest tests\test_world_catalog.py
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe -m ruff check esimu_core scripts tests
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe scripts\validate_world_data.py
$env:SIMULATOR_THEME='demo-campus'; D:\projects\ZJUers_simulator\.venv\Scripts\python.exe scripts\validate_world_data.py
```

Theme manifest generation:

```powershell
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe scripts\sync_theme_metadata.py --write
```

Story metadata generation:

```powershell
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe scripts\sync_story_metadata.py --write
```

