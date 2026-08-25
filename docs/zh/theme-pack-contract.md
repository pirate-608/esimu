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
    cc98_library.json
    characters.json
    graduation_comments.json
    courses/
      <major_abbr>.json
```

`assets/` 可以很小，但 `story.json` 引用的图片必须存在于主题 assets 中。主题校验不再从 ZJU reference frontend 借图片。

## 校验入口

从 `packages/esimu-core/` 运行：

```powershell
$env:ESIMU_THEME='<theme_id>'
python scripts\validate_world_data.py
```

`validate_world_data.py` 会检查：

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

它不会重命名 `cc98` 和 `dingtalk` 这类兼容 ID。

## world 数据

`stat_definitions.json` 是属性事实源。新增属性后，应运行 stat metadata 同步和 world validation。

`items.json` 的 effects 字段必须被属性注册表的 `allow_item_effect` 允许。

`event_library.json` 的 effects 字段必须被属性注册表的 `allow_event_effect` 允许。

`majors.json` 中每个专业/角色都应有对应的 `courses/<abbr>.json`。

`cc98_library.json` 暂时保留兼容文件名，但主题可通过 `theme.json` 把可见名改成任何论坛/社区名称。

## 新主题清单

1. 用 `new_project.py` 生成项目，或复制 `themes/demo-campus/`。
2. 修改 `theme.json`，尤其是 `theme_id` 和 `storage.prefix`。
3. 修改 `story.json` 和图片资源。
4. 修改 `prompts.json`。
5. 替换 `majors.json` 和 `courses/*.json`。
6. 替换属性、道具、成就、事件、论坛、角色和毕业评价。
7. 运行 `validate_world_data.py`。
8. 如需驱动前端，重新生成 theme/story/stat metadata。
