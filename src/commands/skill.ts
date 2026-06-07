import * as fs from "node:fs";
import * as path from "node:path";
import { Command } from "commander";

const SKILL_MD = `---
name: esimu-maker
description: Design and generate browser-based Chinese text simulator games using the esimu YAML format. Use when the user wants to create a text adventure, interactive story game, or text-based simulator. Trigger when user mentions "文字游戏", "文字模拟器", "交互小说", "text adventure game", "make a game", or similar requests.
---

# esimu-maker

You are an expert game designer specializing in **esimu**, a CLI tool that generates browser-based Chinese text simulator games from YAML configuration files.

Your job: help the user design a complete, playable text simulator game. Write YAML config files that \`esimu build\` compiles into a standalone HTML game.

## How esimu works

esimu reads a \`game.yml\` file and optional Markdown event files, then generates a complete browser game:
- \`esimu init\` — scaffold a new game project
- \`esimu build\` — compile game.yml into \`dist/\` (HTML + CSS + JS)
- \`esimu serve\` — in-memory dev server with hot reload

The user doesn't need esimu installed — you only need to write valid \`game.yml\` and event \`.md\` files. The user can build later.

## Game design workflow

### Phase 1: Understand the vision
Ask the user:
1. **Theme & setting** — What kind of story? (fantasy, sci-fi, romance, survival, school life, historical, etc.)
2. **Core stats** — What numbers matter? (HP, money, reputation, skills, relationships, etc.)
3. **Length** — How many events / how long should a playthrough be?
4. **Endings** — How many? What determines them?

### Phase 2: Design the stat system
Design stats that serve the narrative. Each stat needs:
- \`name\` — Chinese display name
- \`min\` / \`max\` — bounds
- \`default\` — starting value

Example:
\`\`\`yaml
stats:
  hp:
    name: 生命值
    min: 0
    max: 100
    default: 100
  reputation:
    name: 声望
    min: 0
    max: 100
    default: 10
  gold:
    name: 金币
    min: 0
    max: 9999
    default: 50
\`\`\`

**Character creation:** define \`total_points\` and \`assignable\` (which stats the player can allocate points to at the start).

### Phase 3: Design the event graph
Events are nodes in a directed graph. Each event has:
- \`id\` — unique identifier (must have a \`start\` event as entry point)
- \`title\` — display title
- \`description\` — inline text OR \`descriptionFile\` — path to a Markdown file
- \`choices\` — array of choices, each with:
  - \`text\` — choice label
  - \`next_event\` — target event ID (use \`ending_xxx\` to trigger ending evaluation)
  - \`condition\` (optional) — stat thresholds to show this choice, e.g. \`{ strength: 8 }\`
  - \`effects\` (optional) — stat changes when chosen, e.g. \`{ hp: -10, gold: 50 }\`

**Naming convention:** use \`snake_case\` for event IDs. Ending-targeting \`next_event\` values should start with \`ending_\`.

### Phase 4: Design endings
Endings are evaluated when the player reaches a \`next_event: ending_xxx\` target. The engine checks conditions in order — first match wins. Must include one \`default: true\` ending as fallback.

\`\`\`yaml
endings:
  - condition:
      reputation: 80
    title: 万人敬仰
    description: 你的善名远扬，百姓为你立碑颂德。
  - condition:
      gold: 1000
    title: 富甲一方
    description: 你积累了惊人财富，成为商界传奇。
  - default: true
    title: 平凡一生
    description: 你的故事到此结束。
\`\`\`

## Critical rules

### Avoid dead-end events
**Every event MUST have at least one choice with NO condition** — a fallback the player can always take. If all choices have conditions and none are met, the game engine shows a game-over screen ("前路已尽").

### Ending condition design
- Ending conditions are checked EVERY TIME a choice is made (not just at ending events).
- Make ending thresholds HIGHER than starting stats. If a player starts with hp=100, \`hp: 50\` as an ending condition fires immediately.
- Use \`condition: {}\` sparingly — it always matches, so the first such ending always fires.

### Stat effects
- Effects are deltas: \`hp: -10\` subtracts 10, \`gold: 50\` adds 50.
- Players rarely see explicit numbers during gameplay — use effects sparingly and only where they create meaningful divergence.

### Balance
- Start stats so that no ending fires immediately.
- Give the point-buy system meaningful trade-offs (if you have \`strength\` and \`intelligence\`, the player should feel the tension of choosing one over the other).
- Include at least 8-15 events for a satisfying experience.

## File organization

For complex games with long event descriptions, use \`descriptionFile\`:
\`\`\`yaml
events:
  - id: forest
    title: 幽暗森林
    descriptionFile: events/forest.md
    choices:
      - text: 前进
        next_event: deep_forest
\`\`\`

Event Markdown files support full Markdown syntax (headings, lists, blockquotes, bold, italic).

## Output format

When asked to create a game:

1. First, describe the game concept in 2-3 sentences and confirm with the user
2. Write the complete \`game.yml\` with all stats, events, and endings
3. For events with long descriptions, create separate \`events/*.md\` files
4. Remind the user they can run \`esimu build\` and \`esimu serve\` to play

## Reference documentation

The \`references/\` directory contains:
- \`game-yml-schema.md\` — complete field reference for game.yml
- \`design-guide.md\` — narrative design patterns, balancing, and best practices

The \`assets/\` directory contains ready-to-use template \`.yml\` files you can adapt or reference.

Consult these references when you need detailed schema information or design inspiration.
`;

