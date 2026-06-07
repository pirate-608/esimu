# esimu — Easy Simulator Generator

通过 YAML 配置文件生成基于浏览器的文字模拟器游戏。

> 编写配置 → 一行命令 → 可玩的 HTML 游戏

## 安装

### 一键安装（推荐）

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/pirate-608/esimu/main/scripts/install.ps1 | iex
```

或手动指定仓库：

```powershell
.\install.ps1 -Repo pirate-608/esimu
```

**Linux / macOS:**

```bash
curl -fsSL https://raw.githubusercontent.com/pirate-608/esimu/main/scripts/install.sh | bash
```

或手动指定仓库：

```bash
REPO=pirate-608/esimu bash install.sh
```

脚本会自动下载最新版本，解压并安装到 `~/.local/bin`。

### 手动安装

从 [GitHub Releases](https://github.com/pirate-608/esimu/releases) 下载对应平台的压缩包：

| 平台 | 文件 |
| :--- | :--- |
| Windows x64 | `esimu-windows-x64.zip` |
| macOS arm64 | `esimu-darwin-arm64.tar.gz` |
| Linux x64 | `esimu-linux-x64.tar.gz` |

解压后将可执行文件放入 PATH 目录（如 `~/.local/bin`），Linux/macOS 需 `chmod +x`。

> 也可以从源码运行：`git clone` 后使用 `bun run src/cli.ts -- <command>` 进行开发调试。

## 快速开始

```bash
# 1. 创建新项目
mkdir my-game && cd my-game
esimu init

# 2. 启动开发服务器（内存构建 + 热重载）
esimu serve

# 3. 构建生产版本（可选，输出到 dist/）
esimu build
```

浏览器会自动打开 `http://localhost:3000`，即可开始游玩。

## 命令

### `esimu init`

在当前目录生成游戏项目脚手架。

| 选项 | 说明 |
| :--- | :--- |
| `--force, -f` | 覆盖已存在的文件 |
| `--interactive, -i` | 交互式问答生成自定义配置 |
| `--template <name>, -t <name>` | 使用预设模板（见下方模板列表） |

```bash
esimu init                          # 使用默认模板
esimu init --interactive            # 交互式创建
esimu init --template cultivation   # 使用修仙模板
```

### `esimu build`

根据 `game.yml` 构建游戏到 `dist/` 目录。

| 选项 | 说明 |
| :--- | :--- |
| `--config <path>, -c <path>` | 指定配置文件路径（默认 `game.yml`） |
| `--output <dir>, -o <dir>` | 指定输出目录（默认 `dist`） |
| `--watch, -w` | 监听文件变化，自动重新构建 |

```bash
esimu build
esimu build --config my-game.yml --output out
esimu build --watch
```

### `esimu serve`

启动本地预览服务器。

无需预先执行 `build`，服务器会在内存中直接构建并推送至浏览器。

| 选项 | 说明 |
| :--- | :--- |
| `--port <number>, -p <number>` | 指定端口（默认 `3000`） |
| `--config <path>, -c <path>` | 指定配置文件路径（默认 `game.yml`） |
| `--no-open` | 不自动打开浏览器 |

```bash
esimu serve
esimu serve --port 8080
```

修改 `game.yml` 或 `events/` 中的文件后，服务器会自动重建并刷新浏览器。

### `esimu graph`

导出事件流程图为 Mermaid 图表，方便可视化游戏逻辑。

| 选项 | 说明 |
| :--- | :--- |
| `--config <path>, -c <path>` | 指定配置文件路径（默认 `game.yml`） |
| `--output <file>, -o <file>` | 输出到文件（默认打印到终端） |

```bash
esimu graph                    # 打印 Mermaid 图表到终端
esimu graph --output game.mmd  # 保存到文件
```

输出的 Mermaid 代码可直接粘贴到 [mermaid.live](https://mermaid.live) 或 GitHub Markdown 中渲染。

## 项目结构

执行 `esimu init` 后生成：

```
my-game/
├── .gitignore          # 忽略 dist、node_modules 等
├── game.yml            # 游戏主配置文件
└── events/             # 事件描述 Markdown 文件目录
    └── example.md
```

执行 `esimu build` 后生成：

```
my-game/
├── .gitignore
├── game.yml
├── events/
│   └── ...
└── dist/               # 构建输出目录
    ├── index.html
    ├── css/
    │   └── style.css
    └── js/
        └── game.js
```

## 配置文件格式 (game.yml)

```yaml
title: 游戏标题
description: 游戏描述
css: custom/style.css               # 可选，自定义 CSS 文件路径（相对于配置文件目录）

stats:
  数值键名:
    name: 显示名称
    min: 0
    max: 100
    default: 0

character_creation:
  total_points: 15
  assignable:
    - 可分配的数值键名

events:
  - id: start                          # 必须有一个 id 为 "start" 的事件作为入口
    title: 事件标题
    description: 事件描述               # 可选，与 descriptionFile 可同时使用
    descriptionFile: events/xxx.md     # 可选，Markdown 文件路径（相对于配置文件目录）
    choices:
      - text: 选项文字
        condition:                     # 可选，显示该选项需要的条件
          数值键名: 阈值
        effects:                       # 可选，选择后应用的数值变化
          数值键名: 变化值
        next_event: 下一个事件id

endings:
  - condition:                         # 可选，触发该结局的条件
      数值键名: 阈值
    title: 结局标题
    description: 结局描述
  - default: true                      # 必须至少有一个默认结局
    title: 默认结局标题
    description: 默认结局描述
```

### 条件系统

- **选项条件** (`choice.condition`)：玩家数值满足条件时，选项才可点击
- **结局条件** (`ending.condition`)：玩家数值满足条件时触发对应结局
- **默认结局** (`ending.default: true`)：无其他结局匹配时触发

### 描述文件

事件可以通过 `descriptionFile` 引用外部 Markdown 文件：

```yaml
events:
  - id: forest
    title: 幽暗森林
    descriptionFile: events/forest.md
    choices:
      - text: 前进
        next_event: deep_forest
```

文件路径相对于 `game.yml` 所在目录。Markdown 会被自动转换为 HTML。

## 预设模板

| 模板 | 命令 | 说明 |
| :--- | :--- | :--- |
| 默认模板 | `esimu init` | 一个简单的奇幻冒险故事 |
| 修仙模拟器 | `esimu init -t cultivation` | 从凡人到飞升的修仙之路 |
| 末日求生 | `esimu init -t survival` | 核战后废土世界的生存挑战 |
| 龙与地牢 | `esimu init -t fantasy` | 经典奇幻地牢探险 |

## 开发

```bash
# 安装依赖
bun install

# 开发模式运行
bun run src/cli.ts -- build

# 类型检查
bun run typecheck

# 构建当前平台二进制
bun run build

# 跨平台编译（需在 Linux 环境执行）
bun build src/cli.ts --compile --target=bun-linux-x64    --outfile dist/esimu
bun build src/cli.ts --compile --target=bun-darwin-arm64 --outfile dist/esimu
bun build src/cli.ts --compile --target=bun-windows-x64  --outfile dist/esimu.exe
```

发布流程：推送 `v*` 标签 → GitHub Actions 自动构建多平台二进制并创建 Release（`.github/workflows/release.yml`）。

技术栈：TypeScript + [Bun](https://bun.sh) · commander · js-yaml · marked · chokidar

## License

MIT
