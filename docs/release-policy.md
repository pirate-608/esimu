# Release Policy

`esimu-core` is alpha software. It is suitable for single-theme simulator
prototypes, but not yet a stable public framework.

## Version And Tag Contract

- Distribution name: `esimu-core`
- Import namespace: `esimu_core`
- Version source: `simulator-core/backend/esimu_core/__init__.py`
- Tag format: `esimu-core-v<version>`

The generator pins downstream projects to that exact Git tag. Therefore a
version is not externally installable until the matching tag exists on
`pirate-608/esimu-lab` and contains the Starter/core changes being documented.
Do not claim a Git-tag release before both branch and tag have been pushed.

The current policy uses Git tags, not PyPI. Reconsider PyPI after a real external
simulator has exercised installation and upgrades.

## Compatibility

Semantic Versioning applies:

- `MAJOR`: breaking Python API or theme/world contract removal.
- `MINOR`: compatible core APIs, validators, and Starter capabilities.
- `PATCH`: bug fixes and stricter rejection of already-invalid data.

Because the package is `0.x`, document substantial minor reshaping in
`CHANGELOG.md`. Public compatibility includes Python APIs documented by core,
theme/world JSON contracts, installed CLI behavior, and the Starter HTTP/WS
surface.

## Required Release Gate

From a clean checkout and local venv:

```powershell
python -m pip install -r requirements-dev.txt
cd simulator-core\backend
python -m pytest tests
python -m ruff check esimu_core scripts tests
python scripts\validate_world_data.py
$env:SIMULATOR_THEME='demo-campus'
python scripts\validate_world_data.py
Remove-Item Env:SIMULATOR_THEME
```

Starter backend and frontend:

```powershell
cd apps\starter\backend
python -m pytest tests
python -m ruff check app tests
cd ..\frontend
corepack pnpm install --frozen-lockfile
corepack pnpm typecheck
corepack pnpm build
```

Artifact-to-consumer smoke:

```powershell
cd esimu-lab
python simulator-core\backend\scripts\release_smoke.py
zensical build
```

`release_smoke.py` builds sdist/wheel, generates a disposable simulator, creates
a clean venv, installs `esimu-core[ai]` from the wheel, runs the installed world
validator, and exercises the generated Starter API. This is mandatory because
editable source tests cannot catch packaging/import-order failures.

## CI And Tagging

CI runs required core, Starter, frontend, docs, and external-install jobs from a
clean checkout. Push the release commit first and wait for CI.

Then confirm:

```powershell
python -c "import esimu_core; print(esimu_core.__version__)"
git status --short
git log -1 --oneline
```

Create and push the exact matching tag:

```powershell
git tag esimu-core-v0.1.0
git push origin main
git push origin esimu-core-v0.1.0
```

Tag-triggered CI rejects a tag whose name differs from
`esimu-core-v<esimu_core.__version__>`. After it passes, generate a project with
the default dependency and verify `pip install -r
apps/starter/backend/requirements.txt` from a machine or clean directory that
does not contain esimu-lab.

If ZJUers Simulator references this repository as a submodule, update the parent
pointer only after the independent release is complete.
