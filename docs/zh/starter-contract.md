# Starter 契约

`apps/starter/` 是新 esimu 模拟器原型的默认应用底座。它刻意比 ZJU reference
adapter 小，应该保持容易复制、删除或替换。

## 范围

starter 提供：

- 最小 FastAPI 后端；
- 很小的 Vite/TypeScript 前端；
- 默认内存 session；
- 可选本地 JSON 文件 session，用于开发；
- 从主题包生成的 theme/story/stat metadata；
- 中性的 forum/messenger public actions；
- 不要求 Redis、PostgreSQL、SQLAdmin、生产 Docker 或强制启用 LLM client。

starter 已安装可选 AI transport，但默认使用 `ESIMU_CONTENT_MODE=library`，不会调用
模型。provider、M2-her 和降级规则见 `ai-integration.md`。

只有项目一开始就需要这些重功能时，才考虑 ZJU reference adapter。

## 后端 HTTP 表面

starter backend 暴露一个很小的接口面：

| Route | 作用 |
| --- | --- |
| `GET /healthz` | 返回轻量进程就绪状态。 |
| `GET /config` | 返回当前主题、故事和属性 metadata。 |
| `POST /api/auth` | 创建占位内存 session token。 |
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
| `relax` | `feedback` |
| `event` | `event` |
| `event_choice` | `feedback` |
| `forum` | `forum_post` |
| `messenger` | `messenger_round` |
| `item_buy` | `items_state` |
| `item_sell` | `items_state` |
| `exam` | `semester_summary` |
| `ending` | `ending` |

`cc98`、`dingtalk` 这类 legacy ID 应留在 ZJU reference adapter 或兼容 mapper，
不要放进 starter public naming。

## 持久化

默认：

```text
ESIMU_STARTER_SESSION_STORE=memory
```

开发文件存储：

```text
ESIMU_STARTER_SESSION_STORE=file
ESIMU_STARTER_DATA_DIR=data/starter-sessions
```

文件存储每个 token 写一个 JSON 文件，只作为本地开发扩展点。生产项目应替换
`SessionStore` protocol，接入自己的持久化层。

## 前端依赖

starter frontend 使用 pnpm，并提交 `pnpm-lock.yaml`。CI 应运行：

```powershell
cd apps\starter\frontend
corepack pnpm install --frozen-lockfile
corepack pnpm typecheck
corepack pnpm build
```

在真实下游项目证明值得抽取前，frontend skin 应保持小而清楚。
