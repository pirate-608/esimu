# New Project Bootstrap

Use this checklist when starting a new simulator from esimu.

The goal is not to fork a perfect framework on day one. The goal is to get one
theme running, validate the data boundary, and only then decide how much of the
reference app should be copied or rewritten.

## 1. Choose The Project Shape

Start with one selected theme at build/startup time:

```powershell
$env:SIMULATOR_THEME='<theme_id>'
```

Runtime multi-theme switching is not part of the current lab contract.

## 2. Create A Theme Pack

Copy the minimal theme:

```powershell
cd D:\projects\ZJUers_simulator\labs\esimu
Copy-Item -Recurse themes\demo-campus themes\<theme_id>
```

Then edit:

```text
themes/<theme_id>/theme.json
themes/<theme_id>/story.json
themes/<theme_id>/prompts.json
themes/<theme_id>/world/
themes/<theme_id>/assets/
```

Keep `theme_id` stable. Future saves may bind to it.

## 3. Edit Theme Metadata

Use `theme.json` for short structural terms:

- product display name
- institution/campus/player labels
- forum and messenger display names
- browser storage prefix
- default visual assets

Use `story.json` for long narrative text:

- first-visit prologue
- diary or scene pages
- ending text
- graduation fallback comments
- end-screen background references

Use `prompts.json` for model-facing content-generation context:

- campus context
- forum and messenger names
- random-event instruction
- private-chat instruction
- graduation-summary instruction
- fallback messages

Do not move long prose into `theme.json`.

## 4. Edit World Data

The `world/` directory currently contains game balance, stats, items,
achievements, courses, characters, event libraries, and forum/message libraries.

For a first playable theme, keep the data small. It is better to validate a tiny
complete theme than to copy a large world pack full of hidden assumptions.

Recommended order:

1. `stat_definitions.json`
2. `game_balance.json`
3. `items.json`
4. majors and courses
5. achievements
6. characters
7. event/forum/message libraries

## 5. Validate The Theme

Run these from `simulator-core/backend/`:

```powershell
$env:SIMULATOR_THEME='<theme_id>'
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe scripts\validate_world_data.py
```

If the theme should drive the reference frontend, regenerate metadata:

```powershell
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe scripts\sync_theme_metadata.py --write
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe scripts\sync_story_metadata.py --write
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe scripts\sync_stat_definitions.py --write
```

Then run validation again.

## 6. Decide Whether To Reuse The Reference App

Read `starter-app-shape.md` before copying any reference-app files.

For the first demo, reuse `apps/zju-reference/` as the adapter. It already knows
how to run the backend, WebSocket loop, frontend, saves, admin pages, and
content-generation fallback path.

Only fork or copy the adapter when the new project needs different product
behavior, not just different nouns or world data.

Current recommendation:

- Use a reference-app fork only when a runnable product shell is needed now.
- Keep ZJU reference as a regression target, not the final starter template.
- Prefer the future `apps/starter/` once Phase 6 creates it.

## 7. Preserve Compatibility IDs

The current lab still uses legacy internal IDs such as `cc98` and `dingtalk` in
protocol payloads, Redis keys, save data, and tests. New themes should change
the visible terms through `theme.json` and `prompts.json`, not by renaming these
IDs yet.

Protocol-ID migration is a separate roadmap item.

## 8. Add A Project Handoff File

For a new simulator project, copy the template:

```powershell
Copy-Item templates\agent\AGENTS.md <new-project-root>\AGENTS.md
```

Fill in the project root, theme ID, app entry points, validation commands, and
any production boundaries. Keep ZJU-specific details out unless the new project
is actually a ZJU reference derivative.
