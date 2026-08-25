# 架构

esimu 分为三个明确层次：

```text
主题包 -> esimu-core -> 应用适配器
```

`themes/<theme_id>` 管理可见名词、故事、Prompt、资源、属性、平衡、道具、
专业、课程、事件、论坛、角色、成就和毕业文案。一个部署通过 `ESIMU_THEME`
选择一个主题。

`packages/esimu-core/esimu_core` 只包含可复用 Python 逻辑：world loader 与
校验、domain 规则、runtime 编排、lifecycle 状态构造、中性的 content 契约、
可选 AI 和 wheel 内项目脚手架。Core 不依赖 FastAPI、SQLite、Redis、
SQLAlchemy、WebSocket 或 Vue。

`apps/starter/backend` 负责 FastAPI、WebSocket、实时 Tick、串行发送和异步
SQLite 持久化；`apps/starter/frontend` 是 Vue 3/Pinia 完整控制台。Starter
公开使用 `forum`、`messenger` 等中性 action，并携带版本 1 的主题、状态和
协议版本。
