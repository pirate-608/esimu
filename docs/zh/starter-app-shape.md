# Starter 应用形态

`apps/starter` 是唯一标准应用基础。`esimu new` 从已安装 wheel 中复制 Starter，
并写入主题、包依赖、生成元数据、README、环境模板和 Agent 交接文件。

可复用纯逻辑应进入 `esimu-core`；FastAPI、SQLite、WebSocket 和 Vue 集成属于
生成项目。下游可以替换 adapter，但升级时应保持版本化主题、状态和协议边界。