const SCHEMA_REFERENCE = `# game.yml 完整字段参考

## 顶层字段

| 字段 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| \`title\` | string | ✅ | 游戏标题 |
| \`description\` | string | ✅ | 游戏简介 |
| \`css\` | string | ❌ | 自定义 CSS 文件路径（相对于配置文件目录） |
| \`stats\` | object | ✅ | 数值系统定义 |
| \`character_creation\` | object | ✅ | 角色创建规则 |
| \`events\` | array | ✅ | 事件列表 |
| \`endings\` | array | ✅ | 结局列表 |

## stats

每个数值键名映射到一个对象：

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| \`name\` | string | 中文显示名称 |
| \`min\` | number | 最小值（数值不会低于此值） |
| \`max\` | number | 最大值（数值不会超过此值） |
| \`default\` | number | 初始值 |

## character_creation

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| \`total_points\` | number | 可分配点数上限 |
| \`assignable\` | string[] | 可分配数值的键名列表（必须是 stats 中已定义的键） |

## events[]

每个事件：

| 字段 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| \`id\` | string | ✅ | 唯一标识（必须有一个 id 为 \`start\` 的事件作为入口） |
| \`title\` | string | ✅ | 事件标题 |
| \`description\` | string | ❌ | 事件描述文本（与 descriptionFile 可同时使用） |
| \`descriptionFile\` | string | ❌ | 外部 Markdown 文件路径（相对于配置文件目录） |
| \`choices\` | array | ✅ | 选项列表（至少一个） |

### choices[] 每个选项：

| 字段 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| \`text\` | string | ✅ | 选项文字 |
| \`next_event\` | string | ✅ | 目标事件 ID（以 \`ending_\` 开头触发结局判定） |
| \`condition\` | object | ❌ | 显示条件，如 \`{ strength: 8 }\` 表示力量≥8 |
| \`effects\` | object | ❌ | 数值变化，如 \`{ hp: -10, gold: 50 }\` |

## endings[]

每个结局：

| 字段 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| \`title\` | string | ✅ | 结局标题 |
| \`description\` | string | ✅ | 结局描述 |
| \`condition\` | object | ❌ | 触发条件（非默认结局需要） |
| \`default\` | boolean | ❌ | 是否为默认结局（至少需要一个，兜底用） |

结局判定逻辑：按顺序检查每个非默认结局的 condition，第一个满足的命中。都不满足则使用 default 结局。

## 条件系统

- **选项条件** — 玩家数值满足条件时选项才可交互（不满足的选项直接不显示）
- **结局条件** — 每次选择后都会检查；满足某个结局条件时触发对应结局
- **空条件** — \`condition: {}\` 始终满足，慎用

## 自定义 CSS

在 game.yml 中通过 \`css\` 字段指定自定义样式表路径，完全替换自动生成的样式。默认样式使用 CSS 自定义属性，可通过覆盖以下变量轻松换肤：

\`\`\`css
:root {
  --bg: #1a1a2e;
  --surface: #16213e;
  --surface-alt: #0f3460;
  --text: #e0e0e0;
  --text-muted: #a0a0b0;
  --accent: #e94560;
  --border: #0f3460;
}
\`\`\`
`;

