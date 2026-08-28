# 架构

esimu 分为三个明确层次：

```text
主题包 -> esimu-core -> 应用适配器
```

`themes/<theme_id>` 管理可见名词、故事、Prompt、资源、属性、平衡、道具、
专业、课程、事件、论坛、角色、成就和毕业文案。一个部署通过 `ESIMU_THEME`
选择一个主题。

`packages/esimu-core/esimu_core` 只包含可复用 Python 逻辑：world loader 与
校验、domain 成就/效果/学期规则、runtime 自动调度与任务编排、lifecycle 状态
构造、中性的 content 契约、可选 AI、安装后 authoring CLI 和 wheel 内项目脚手架。
Core 不依赖 FastAPI、SQLite、Redis、
SQLAlchemy、WebSocket 或 Vue。

`apps/starter/backend` 负责 FastAPI、WebSocket、实时 Tick、串行发送和异步
SQLite 持久化；慢内容生成在 session lock 外按 target 去重执行。
`apps/starter/frontend` 是 Vue 3/Pinia 完整控制台。Starter 公开使用
`forum`、`messenger` 等中性 action；主题 schema 为 v1，状态和协议为 v2，
并迁移 v1 状态、接受 v1 客户端。
