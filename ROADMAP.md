# esimu - Easy Simulator Generator

## 项目简介

esimu 是一个命令行工具，通过 YAML 配置文件生成基于浏览器的文字模拟器游戏。

## 核心理念

编写配置 → 一行命令 → 可玩的 HTML 游戏

## 技术栈

- TypeScript + Bun
- CLI: commander
- YAML 解析: js-yaml
- Markdown 解析: marked 或内置简单转换
- 本地服务器: serve 或内置静态服务器
- 发布: npm / 二进制

## Roadmap

### Phase 1: 核心构建能力

目标：能从 YAML 配置文件生成可玩的 HTML 游戏，输出到 dist 目录

#### 1.1 项目基础
- [ ] 项目初始化，TypeScript + Bun 配置
- [ ] 目录结构搭建
- [ ] 依赖安装（commander, js-yaml, @types/bun, chokidar）

#### 1.2 CLI 框架
- [ ] 命令结构搭建（init, build, serve）
- [ ] 命令行参数解析
- [ ] 全局帮助信息

#### 1.3 init 命令 - 脚手架生成
- [ ] 在工作区目录生成初始项目结构
- [ ] 生成 .gitignore（排除 dist、node_modules 等）
- [ ] 生成 game.yml 默认配置模板
- [ ] 生成 events/ 目录及示例 Markdown 文件
- [ ] 支持 --force 选项覆盖已有文件

#### 1.4 build 命令 - 项目构建
- [ ] 默认读取工作区根目录的 game.yml
- [ ] 支持通过参数指定配置文件路径
- [ ] YAML 文件读取与解析
- [ ] 配置结构校验（必填字段、类型检查）
- [ ] descriptionFile 支持
  - [ ] 相对路径解析（相对于配置文件目录）
  - [ ] Markdown 文件读取
  - [ ] 文件不存在时的错误提示
  - [ ] description 与 descriptionFile 合并逻辑
- [ ] 友好的错误提示（哪个字段出错、期望什么类型）

#### 1.5 游戏模板生成
- [ ] 清空并重建 dist 目录
- [ ] index.html 主文件生成
- [ ] CSS 样式文件生成（css/style.css）
  - [ ] 响应式布局
  - [ ] 深色主题
  - [ ] 移动端适配
- [ ] JavaScript 游戏引擎生成（js/game.js）
  - [ ] 状态管理（数值系统的读取与更新）
  - [ ] 角色创建界面（可分配点数、总和限制）
  - [ ] 事件调度器（根据 next_event 跳转）
  - [ ] 选项处理与数值变化应用
  - [ ] 条件系统（选项显示条件、结局判定条件）
  - [ ] 结局判定与展示
- [ ] 输出目录结构：
  ```
  dist/
  ├── index.html
  ├── css/
  │   └── style.css
  └── js/
      └── game.js
  ```

#### 1.6 serve 命令 - 本地预览
- [ ] 启动本地静态文件服务器
- [ ] 默认端口 3000，支持 --port 参数配置
- [ ] 自动打开浏览器预览
- [ ] 监听文件变化并自动刷新（可选，Phase 3 完善）

#### 1.7 示例与文档
- [ ] init 生成的默认配置包含示例游戏
- [ ] 配置文件格式说明文档

**Phase 1 交付物**

```bash
# 初始化项目脚手架
esimu init

# 构建游戏
esimu build

# 启动本地预览
esimu serve
```

执行后生成完整的项目结构和可玩的 HTML 游戏。

### Phase 2: 交互式配置增强

目标：提升配置体验，支持更多自定义

- [ ] init 命令支持交互式问答生成自定义配置
  - [ ] 游戏基本信息（标题、描述）
  - [ ] 数值系统定义
  - [ ] 角色创建规则
  - [ ] 事件录入（支持后续编辑）
  - [ ] 结局定义
- [ ] init 命令支持 --template 参数选择预设模板
  - [ ] 修仙模拟器模板
  - [ ] 末日生存模板
  - [ ] 奇幻冒险模板
- [ ] build 命令支持 --watch 模式，文件变化自动重新构建
- [ ] serve 命令支持 --live 参数，开启热更新

**Phase 2 交付物**

```bash
# 交互式创建配置
esimu init --interactive

# 使用预设模板
esimu init --template cultivation

# 监听模式构建
esimu build --watch

# 带热更新的本地服务器
esimu serve --live
```

### Phase 3: 体验优化与发布

目标：完善工具，正式发布

- [ ] 错误处理全面优化，错误信息更友好
- [ ] 构建性能优化
- [ ] 提供 3+ 个官方预设模板
- [ ] serve 命令文件监听与热更新完善
- [ ] 支持自定义输出目录（build -o 参数）
- [ ] 完善 README 文档
  - [ ] 安装方式（npm -g / 二进制下载）
  - [ ] 快速开始（init → build → serve）
  - [ ] 项目结构说明
  - [ ] 配置文件完整说明
  - [ ] 预设模板说明
- [ ] npm 包发布（支持 -g 全局安装）
- [ ] 二进制文件打包（bun build --compile）
  - [ ] macOS (x64, arm64)
  - [ ] Linux (x64)
  - [ ] Windows (x64)
- [ ] 版本管理与更新日志

**Phase 3 交付物**

```bash
# npm 全局安装
npm install -g esimu
esimu init
esimu build
esimu serve

# 或使用 npx 直接运行
npx esimu init

# 二进制方式（下载后放入 PATH）
esimu init
```

## 工作区项目结构

执行 `esimu init` 后生成：

```
my-game/
├── .gitignore          # 忽略 dist、node_modules 等
├── game.yml            # 游戏主配置文件
└── events/             # 事件描述 Markdown 文件目录
    ├── example1.md
    └── example2.md
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

- 启动本地服务器，默认 http://localhost:3000
- 自动打开浏览器预览游戏

## 配置文件格式 (game.yml)

```yaml
title: 游戏标题
description: 游戏描述

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
  - id: 事件唯一标识
    title: 事件标题
    description: 事件描述（可选，与 descriptionFile 二选一或同时使用）
    descriptionFile: events/xxx.md（可选，相对于配置文件目录）
    choices:
      - text: 选项文字
        condition:  # 可选，显示该选项需要的条件
          数值键名: 阈值
        effects:
          数值键名: 变化值
        next_event: 下一个事件id

endings:
  - condition:
      数值键名: 阈值
    title: 结局标题
    description: 结局描述
  - default: true
    title: 默认结局标题
    description: 默认结局描述
```

## 命令概览

| 命令 | 说明 | 示例 |
| :--- | :--- | :--- |
| `esimu init` | 在当前目录生成游戏脚手架 | `esimu init` |
| `esimu build` | 根据 game.yml 构建游戏到 dist/ | `esimu build` |
| `esimu serve` | 启动本地预览服务器 | `esimu serve --port 8080` |

## 版本规划

| 版本 | 内容 | 时间预估 |
| :--- | :--- | :--- |
| v0.1.0 | Phase 1 完成（init, build, serve 基础功能） | 第 1 周 |
| v0.2.0 | Phase 2 完成（交互式配置、监听模式） | 第 2 周 |
| v1.0.0 | Phase 3 完成（正式发布、二进制分发） | 第 3-4 周 |