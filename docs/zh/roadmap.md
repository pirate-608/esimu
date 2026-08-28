# 路线图

esimu 是面向单主题叙事模拟器的独立主题驱动框架。本页记录当前产品里程碑，不再
把归档的代码提取任务当作现役 roadmap。

## 已完成里程碑

### 提取与独立

- 原始 ZJU 提取基线保存在 `esimu-lab-final`。
- esimu 已拥有独立仓库、包、文档站、许可证、CI 和发布 workflow；运行时不依赖
  ZJUers Simulator。
- `packages/esimu-core`、`apps/starter`、`themes/demo-campus` 分别是标准
  core、应用和主题边界。

### 公开 Beta 0.2

- `esimu-core 0.2.0b5` 已通过 PyPI 和 GitHub Release 发布。
- wheel 内 `esimu new` 可生成独立 FastAPI + Vue/Pinia 项目。
- 已建立主题 schema v1、SQLite、可选 AI、严格世界数据校验和外部生成项目验证。

### 0.3 运行时候选

- 状态与 WebSocket 协议升级到 v2，同时迁移 v1 状态并接受 v1 客户端。
- 持久化冷却、自动事件/私聊、声明式成就、Game Over、内容模式和有序保存退出
  补齐运行时闭环。
- 私聊采用玩家消息立即显示、NPC 后台生成的两阶段流程，并支持未读、联系人
  多样性/复用和三回复结算。
- 安装后的 `doctor/inspect/sync/add` 提供项目诊断和原子主题编辑。
- 标准 Starter 前端已覆盖全部候选行为。

## Phase 16：发布 0.3 Beta

- 推送候选提交并通过 clean-checkout matrix。
- 在 `esimu-beta-example` 验证 wheel、作者 CLI 和桌面/移动 Starter 流程。
- 发布不可覆盖的 TestPyPI 候选，修复外部安装问题后发布最终 `0.3.0b*`。
- 发布与代码一致的 Zensical 0.0.57 文档站。

完成标准：外部项目无需 esimu 源码 checkout，即可安装、生成模拟器、编辑和同步
主题、保存恢复状态并完成主题配置的游戏流程。

## Phase 17：Adapter 生态

- 定义可选生产身份和多存档扩展契约。
- 在下游证明至少一个 PostgreSQL 或 Redis `SessionStore`，不把依赖引入 core。
- 基于 `esimu add` 的 validator 和原子发布规则设计可选运营编辑器。
- 补充可观测性、备份、迁移和部署模式。

## Phase 18：复用与稳定

- 真实项目证明价值后，再决定是否发布独立 npm 组件包。
- 修改主题 schema v1 或协议 v2 前先提供迁移工具。
- 用多个非校园主题继续暴露隐藏领域名词。
- 定义从 Beta 兼容承诺走向稳定 1.0 的路径。

## 明确不做

- 单部署运行时多主题切换。
- 在 core 中引入 Redis、PostgreSQL、生产身份或 Admin 依赖。
- 把 ZJU 专有协议 ID 或产品文案重新带回 Starter。
