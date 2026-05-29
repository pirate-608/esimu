# AGENTS.md

## Project

`esimu` — CLI tool that generates browser-based text simulator games from YAML config files.

**One-liner:** Write YAML config → `esimu build` → playable HTML game in `dist/`.

## Tech stack

- **Runtime:** TypeScript + [Bun](https://bun.sh) (use `bun` commands, not `node`/`npm`)
- **CLI framework:** commander
- **YAML parsing:** js-yaml
- **Markdown conversion:** marked (or built-in simple converter)
- **File watching:** chokidar
- **Local server:** Bun's built-in `Bun.serve` or `serve` package

## Commands

- `esimu init` — scaffold a new game project (game.yml + events/)
- `esimu build` — compile game.yml into `dist/` (index.html, css/style.css, js/game.js)
- `esimu serve` — start local dev server (default port 3000), auto-open browser

## Project structure (user workspace)

```
my-game/
├── game.yml          # main config (YAML format defined in ROADMAP.md)
├── events/           # per-event Markdown descriptions (referenced via descriptionFile)
└── dist/             # build output (gitignored)
    ├── index.html
    ├── css/style.css
    └── js/game.js
```

## Configuration format

`game.yml` sections: `title`, `description`, `stats`, `character_creation`, `events[]`, `endings[]`.
Full schema is documented in `ROADMAP.md` lines 210–248.

## Key conventions

- All CLI commands operate on the **current working directory** (not a subdirectory).
- `descriptionFile` paths in game.yml are relative to the **config file's directory**.
- Build always **clears and recreates** `dist/` — no incremental builds.
- The generated game engine (`js/game.js`) handles: state management, character creation (point-buy), event scheduling, conditional choices, and ending evaluation.

## Development status

Refer to `ROADMAP.md`. The repo is in **Phase 1 (planning)** — no source code exists yet.
Implementation order: project init → CLI framework → `init` command → `build` command → game template → `serve` command → docs.