const DESIGN_GUIDE = `# 游戏设计指南

## 叙事分支模式

### 线性 (Linear)
A → B → C → D → ending。适合教程或短篇。简单可控。

### 中心辐射 (Hub & Spoke)
一个中心事件（如"城镇广场"）连接多个分支事件，完成后返回中心。适合开放式探索。

### 分支树 (Branching Tree)
每次选择走向不同分支，不同分支之间可以交汇（网状）或保持分离。重玩价值高。

### 选通内容 (Gated Content)
某些选项需要满足数值条件才可交互。例如：
- "破门而入" 需要 \`strength >= 10\`
- "施展魔法" 需要 \`mana >= 50\`
- "说服守卫" 需要 \`charisma >= 8\`

## 数值设计原则

### 起点与终点
- 初始数值应使所有结局条件在开局都**不满足**
- 角色创建的点数分配应创造有意义的取舍（力量 vs 智力，财富 vs 声望）
- 不要让某个属性成为"废属性"——确保每个属性都在至少一个选项条件或结局条件中被使用

### 事件中的数值变化
- 每次选择的效果变化建议在 1-5 之间（小属性）或 10-30 之间（大属性如 HP）
- 负面效果增加决策重量：\`hp: -10\` 让玩家三思
- 让效果可被感知——如果金币+5 永远不够买任何东西，那它就是无意义的设计

### 结局条件阈值
- 阈值应**明显高于初始值**。如果力量初始=5，结局条件设 \`strength: 8\` 确保了玩家需要做出选择或经历事件才能达到。
- 不要用 \`condition: {}\` 除非该结局只通过 \`next_event: ending_xxx\` 显式路由到达

## 避免常见陷阱

### 死胡同事件
**每个事件至少有一个无条件选项。** 如果一个事件的所有选项都有条件，而玩家都不满足，游戏会显示"前路已尽"并结束。

### 过早结局
结局条件在**每次选择后**都会检查。确保初始数值不满足任何结局条件。

### 无法到达的事件
确保每个事件都有一条从 \`start\` 出发的路径可达。用 \`esimu graph\` 可视化检查。

### 无限循环
避免事件之间形成永不终结的循环。至少一条路径应通向结局。

## 事件描述最佳实践

### 内联 vs 文件
- 短描述（1-2句）→ 使用 \`description\` 内联写在 game.yml 中
- 长描述（多段、列表、引用）→ 使用 \`descriptionFile\` 引用外部 .md 文件

### Markdown 在事件描述中的用法
Markdown 被渲染为 HTML。支持：
- **加粗**、*斜体*
- 无序列表和有序列表
- 引用块
- 标题（h1-h3）
- 代码块

### 写作风格
- 使用第二人称"你"让玩家沉浸
- 简洁有力——2-4句话的选项提示效果最好
- 在选择之间留下悬念，而非在每个事件中揭示所有信息
- 中文写作，保持沉浸感

## 游戏长度建议

| 体验 | 事件数 | 结局数 | 预计游玩时间 |
| :--- | :--- | :--- | :--- |
| 极简 | 5-8 | 2-3 | 2-5 分钟 |
| 短篇 | 8-15 | 3-5 | 5-10 分钟 |
| 中篇 | 15-30 | 5-8 | 10-20 分钟 |
| 长篇 | 30+ | 8+ | 20+ 分钟 |
`;

function scaffoldSkill(cwd: string, force: boolean) {
  const skillDir = path.join(cwd, "esimu-maker");
  const refsDir = path.join(skillDir, "references");
  const assetsDir = path.join(skillDir, "assets");

  if (fs.existsSync(skillDir) && !force) {
    throw new Error(
      "esimu-maker/ 目录已存在。使用 --force 选项覆盖，或手动删除后重试。"
    );
  }

  // Create directories
  fs.mkdirSync(skillDir, { recursive: true });
  fs.mkdirSync(refsDir, { recursive: true });
  fs.mkdirSync(assetsDir, { recursive: true });

  // Write SKILL.md
  fs.writeFileSync(path.join(skillDir, "SKILL.md"), SKILL_MD, "utf-8");
  console.log("✓ 已创建 SKILL.md");

  // Write references
  fs.writeFileSync(path.join(refsDir, "game-yml-schema.md"), SCHEMA_REFERENCE, "utf-8");
  console.log("✓ 已创建 references/game-yml-schema.md");

  fs.writeFileSync(path.join(refsDir, "design-guide.md"), DESIGN_GUIDE, "utf-8");
  console.log("✓ 已创建 references/design-guide.md");

  // Copy template assets
  const templatesDir = path.join(import.meta.dir, "..", "templates", "files");
  const assets = ["default.yml", "cultivation.yml", "survival.yml", "fantasy.yml", "example-event.md"];
  for (const asset of assets) {
    const src = path.join(templatesDir, asset);
    const dst = path.join(assetsDir, asset);
    if (fs.existsSync(src)) {
      fs.copyFileSync(src, dst);
      console.log(`✓ 已复制 assets/${asset}`);
    }
  }
}

export const skillCommand = new Command("skill")
  .description("生成 esimu-maker agent skill（Claude Code 用）")
  .option("-f, --force", "覆盖已存在的目录")
  .action((options) => {
    const cwd = process.cwd();
    const force = options.force ?? false;

    try {
      scaffoldSkill(cwd, force);
    } catch (err) {
      console.error((err as Error).message);
      process.exit(1);
    }

    console.log("\nesimu-maker skill 已生成！安装方式：");
    console.log("  将 esimu-maker/ 目录复制到 ~/.claude/skills/ 下即可使用");
    console.log("\n安装后，在 Claude Code 中对 AI 说「帮我做一个修仙游戏」即可触发此 skill。");
  });
