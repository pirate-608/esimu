# Starter 形态

当前决策：**新模拟器默认从 `apps/starter/` 开始，而不是直接复制 ZJU reference app。**

## 推荐路径

1. 创建或复制一个主题包。
2. 用 `esimu-core` 校验主题。
3. 从 `apps/starter/` 启动第一个可运行产品壳。
4. 优先通过 theme/story/prompt metadata 改名词和可见文案。
5. 只有在确实需要 reference 的存档、管理后台、Redis/PostgreSQL、向量检索或 legacy 兼容行为时，再复用 `apps/zju-reference/`。

## 为什么不默认复制 reference app

reference app 很有价值，因为它已经有：

- FastAPI 后端；
- WebSocket loop；
- 存档服务；
- Redis/PostgreSQL；
- 管理后台；
- 带 Redis 内容池和 pgvector 的完整 LLM 兼容 adapter；
- Vue 游戏控制台。

但它也很重，带有 ZJU 产品文案、DingTalk/CC98 兼容 ID、生产部署选择和大量围绕原游戏建立的测试。

新项目通常先需要“能跑起来”，再决定是否引入这些复杂能力。

## 文件选择原则

- `apps/starter/`：默认复制。
- `themes/<theme_id>/`：项目内容事实源。
- `apps/zju-reference/`：高级功能参考和回归目标。
- `templates/agent/AGENTS.md`：给新项目 agent handoff 使用。

不要把 ZJU docs、部署域名、生产镜像名、证书、数据库 volume 或项目私有 workflow 直接复制进新项目。
