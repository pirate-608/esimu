# Theme Pack Contract

This page is the authoring contract for esimu theme packs. A theme pack owns the
world, narrative, prompt, and asset data for one simulator deployment; core code
and adapter code should consume this data instead of hardcoding product nouns.

Use `new-project-bootstrap.md` for the step-by-step workflow, and use
`starter-app-shape.md` before copying the reference app.

## Validation Gate

The canonical validation command is:

```powershell
cd D:\projects\ZJUers_simulator\labs\esimu\simulator-core\backend
$env:SIMULATOR_THEME='<theme_id>'
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe scripts\validate_world_data.py
```

`validate_world_data.py` now includes the schema-equivalent validator in
`esimu_core.world.theme_contract`. It validates:

- required theme files and world files,
- `theme.json`, `story.json`, `prompts.json`, and `stat_definitions.json`
  through Pydantic models,
- structural contracts for majors, courses, achievements, event libraries,
  forum libraries, characters, items, balance, and graduation comments,
- item/event effect allowlists from the stat registry,
- story image availability,
- generated frontend metadata freshness for the default theme.

For non-default themes, generated frontend metadata freshness is skipped unless
`SIMULATOR_VALIDATE_GENERATED=1` is set. This prevents demo-theme validation
from overwriting the reference frontend by accident.

## Required Directory

```text
themes/<theme_id>/
  theme.json
  story.json
  prompts.json
  assets/
  world/
    stat_definitions.json
    game_balance.json
    items.json
    majors.json
    achievements.json
    event_library.json
    cc98_library.json
    characters.json
    graduation_comments.json
    courses/
      <major_abbr>.json
```

`assets/` may be minimal, but images referenced by `story.json` must exist in
either the theme assets directory or the reference frontend public images
directory while the reference app remains the active adapter.

## Theme Manifest

`theme.json` owns short structural terms and public metadata.

Required fields:

- `theme_id`: stable lowercase ID matching `[a-z][a-z0-9-]*`.
- `display_name`: public product/theme name.
- `terms`: must include at least `campus`, `forum`, `messenger`, `player`,
  `semester`, `course`, and `item`.
- `storage.prefix`: browser storage namespace matching `[a-z][a-z0-9_]*`.

Recommended terms:

- `institution`
- `institution_short`
- `feed`
- `server`
- `player_nickname`
- `rules`
- `notice`

Use `theme.json` for short nouns only. Do not put prologue writing, prompt
templates, item descriptions, or course data here.

## Story Content

`story.json` owns long narrative copy:

- first-visit prologue dedication lines,
- diary pages and scene image mappings,
- failure ending copy,
- graduation ending copy,
- GPA-branched graduation lines,
- fallback graduation summary,
- graduation background image filenames.

Scene and ending image fields are filenames, not paths. Path traversal and
subdirectories are rejected.

## Prompt Fragments

`prompts.json` owns model-facing context:

- campus context,
- forum and messenger names,
- forum batch instruction,
- random-event instruction,
- messenger batch instruction,
- private-chat instruction,
- player identity template,
- messenger scene/opening templates,
- graduation-summary instruction,
- forum fallback text.

Prompt fragments theme the visible and model-visible context. They do not
rename legacy internal IDs such as `cc98` and `dingtalk`; those remain adapter
compatibility IDs until a later protocol migration.

## World Data

### Stats

`world/stat_definitions.json` is the stat registry:

- every stat ID must match `[a-z][a-z0-9_]*`,
- `default` must be inside `min`/`max`,
- allocatable stats must show in character creation,
- allocatable defaults must sum to `initial_budget`,
- item and event effect allowlists come from `allow_item_effect` and
  `allow_event_effect`.

### Balance

`world/game_balance.json` must contain at least:

- `tick.interval_seconds`,
- `events.random_event`,
- `events.dingtalk`,
- `game_over`.

The reference adapter may support additional balance fields. Theme validation
checks only the structural minimum that a starter app can depend on.

### Items

`world/items.json` must contain:

- `economy` object,
- `items` array,
- unique item IDs,
- item names and numeric prices,
- optional `effects` object.

Item effect fields must also be allowed by `stat_definitions.json`.

### Majors And Courses

`world/majors.json` may be either:

- a flat list of major objects, or
- a grouped object whose values are lists of major objects.

Each major needs:

- `abbr` or `id`,
- `name`.

For each major, `world/courses/<major_abbr>.json` must exist. Course files may
be either:

- a flat list of course objects, treated as one starter term, or
- an object with `plan` or `semesters`, where each term has `courses`.

Each course needs:

- `id`,
- `name`,
- numeric `credits` greater than zero.

### Achievements

`world/achievements.json` may be either:

- an object keyed by achievement code, or
- a list of objects with `code` or `id`.

Each achievement needs:

- code/id,
- `name`,
- `desc` or `description`.

Condition expressions remain reference-adapter behavior for now; later phases
may move achievement evaluation into core.

### Events And Forum

`world/event_library.json` must be a non-empty array. Each event needs:

- `title`,
- `desc` or `description`,
- non-empty `options` array,
- each option needs `text` and `effects` object.

`world/cc98_library.json` is still the compatibility filename for the local
forum library. Each forum entry needs `content`; `effect`, `trigger`, and
`topic` are optional.

### Characters

`world/characters.json` must be a non-empty array. Each character needs:

- `name`,
- `role`,
- `content` or `description`.

The current ZJU reference app still uses DingTalk-compatible role IDs for
private-message behavior. Theme-visible messenger names come from `theme.json`
and `prompts.json`.

### Graduation Comments

`world/graduation_comments.json` must contain a non-empty `comments` array.
Each comment needs either:

- `texts`, or
- `paragraphs`.

Optional `min_gpa` and `max_gpa` fields define GPA branches.

## New Theme Checklist

1. Copy `themes/demo-campus/` to `themes/<theme_id>/`.
2. Update `theme.json`, especially `theme_id` and `storage.prefix`.
3. Update `story.json` and referenced images.
4. Update `prompts.json`.
5. Replace `world/majors.json` and `world/courses/*.json`.
6. Replace stats, items, achievements, events, forum posts, characters, and
   graduation comments.
7. Run `validate_world_data.py`.
8. If the reference frontend should run this theme, regenerate metadata:

```powershell
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe scripts\sync_theme_metadata.py --write
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe scripts\sync_story_metadata.py --write
D:\projects\ZJUers_simulator\.venv\Scripts\python.exe scripts\sync_stat_definitions.py --write
```

9. Run validation again.
10. Run the relevant reference backend/frontend smoke checks.

## Compatibility Notes

- `cc98` and `dingtalk` are legacy internal IDs in the reference app.
- Theme authors should change visible labels through `forum` and `messenger`
  terms rather than renaming protocol IDs.
- `cc98_library.json` keeps its compatibility filename until the protocol/data
  migration phase explicitly renames it.
- Runtime multi-theme switching is out of scope; esimu uses startup/build-time
  theme selection.

## Related Documents

- `quickstart.md`: validation and metadata-generation commands.
- `new-project-bootstrap.md`: practical new-theme checklist.
- `starter-app-shape.md`: whether to copy the reference app.
- `agent-handoff.md`: agent rules for keeping theme data out of core logic.
- `architecture.md`: how theme packs relate to `esimu-core` and adapters.
