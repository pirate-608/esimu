# AGENTS.md

## Project

`esimu` — CLI tool that generates browser-based text simulator games from YAML config files.

**One-liner:** Write YAML config → `esimu build` → playable HTML game in `dist/`.

## Tech stack

- **Runtime:** TypeScript + [Bun](https://bun.sh) (use `bun` commands, not `node`/`npm`)
- **CLI framework:** commander
- **YAML parsing:** js-yaml
- **Markdown conversion:** marked
- **File watching:** chokidar
- **Local server:** Bun.serve (in-memory, SSE live reload)
- **Distribution:** standalone binaries (GitHub Releases)

## Commands

```bash
esimu init                          # Scaffold game project (game.yml + events/ + .gitignore)
esimu init --interactive            # Interactive config wizard
esimu init --template <name>        # Preset template (default|cultivation|survival|fantasy)
esimu init --force                  # Overwrite existing files
esimu build                         # Build dist/ from game.yml
esimu build --config <path>         # Use non-default config file
esimu build --output <dir>          # Custom output directory
esimu build --watch                 # Watch mode — auto-rebuild on changes
esimu serve                         # In-memory dev server with live reload (no prior build needed)
esimu serve --port <number>         # Custom port
esimu serve --config <path>         # Use non-default config file
esimu serve --no-open               # Don't auto-open browser
```

## Project structure (user workspace)

```
my-game/
├── game.yml          # main config
├── events/           # per-event Markdown descriptions (referenced via descriptionFile)
└── dist/             # build output (gitignored)
    ├── index.html
    ├── css/style.css
    └── js/game.js
```

## Configuration format

`game.yml` sections: `title`, `description`, `css` (optional), `stats`, `character_creation`, `events[]`, `endings[]`.
Full schema is documented in `README.md`.

## Key conventions

- All CLI commands operate on the **current working directory** (not a subdirectory).
- `descriptionFile` and `css` paths in game.yml are relative to the **config file's directory**.
- Build always **clears and recreates** `dist/` — no incremental builds.
- The generated game engine (`js/game.js`) handles: state management, character creation (point-buy), event scheduling, conditional choices, and ending evaluation.
- Custom CSS: `game.yml` supports an optional `css` field pointing to a custom stylesheet. If set, it replaces the auto-generated CSS.
- Errors in Chinese.
- Template content is inlined in `src/templates/index.ts` (required for `bun build --compile`). Editable YAML/MD source files live in `src/templates/files/`. Run `bun run sync-templates` after editing them.

## Repo structure (source)

```
src/
├── cli.ts                # Entry point (commander)
├── commands/
│   ├── init.ts           # Scaffold game projects
│   ├── build.ts          # YAML → HTML/CSS/JS compilation
│   └── serve.ts          # In-memory dev server with SSE live reload
├── generator.ts          # Shared HTML/CSS/JS generators
├── templates/
│   ├── index.ts          # Inlined template strings (TEMPLATES, TEMPLATE_NAMES, EXAMPLE_EVENT_MD)
│   └── files/            # Editable source-of-truth YAML/MD files
└── utils/
    ├── config.ts         # YAML loading + validation + description resolution
    ├── types.ts          # TypeScript interfaces
    └── prompt.ts         # readline-based interactive prompts
scripts/
├── install.ps1           # Windows installer (one-liner: irm ... | iex)
├── install.sh            # Linux/macOS installer (one-liner: curl ... | bash)
└── sync-templates.ts     # Sync files/ → index.ts inline strings
.github/workflows/
└── release.yml           # Cross-compile + GitHub Release on tag push (v*)
```
