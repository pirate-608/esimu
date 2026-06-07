# esimu - Easy Simulator Generator

## 项目简介

esimu 是一个命令行工具，通过 YAML 配置文件生成基于浏览器的文字模拟器游戏。

## 核心理念

编写配置 → 一行命令 → 可玩的 HTML 游戏

## 技术栈

- TypeScript + Bun
- CLI: commander
- YAML 解析: js-yaml
- Markdown 解析: marked
- 文件监听: chokidar
- 本地服务器: Bun.serve
- 发布: 二进制（GitHub Releases）

## Roadmap

### ✅ Phase 1: 核心构建能力

目标：能从 YAML 配置文件生成可玩的 HTML 游戏，输出到 dist 目录

- [x] 项目初始化，TypeScript + Bun 配置
- [x] 命令结构搭建（init, build, serve）
- [x] init 命令 — 脚手架生成（game.yml + events/ + .gitignore），支持 --force
- [x] build 命令 — YAML 加载、校验、descriptionFile 支持、HTML/CSS/JS 生成
- [x] 游戏引擎 — 状态管理、角色创建（点数分配）、事件调度、条件系统、结局判定
- [x] serve 命令 — 本地预览服务器，自动打开浏览器

### ✅ Phase 2: 交互式配置增强

目标：提升配置体验，支持更多自定义

- [x] init --interactive — 交互式问答生成自定义配置
- [x] init --template — 4 个预设模板（默认、修仙、末日、龙与地牢）
- [x] build --watch — 监听文件变化自动重新构建
- [x] serve — 热更新（内存构建 + SSE 推送刷新，无需提前 build）
- [x] build --output — 自定义输出目录

### ✅ Phase 3: 体验优化与发布

目标：完善工具，正式发布

- [x] 错误处理 — 中文错误提示，指明具体字段和期望类型
- [x] 4 个官方预设模板（默认、修仙模拟器、末日求生、龙与地牢）
- [x] serve 内存构建 + SSE 热更新（类 mkdocs serve 体验）
- [x] CSS 自定义属性（`--bg`、`--accent` 等），支持 game.yml 中 `css` 字段覆写样式
- [x] README 完整文档（安装、快速开始、命令参考、配置格式、模板说明）
- [x] 模板文件抽离（`src/templates/files/` 下的独立 .yml/.md 文件）
- [x] 生成器模块抽离（`src/generator.ts` 复用 HTML/CSS/JS 生成逻辑）
- [x] 二进制发布 — `bun build --compile` 跨平台编译
  - [x] Linux x64
  - [x] macOS arm64
  - [x] Windows x64
- [x] GitHub Actions 自动发布（`.github/workflows/release.yml`，推送 tag 触发）
- [ ] ~~npm 包发布~~ — 已放弃，仅通过二进制分发

## 工作区项目结构

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

执行 `esimu serve` 后：

- 在内存中直接构建，不写入磁盘
- 启动本地服务器，默认 http://localhost:3000
- 自动打开浏览器预览游戏
- 监听文件变化，自动重建并通过 SSE 刷新浏览器

## 命令概览

| 命令 | 说明 | 示例 |
| :--- | :--- | :--- |
| `esimu init` | 在当前目录生成游戏脚手架 | `esimu init --template cultivation` |
| `esimu build` | 根据 game.yml 构建游戏到 dist/ | `esimu build --watch` |
| `esimu serve` | 内存构建 + 热更新预览 | `esimu serve --port 8080` |
