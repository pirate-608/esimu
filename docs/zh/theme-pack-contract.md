# 主题包契约

主题包是 esimu 的产品边界：一个主题包拥有一个模拟器部署的世界、叙事、prompt 和资源。

## 必需目录

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
    forum_library.json
    characters.json
    graduation_comments.json
    courses/
      <major_abbr>.json
```

`assets/` 可以很小，但 `story.json` 引用的图片必须存在于主题 assets 中。

## 校验入口

下游项目的标准命令：

```powershell
esimu validate --root . --theme <theme_id>
```

维护者脚本 `packages/esimu-core/scripts/validate_world_data.py` 调用同一校验器。
校验内容包括：

- 必需文件是否存在。
- `theme.json`、`story.json`、`prompts.json`、`stat_definitions.json` 的结构。
- 专业/课程、成就、事件库、论坛库、角色、道具、平衡和毕业评价。
- 道具/事件 effects 是否被属性注册表允许。
- story 图片是否存在。
- 默认主题的前端 generated metadata 是否新鲜。

## theme.json

`theme.json` 只放短结构信息：

- `theme_id`：稳定小写 ID。
- `display_name`：公开显示名。
- `terms`：至少包含 `campus`、`forum`、`messenger`、`player`、`semester`、`course`、`item`。
- `storage.prefix`：浏览器存储命名空间。

不要把长篇序章、prompt 模板、道具描述或课程数据放进 `theme.json`。

## story.json

`story.json` 放长叙事：

- 首访序章 dedication lines。
- 日记页和场景图片映射。
- 失败结局文案。
- 毕业结局文案。
- GPA 分支毕业标题。
- 毕业总结 fallback。
- 结局背景图片文件名。

图片字段是文件名，不是路径；路径穿越和子目录会被拒绝。

## prompts.json

`prompts.json` 放模型可见上下文：

- 场景背景。
- 论坛与私信名称。
- 论坛批量生成说明。
- 随机事件说明。
- 私聊说明。
- 玩家身份模板。
- 毕业总结说明。

Starter 的公开 action 始终使用中性的 `forum`、`messenger` ID。

## world 数据

`stat_definitions.json` 是属性事实源。新增属性后，应运行 stat metadata 同步和 world validation。

`items.json` 的 effects 字段必须被属性注册表的 `allow_item_effect` 允许。

`event_library.json` 的 effects 字段必须被属性注册表的 `allow_event_effect` 允许。
每个事件至少提供两个选项。

`majors.json` 中每个专业/角色都应有对应的 `courses/<abbr>.json`。

`forum_library.json` 是中性的本地论坛内容库，主题可通过 `theme.json` 修改可见名称。

`characters.json` 的可回复角色使用中性 ID：`roommate`、`classmate`、`friend`、
`teaching_assistant`、`teacher` 和 `crush`。

`achievements.json` 中的 `condition` 可自动解锁成就。条件必须只包含一个非空
`all` 或 `any` 数组；谓词格式为 `scope/key/op/value`。scope 支持
`stat/action/session`，op 支持 `gte/gt/lte/lt/eq`。session 指标支持
`semester_idx`、`completed_terms`、`failed_count`、`term_gpa` 和
`cumulative_gpa`。没有 condition 的旧条目只展示或由下游手动解锁。

## 新主题清单

1. 用 `new_project.py` 生成项目，或复制 `themes/demo-campus/`。
2. 修改 `theme.json`，尤其是 `theme_id` 和 `storage.prefix`。
3. 修改 `story.json` 和图片资源。
4. 修改 `prompts.json`。
5. 替换 `majors.json` 和 `courses/*.json`。
6. 替换属性、道具、成就、事件、论坛、角色和毕业评价。
7. 运行 `esimu validate --root . --theme <theme_id>` 和 `esimu doctor`。
8. 运行 `esimu sync --root . --theme <theme_id> --write` 更新前端 metadata。
9. 使用 `esimu add ...` 预览内容；显式 `--write` 才写入，验证失败自动回滚。
