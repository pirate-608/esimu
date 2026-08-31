# Release Policy

esimu publishes pre-release versions of `esimu-core` for single-theme
narrative simulator projects. The current public Beta is `0.4.0b2`.

## Version And Contract

- Distribution: `esimu-core`
- Import namespace: `esimu_core`
- Version source: `packages/esimu-core/esimu_core/__init__.py`
- Tag format: `esimu-core-v<version>`
- Theme schema: v1
- Starter state and WebSocket protocol: v2

State v1 is migrated during load and protocol-v1 clients remain accepted.
Breaking changes to documented Python APIs, theme/world data, installed CLI,
or Starter HTTP/WebSocket behavior require a new minor Beta with migration
notes. Patch releases may reject data that was already invalid.

## Distribution

- `.github/workflows/release-candidate.yml` publishes manual TestPyPI
  candidates through Trusted Publishing.
- `.github/workflows/release.yml` builds and publishes PyPI artifacts and a
  GitHub prerelease when an exact `esimu-core-v<version>` tag is pushed.
- No long-lived PyPI token belongs in repository secrets.
- The GitHub Release must attach the wheel and sdist produced by the same job.

Do not claim a release until its tag workflow, PyPI page, GitHub prerelease,
and external installation trial all succeed.

## Required Gate

From a clean checkout and local venv:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest packages\esimu-core\tests
python -m pytest apps\starter\backend\tests
python -m ruff check packages\esimu-core\esimu_core packages\esimu-core\scripts packages\esimu-core\tests apps\starter\backend\app apps\starter\backend\tests
python packages\esimu-core\scripts\validate_world_data.py
python packages\esimu-core\scripts\sync_scaffold_bundle.py
```

Frontend and documentation:

```powershell
cd apps\starter\frontend
corepack pnpm install --frozen-lockfile
corepack pnpm typecheck
corepack pnpm test
corepack pnpm build
cd ..\..\..
zensical build
```

Artifact-to-consumer smoke:

```powershell
python packages\esimu-core\scripts\release_smoke.py
```

The smoke builds wheel/sdist, installs the wheel in a disposable environment,
runs `esimu new/validate/doctor/inspect/sync/add`, starts the generated Starter,
finishes both demo semesters, and verifies SQLite restart recovery.

## Candidate And Release Flow

1. Commit and push the candidate to `main`; wait for required CI.
2. Run the external `esimu-beta-example` trial without a source checkout.
3. Dispatch the TestPyPI workflow and install the exact candidate externally.
4. Fix framework issues and increment the immutable Beta suffix if necessary.
5. Create and push `esimu-core-v<version>` only after external acceptance.
6. Verify PyPI, GitHub prerelease assets, checksums, Pages, and clean install.

Zensical is pinned in `docs/requirements.txt`; documentation CI must install
that exact version and build in strict mode.
