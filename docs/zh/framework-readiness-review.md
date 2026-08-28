# Beta 就绪审查

esimu `0.3.0b1` 是下一版源码候选。已发布的 `0.2.0b5` 已通过 TestPyPI 和独立
示例仓验收；0.3 在下一次发布门禁前补齐运行时闭环和安装后作者命令。

当前已具备强类型 core、版本化主题/状态/协议、自包含 `esimu new`、安装后作者
CLI、严格主题校验、可选 AI、Vue/Pinia Starter、非阻塞内容任务、自动事件/私聊、
冷却、声明式成就、Game Over、有序保存退出、SQLite 重启恢复、release smoke
和 Zensical 0.0.57 双语文档。

发布 0.3 前仍需：推送候选、通过 clean-checkout CI、在外部示例验证 wheel，并
验证不可覆盖的 TestPyPI 候选后再创建最终标签。

运行时多主题、生产账号、分布式持久化、独立 npm 包和稳定 1.0 保证不属于
本 Beta。具体边界见 Beta 支持策略与发布策略。
