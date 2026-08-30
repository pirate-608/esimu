# Agent 交接

先阅读根目录 `AGENTS.md`，只在独立 esimu 仓库内工作。Core 改动属于
`packages/esimu-core`，adapter/UI 属于 `apps/starter`，可见内容属于
`themes/<theme_id>`。

交接前运行 core/Starter 测试、Ruff、前端 type/test/build、主题校验、scaffold
同步检查、Zensical build 和 release smoke。公共命令或契约变化时同步中英文文档。

文档依赖固定在 `docs/requirements.txt`，当前工具链是 Zensical 0.0.57。
`mkdocs.yml` 导航不得引用已删除/归档页面，每次文档改动后都运行 strict build。

当前源码候选是 `0.4.0b2`，最新发布版是 `0.3.0b2`；主题 schema v1 与状态/协议
v2 不变。默认 source theme 是 `zju-simplified`，中性替代是 `demo-campus`。
优先使用安装后的 `esimu doctor/inspect/sync/add/dev/reload/build`；源码脚本只是
兼容 wrapper。事件、论坛和私聊的慢 AI 工作必须在 session lock 外、通过 target
去重后台任务执行。
