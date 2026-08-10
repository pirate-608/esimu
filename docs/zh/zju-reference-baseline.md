# ZJU 参考基线

这份文档记录框架实验仓第一次复制 ZJU reference app 的基线。

## 来源

- 源工作区：原开发机上的 ZJUers Simulator 历史 checkout。
- 当前参考应用位置：`apps/zju-reference`
- 复制验证时源 commit：`53cb7d176bb68094beb30979eff70fd15aa6220e`
- 复制时间：`2026-07-01T19:33:51+08:00`
- 复制验证后源工作树：clean

## 复制策略

第一个 lab app 是完整可运行参考副本。它不是最终框架形态。

它存在的原因是：框架抽取可以从一个已知可运行游戏开始，而不是从零重建所有 glue code。

## 排除项

- `.git`
- `.env` 和 `.env.*`
- `node_modules`
- `dist`
- Python cache 和测试 cache
- 临时 pytest/release-health 目录
- 运行日志
- `nginx/ssl`

## 第一轮隔离

- Docker image/container/volume 使用 `simlab` 前缀。
- 本地后端端口：`127.0.0.1:18000:8000`。
- 本地 Postgres 端口：`127.0.0.1:25432:5432`。
- 本地 Redis 端口：`127.0.0.1:16379:6379`。
- 本地 Nginx HTTP 端口：`18080`。
- Vite dev server 端口：`15173`。
- 前端浏览器存储现在从 active theme 的 `storage.prefix` 派生。
