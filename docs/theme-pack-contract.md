# Theme Pack Contract

This contract is provisional. It exists to make copied ZJU code move toward a
clear theme boundary instead of becoming another one-off game.

## Required Files

```text
themes/<theme_id>/
  theme.json
  story.json
  prompts.json
  world/
  assets/
```

## `theme.json`

Minimal shape:

```json
{
  "theme_id": "zju",
  "display_name": "ZJUers Simulator",
  "locale": "zh-CN",
  "terms": {
    "institution": "折姜大学",
    "institution_short": "折大",
    "campus": "求是园",
    "feed": "求是园动态",
    "forum": "CC98",
    "messenger": "钉钉",
    "server": "折大服务器",
    "player": "同学",
    "player_nickname": "折大人",
    "semester": "学期"
  },
  "storage": {
    "prefix": "zjus"
  },
  "assets": {
    "hero": "assets/hero.webp",
    "logo": "assets/logo.webp"
  }
}
```

## Design Notes

- `theme_id` should be stable because saves may eventually bind to it.
- `terms` replaces hardcoded product nouns in frontend and backend messages.
- `storage.prefix` prevents browser state from colliding across themes.
- Asset paths are relative to the theme directory until a runtime manifest
  loader says otherwise.

## `story.json`

`story.json` owns long narrative text: first-visit prologue scenes, diary pages,
ending copy, graduation background images, and deterministic graduation fallback
summaries. It is intentionally separate from `theme.json` so theme manifests
stay small and mostly structural.

## `prompts.json`

`prompts.json` owns model-facing short fragments for content generation:

```json
{
  "campus_context": "星桥学院校园",
  "forum_name": "星桥论坛",
  "messenger_name": "校内信",
  "forum_batch_instruction": "模拟星桥学院的校内论坛，生成 5 条帖子。",
  "random_event_instruction": "生成 3 个星桥学院校园随机事件，风格迥异。",
  "messenger_batch_instruction": "模拟星桥学院校内信消息，生成 5 条。",
  "private_chat_instruction": "你正在模拟星桥学院校园校内信私聊。",
  "player_identity_template": "你是一位星桥学院{major}专业的学生，名叫{username}，目前处于{semester}，{charm_label}值约为{charm}。",
  "messenger_scene_template": "场景：星桥学院校园，{semester}，校内信对话。当前情境：{scene}。",
  "messenger_open_template": "（{username}打开了校内信，看到一条新消息）",
  "graduation_instruction": "请根据玩家结业数据撰写毕业总结。",
  "forum_empty_fallback": "星桥论坛现在没有新的帖子。",
  "forum_unavailable_fallback": "星桥论坛暂时维护中..."
}
```

These fragments theme the visible and model-visible context. They do not rename
legacy internal IDs such as `cc98` and `dingtalk`, because those still appear in
WebSocket payloads, Redis keys, save data, and compatibility tests.

## Current Loader Defaults

- `SIMULATOR_THEME` selects the theme and defaults to `zju`.
- `SIMULATOR_LAB_ROOT` may override automatic lab-root discovery.
- `SIMULATOR_WORLD_DIR` may point directly at a world directory for one-off
  checks.
- `SIMULATOR_FRONTEND_STAT_OUTPUT` may override the generated TypeScript stat
  metadata destination.
- `sync_theme_metadata.py` generates `theme.generated.ts` for frontend shell
  copy and storage metadata.
- `validate_world_data.py` validates `theme.json`, `story.json`,
  `prompts.json`, world data, and generated frontend metadata freshness for the
  active theme.

## Later Candidates

These are intentionally not required in the bootstrap:

- `prologue`
- `ending_text`
- `admin_labels`
- `default_models`
- `route_titles`
- `legal_links`
