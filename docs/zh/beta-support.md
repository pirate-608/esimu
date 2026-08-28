# Beta 支持策略

`esimu-core 0.3.0b2` 面向单主题叙事模拟器原型。当前仅在 `main` 准备，完成
独立发布验收前不会推送 PyPI。

本 Beta 支持 Python 3.11–3.13、单部署单主题、主题 schema v1、状态和
WebSocket 协议 v2、v1 状态迁移与 v1 客户端接入、Vue/Pinia Starter、单机
SQLite 持久化、安装后作者 CLI，以及带本地降级的可选 OpenAI-compatible
内容生成。

本版本不承诺运行时多主题、生产账号系统、Redis/PostgreSQL、水平扩展、独立
npm 组件包，或任意未发布提取快照的兼容性。Beta 阶段的破坏性变更必须提升次
版本并提供迁移说明。
