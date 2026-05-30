# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`esimu` — CLI tool that generates browser-based text simulator games from YAML config files. Write YAML → `esimu build` → playable HTML game.

## Commands

```bash
# Development (use bun, not node/npm)
bun run src/cli.ts -- <command>    # Run CLI during development
bun run typecheck                   # TypeScript type checking (noEmit)

# CLI commands (operate in CWD)
esimu init                          # Scaffold game project (game.yml + events/ + .gitignore)
esimu init --interactive            # Interactive config wizard
esimu init --template <name>        # Use preset template (default|cultivation|survival|fantasy)
esimu init --force                  # Overwrite existing files
esimu build                         # Build dist/ from game.yml
esimu build --config <path>         # Use non-default config file
esimu build --output <dir>          # Custom output directory
esimu build --watch                 # Watch mode — auto-rebuild on changes
esimu serve                         # In-memory dev server with live reload (no prior build needed)
esimu serve --port <number>         # Custom port
esimu serve --config <path>         # Use non-default config file
esimu serve --no-open               # Don't auto-open browser

# Production build (single binary, current platform)
bun build src/cli.ts --compile --outfile dist-bin/esimu

# Cross-compile for all platforms (used in CI)
bun build src/cli.ts --compile --target=bun-linux-x64    --outfile dist/esimu
bun build src/cli.ts --compile --target=bun-darwin-arm64 --outfile dist/esimu
bun build src/cli.ts --compile --target=bun-windows-x64  --outfile dist/esimu.exe

# Release: push a v* tag → GitHub Actions builds & publishes via .github/workflows/release.yml
```

## Architecture

### CLI entry (`src/cli.ts`)
Minimal commander setup — registers three subcommands imported from `src/commands/`. The entry runs as a Bun script (`#!/usr/bin/env bun`), so use `bun` for all development.

### Commands (`src/commands/`)

- **`init.ts`** — Scaffolds a game project in CWD. Supports three modes: default template, interactive wizard (asks questions via readline, builds config string), or named template. Calls `scaffold()` to write `game.yml`, `events/example.md`, and `.gitignore` to disk. Template strings come from `src/templates/index.ts`.

- **`build.ts`** — Core compilation pipeline: `loadConfig()` validates + parses the YAML, `resolveDescriptions()` converts Markdown event files to HTML via `marked`, then `doBuild()` generates three output files into `dist/`:
  - `index.html` — hardcoded dark-theme HTML shell with three screens (character creation, game, ending)
  - `css/style.css` — dark theme with responsive design, inline styles for stat panels, event area, choices, endings
  - `js/game.js` — serialized `GAME_CONFIG` + `EVENT_DESCRIPTIONS` JSON embedded directly, plus a runtime engine (state management, point-buy character creation, conditional choice display, stat effects, event routing, ending evaluation)
  
  Watch mode uses `chokidar` on the config file + `events/` directory, suppressing per-build output.

- **`serve.ts`** — In-memory dev server (like mkdocs serve). `buildInMemory()` calls `loadConfig()` + `resolveDescriptions()` + the generator functions and stores the result as `{ html, css, js }` in memory — no disk writes. `Bun.serve` routes `/`, `/css/style.css`, `/js/game.js` from these in-memory strings, plus `/__esimu_live` for SSE. Always watches source files via `chokidar`, rebuilds in memory on change, and pushes SSE `reload` events to the browser. No `--live` or `--dir` flags — serve always operates this way. `esimu build` is the separate path for writing output to `dist/`.

### Utilities (`src/utils/`)

- **`config.ts`** — YAML loading + validation. `loadConfig()` reads + parses via `js-yaml`, then calls `validateConfig()` which checks every field in the config schema (title, description, stats with min/max/default, character_creation with assignable referencing valid stat keys, events with unique ids, choices with next_event, endings). A "start" event is required. `resolveDescriptions()` merges inline `description` text with file-based `descriptionFile` (converted via `marked`) for each event.

- **`types.ts`** — TypeScript interfaces for the full config schema: `GameConfig`, `StatConfig`, `CharacterCreationConfig`, `EventConfig`, `Choice`, `EndingConfig`. All config validation is runtime, not compile-time.

- **`prompt.ts`** — readline-based interactive prompts used by `init --interactive`: `ask()`, `askNumber()`, `askYesNo()`.

- **`generator.ts`** — shared HTML/CSS/JS output generators used by both `build.ts` and `serve.ts`. `generateHTML(config, liveReload?)` accepts an optional boolean to inject the SSE live-reload script. `generateCSS()` produces a minimal dark theme using CSS custom properties (`--bg`, `--accent`, etc.) that users can override. `resolveCSS(config, baseDir)` reads a custom CSS file if `css` is set in game.yml, otherwise falls back to `generateCSS()`.

### Templates (`src/templates/`)
`index.ts` exports a `TEMPLATES` map (key → YAML string) and `TEMPLATE_NAMES` map (key → Chinese display name). Four presets: default, cultivation (修仙), survival (末日), fantasy (龙与地牢). Each is a complete `game.yml` with stats, character creation, events, and endings.

Template content is inlined as template literal strings in `index.ts` (needed for `bun build --compile`). The editable source-of-truth YAML/MD files live in `src/templates/files/`. After editing them, run `bun run sync-templates` to regenerate `index.ts` with the updated content.

## Key conventions

- **All CLI commands operate on CWD**, not a subdirectory. User workspace files (game.yml, events/, dist/) live in the directory the user runs the command from.
- **`descriptionFile` and `css` paths** in game.yml are resolved relative to the config file's directory, not CWD.
- **Build is destructive** — `dist/` is always cleared and fully regenerated; no incremental builds.
- **Custom CSS** — `game.yml` supports an optional `css` field pointing to a custom stylesheet. If set, it replaces the auto-generated CSS entirely. The default CSS uses CSS custom properties (`--bg`, `--surface`, `--accent`, etc.) for easy theming.
- **Errors in Chinese** — user-facing error messages and console output use Chinese.
- **The HTML/CSS/JS generators** live in `src/generator.ts`. `build.ts` and `serve.ts` both import from it. `generateHTML(config, liveReload?)` accepts an optional boolean to inject the SSE live-reload script for `--live` mode.
- **`bun` runtime** — use `bun` for running, building, and typechecking. The `@types/bun` package provides Bun's API types.
