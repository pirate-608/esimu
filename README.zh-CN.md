# esimu

[English](README.md) | [简体中文](README.zh-CN.md)

esimu 是面向校园、职业和人生叙事模拟器的主题驱动框架。Beta 的正式形态是：

```text
esimu-core + 生成的 Starter 应用 + 单一主题包
```

当前公开 PyPI 版本 `esimu-core 0.4.0b2` 提供强类型世界数据加载、主题校验、游戏规则、运行时
payload、可选 AI 生成和自包含项目 CLI。生成的 Starter 包含 Vue 3/Pinia
控制台、FastAPI/WebSocket、实时 Tick、事件、论坛、私聊、道具、学期结算、
冷却、声明式成就、自动内容、区分失败/毕业的结局和 SQLite 持久化。

## 快速开始

从 PyPI 安装精确 Beta：

```powershell
python -m pip install "esimu-core[ai]==0.4.0b2"
esimu new D:\projects\zju-lite `
  --project-name "ZJUers Simulator Lite" `
  --theme-id zju-lite `
  --institution "浙江大学"
cd D:\projects\zju-lite
python -m pip install -r apps\starter\backend\requirements.txt
esimu validate --root . --theme zju-lite
esimu doctor --root . --theme zju-lite
esimu dev --root . --theme zju-lite
```

在另一个终端请求同步并完整重启：

```powershell
esimu reload --root . --theme zju-lite
```

构建生产前端：

```powershell
esimu build --root . --theme zju-lite
```

访问 `http://127.0.0.1:15175`。

需要完全中性的模板时，给 `esimu new` 增加 `--source-theme demo-campus`。

## 仓库结构

```text
packages/esimu-core/    可安装 Python 核心与 CLI
apps/starter/           标准 FastAPI + Vue Starter
themes/demo-campus/     中性的两学期示例主题
themes/zju-simplified/  默认的浙大模拟器精简适配主题
templates/              生成项目的交接模板
docs/                   中英文 Zensical 文档站
```

旧 ZJU 提取参考已封存在 `esimu-lab-final` tag，不属于正式 Beta 主分支。
ZJUers Simulator 始终是独立产品，不是 esimu 的运行时依赖。

## 开发检查

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pytest packages\esimu-core\tests
python -m pytest apps\starter\backend\tests
python packages\esimu-core\scripts\sync_scaffold_bundle.py
zensical build
```

前端执行 `corepack pnpm typecheck`、`corepack pnpm test` 和
`corepack pnpm build`。更多内容见中文快速开始、CLI 参考、主题契约、架构、
Beta 支持策略和发布策略文档。

## 兼容性

- 包名：`esimu-core`
- Python 命名空间：`esimu_core`
- CLI：`esimu new/validate/doctor/inspect/sync/add/dev/reload/build/version`
- 主题契约版本：`1`
- Starter 状态与 WebSocket 协议版本：`2`；旧状态自动迁移并兼容 v1 客户端
- 许可证：MIT

本 Beta 不承诺运行时多主题、生产账号系统、Redis/PostgreSQL adapter 或独立
npm 组件包。
