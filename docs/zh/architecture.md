# 架构

esimu 从 ZJUers Simulator 的形态出发，把系统拆成三个明确层次：

```text
esimu-core + adapter app + theme pack
```

## esimu-core

core 拥有跨主题可复用的行为：

- 学期结算、GPA、周期恢复、属性边界和效果反馈等纯规则。
- 平衡、属性定义、道具、主题 manifest、story、prompt 和世界目录的加载器。
- tick、action gate、快照、冷却和后台任务去重等运行时辅助。
- 开局、学期切换、成就详情、事件/论坛/私信 payload 标准化。
- 可选 OpenAI-compatible transport、主题化生成、M2-her 角色消息、输出校验和降级策略。

基础 core 不依赖 FastAPI、Redis、SQLAlchemy、WebSocket 或参考应用 service。
`esimu_core.ai` 通过可选 `[ai]` extra 延迟接入 OpenAI SDK；不启用 AI 时不会加载它。

## 主题包

主题包拥有一个游戏自己的名词、数据和资源：

```text
themes/<theme_id>/
  theme.json
  story.json
  prompts.json
  assets/
  world/
```

主题控制学校/场景名称、论坛名称、私信工具名称、序章与结局、prompt 上下文、属性、平衡、道具、课程、角色、事件库和成就。

## 前端皮肤

前端皮肤把 core 的通用 UI 面映射到主题语言和视觉设计。

当前策略是构建期/启动期单主题：通过生成的 `theme.generated.ts`、`story.generated.ts` 和 `statDefinitions.generated.ts` 让前端消费主题数据。

## Starter App

`apps/starter/` 是第一个最小非 ZJU 应用形态：

- 后端：内存态 FastAPI/WebSocket adapter。
- 前端：很小的 Vite/TypeScript skin。
- 默认主题：`demo-campus`。

它刻意不包含 Redis、PostgreSQL、管理后台和生产 Docker。可选 AI adapter
已经接入，但默认处于纯本地 `library` 模式。

## Reference App

`apps/zju-reference/` 是从 ZJUers Simulator 复制来的完整参考适配器。

它保留了 Redis/PostgreSQL、存档、管理后台、LLM fallback、复杂前端和大量回归测试。它是回归目标和高级参考，不是新项目默认模板。

## 兼容 ID

当前仍保留 `cc98` 和 `dingtalk` 作为内部兼容 ID，因为它们流经 WebSocket、Redis、存档和旧测试。

用户可见名词应从主题的 `forum` 和 `messenger` 读取。协议 ID 迁移是后续兼容性阶段。

## 可选 AI 层

`esimu_core.ai` 正式承载模型配置、OpenAI-compatible transport、主题 prompt
组装、结构化输出解析、事件 effects 校验、M2-her 高级角色消息以及三模式降级策略。

应用 adapter 仍负责密钥来源、Redis/数据库缓存、embedding 检索、计费审核、
WebSocket 推送和存档。这样既能复用原模拟器 AI 核心，也不会让纯算法游戏被模型 SDK
或具体平台绑定。
