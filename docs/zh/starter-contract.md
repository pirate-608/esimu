# Starter 契约

`apps/starter/` 是新 esimu 模拟器原型的默认应用底座。它刻意比生产专用 adapter
小，应该保持容易复制、删除或替换。

## 范围

starter 提供：

- 最小 FastAPI 后端；
- Vue 3/Pinia Vite/TypeScript 控制台；
- 默认 SQLite session，测试使用内存 session；
- 本地 JSON 文件 session 仅作为 Beta 临时兼容 adapter；
- 从主题包生成的 theme/story/stat metadata；
- 中性的 forum/messenger public actions；
- 持久化冷却、声明式成就、session 级内容模式和失败/毕业结局；
- 自动事件/私聊调度与不阻塞 WebSocket 的模型任务；
- 不要求 Redis、PostgreSQL、SQLAdmin、生产 Docker 或强制启用 LLM client。

starter 已安装可选 AI transport，但默认使用 `ESIMU_CONTENT_MODE=library`，不会调用
模型。provider、M2-her 和降级规则见 `ai-integration.md`。

需要分布式存储、正式身份或运营后台时，由下游替换 adapter。

## 后端 HTTP 表面

starter backend 暴露一个很小的接口面：

| Route | 作用 |
| --- | --- |
| `GET /healthz` | 返回轻量进程就绪状态。 |
| `GET /config` | 返回当前主题、故事和属性 metadata。 |
| `POST /api/auth` | 创建或恢复不透明本地 profile token。 |
| `GET /api/majors` | 返回当前主题专业列表。 |
| `POST /api/init_character` | 初始化一个内存角色。 |
| `WS /ws` | 跑一组用于 smoke 的小型 action 协议。 |

这些接口是 starter contract，不代表每个下游游戏的最终 API。

## 浏览器连接

前端默认使用同源请求。开发时，`vite.config.ts` 把 `/api`、`/config`、
`/healthz` 和 `/ws` 代理到 `ESIMU_DEV_BACKEND_URL`，默认地址是
`http://127.0.0.1:18001`。

同源生产部署应由反向代理转发这些路径。前后端分域时，在前端构建阶段设置
`VITE_ESIMU_API_BASE`、`VITE_ESIMU_WS_BASE`，并在后端用逗号分隔的
`ESIMU_CORS_ORIGINS` 放行明确来源。带凭证的生产 API 不应使用通配 CORS。

## WebSocket Actions

starter 使用中性的 action 名：

| Action | Response |
| --- | --- |
| `start` / `get_state` | `tick` |
| `ping` | `pong` |
| `pause` / `resume` / `set_speed` | `tick` |
| `set_mode` | `mode_changed` |
| `relax` | `feedback` |
| `event` | `event` |
| `event_choice` | `feedback` |
| `forum` | `forum_post` |
| `messenger` | `messenger_update`（v1 客户端为 `messenger_round`） |
| `messenger_reply` | 立即推送玩家消息，后台完成 NPC update |
| `messenger_mark_read` | `messenger_update` |
| `item_buy` | `items_state` |
| `item_sell` | `items_state` |
| `exam` | `semester_summary` |
| `next_semester` | `new_semester` |
| `ending` | `ending` |
| `save_game` | `save_result` |
| `save_and_exit` | `save_result`、`exit_confirmed`、1000 close |
| `exit_without_save` | `exit_confirmed`、1000 close |

当前协议为 v2，同时接受 v1 客户端并为其保留旧私聊响应名。Starter public naming
始终使用中性的 `forum`、`messenger`。

## 持久化

默认单机存储：

```text
ESIMU_STARTER_SESSION_STORE=sqlite
ESIMU_STARTER_DATABASE_PATH=data/esimu.sqlite3
```

开发文件存储：

```text
ESIMU_STARTER_SESSION_STORE=file
ESIMU_STARTER_DATA_DIR=data/starter-sessions
```

SQLite 使用 WAL、事务写入、token hash 和 v2 JSON 状态；v1 状态加载时自动补齐
新字段，不修改 SQLite user_version。测试可使用 `memory`，分布式部署应由下游实现
异步 `SessionStore`。

## 运行时行为

- 冷却时间戳随 session 保存，`init/tick` 下发剩余秒数。
- 自动事件与私聊读取 `game_balance.json` 的间隔和概率，暂停或结算时停止。
- 玩家私聊消息先保存并显示，NPC/AI 回复在后台生成；每三次回复结算一轮。
- 成就使用主题拥有的声明式 `all/any` 条件。
- Game Over 阈值来自 balance；失败结局与毕业结局是不同 outcome。

## 前端依赖

starter frontend 使用 pnpm，并提交 `pnpm-lock.yaml`。CI 应运行：

```powershell
cd apps\starter\frontend
corepack pnpm install --frozen-lockfile
corepack pnpm typecheck
corepack pnpm build
```

在真实下游项目证明值得抽取前，frontend skin 应保持小而清楚。
