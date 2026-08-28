# AI 集成

esimu 包含面向主题内容生成的可选 AI 模块。模型生成是正式框架能力，但算法模式
或本地事件库游戏仍无需安装、配置任何模型。

## 包边界

`esimu_core.ai` 提供：

- OpenAI-compatible provider/model 配置校验；
- 通用模型与 MiniMax M2-her role profile；
- 延迟导入、可选安装的 OpenAI SDK transport；
- 平台共享 client 与玩家会话 client 的生命周期隔离；
- JSON 和 Markdown fenced output 的防御性解析；
- 主题化事件、论坛、私信、回复与毕业总结生成；
- 基于属性注册表的 effect 白名单和限幅；
- `library`、`hybrid`、`ai` 三模式及本地降级。

基础包仍只强制依赖 Pydantic。需要内置 transport 时安装：

```powershell
python -m pip install -e ".[ai]"
```

应用也可以自行实现很小的 `ChatTransport` protocol。

## Starter 配置

starter 默认完全使用本地内容库。环境变量决定初始模式和可用 transport；每个持久化
session 可通过 `set_mode` 独立切换，不会修改其他玩家的模式：

```text
ESIMU_CONTENT_MODE=library
```

启用通用兼容接口：

```powershell
$env:ESIMU_CONTENT_MODE='hybrid' # library、hybrid 或 ai
$env:ESIMU_LLM_PROVIDER='qwen'
$env:ESIMU_LLM_MODEL='qwen-plus'
$env:ESIMU_LLM_API_KEY='...'
$env:ESIMU_LLM_BASE_URL='https://example.com/v1' # 自定义端点时可选
$env:ESIMU_LLM_TIMEOUT_SECONDS='20'
$env:ESIMU_HYBRID_AI_PROBABILITY='0.35'
```

本地 Ollama 无需 API key：

```powershell
$env:ESIMU_CONTENT_MODE='ai'
$env:ESIMU_LLM_PROVIDER='ollama'
$env:ESIMU_LLM_MODEL='qwen3:8b'
```

私信角色扮演可选 MiniMax M2-her：

```powershell
$env:ESIMU_RP_PROVIDER='minimax'
$env:ESIMU_RP_MODEL='M2-her'
$env:ESIMU_RP_API_KEY='...'
$env:ESIMU_RP_BASE_URL='https://api.minimaxi.com/v1'
```

M2-her 会保留 `user_system`、`group` 和 sample-message 等角色类型，并使用
`max_completion_tokens`；普通兼容模型使用 `max_tokens`。

## 降级规则

| 模式 | 行为 |
| --- | --- |
| `library` | 永不调用模型。 |
| `hybrid` | 按配置概率选择 AI，失败时尝试另一内容源。 |
| `ai` | 优先 AI；超时、异常、空响应或非法输出时回退本地库。 |

模型生成的事件和私信 effects 会经过 `world/stat_definitions.json` 白名单；未知字段
被丢弃，合法数值在进入 session 前限幅。

私聊回复采用两阶段流程：玩家消息立即保存和推送，NPC/AI 生成进入按联系人去重的
后台任务；每三次玩家回复关闭并结算一轮。

## Adapter 责任

core 不负责 Redis/数据库内容池、浏览器玩家提交的 API key、计费配额、内容审核、
pgvector 检索、WebSocket 推送或存档 schema。部署密钥可使用
`OpenAITransportRegistry.shared()`；玩家密钥应使用 `session()`，结束后关闭，且禁止
把其生成内容写入全局共享池。

生产专用 adapter 可增加 Redis 内容池或向量检索，同时继续复用这些 transport、
解析和角色合同。
