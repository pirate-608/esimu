# CLI Reference

The installed `esimu` command owns project generation, validation, diagnostics,
metadata synchronization, and conservative world-data authoring.

## Project Commands

```powershell
esimu version
esimu new <target> --project-name "My Simulator" --theme-id my-simulator
esimu validate --root . --theme my-simulator
esimu doctor --root . --theme my-simulator
esimu inspect --root . --theme my-simulator
```

- `new` copies the wheel-owned Starter and source theme into an independent
  project and pins its core dependency.
- `validate` checks the complete theme/world contract and returns non-zero on
  authoring errors.
- `doctor` checks Python/core versions, the theme contract, generated metadata,
  Starter paths, Node/corepack/pnpm availability, SQLite path, and whether AI
  credentials are configured. It never prints secrets.
- `inspect` reports contract versions, resolved project/theme paths, generated
  outputs, and world-data counts.

Use `--json` with `doctor` or `inspect` for automation.

## Metadata Sync

```powershell
esimu sync --root . --theme my-simulator
esimu sync --root . --theme my-simulator --write
```

Without `--write`, sync only checks theme/story/stat TypeScript metadata and
fails when generated files are stale. Explicit writes validate first and
replace all generated files atomically; a failed write restores the originals.

## World Authoring

```powershell
esimu add stat focus --root . --theme my-simulator --label Focus --show-in-hud
esimu add item focus_card --root . --theme my-simulator --name "Focus Card"
esimu add achievement first_win --root . --theme my-simulator --name "First Win"
esimu add event campus_moment --root . --theme my-simulator --title "Campus Moment"
esimu add course systems --root . --theme my-simulator --plan GEN --semester 2
esimu add prompt graduation_instruction --root . --theme my-simulator --text "..."
```

`add` prints a JSON preview by default. Add `--write` only after review. A write
updates one source file, synchronizes generated metadata, validates the complete
theme, and rolls back source/generated files on failure.

Useful stat options include `--allocatable`, `--adjust-budget`,
`--allow-item-effect`, `--allow-event-effect`, and `--llm-context`.
Achievement predicates use `--scope`, `--key`, `--op`, and `--value`. Event
drafts always contain two choices so they satisfy the Starter contract.

## Compatibility

`esimu-validate-world` remains an alias for `esimu validate` during the 0.3
Beta. Generated source scripts remain wrappers for one Beta cycle; new CI and
agent automation should call the installed `esimu` command.
