# 快速开始

这是从全新 clone 到运行 esimu Starter、再到生成独立模拟器的最短验收路径。

## 克隆并安装 esimu

```powershell
git clone https://github.com/pirate-608/esimu.git
cd esimu
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements-dev.txt
```

仓库应当可以独立运行，不要把 import、校验命令或生成文件指向 ZJUers
Simulator 母仓。

## 验证 core 与主题

```powershell
cd packages\esimu-core
python -m pytest tests
python -m ruff check esimu_core scripts tests
python scripts\validate_world_data.py
$env:ESIMU_THEME='demo-campus'
python scripts\validate_world_data.py
Remove-Item Env:ESIMU_THEME
```

默认校验现在使用 `zju-simplified`；第二次显式运行继续覆盖中性的
`demo-campus` 模板。

生成项目不需要保留 esimu 路径，安装 core 后直接运行：

```powershell
esimu validate --root <项目根目录> --theme <主题 ID>
esimu doctor --root <项目根目录> --theme <主题 ID>
esimu inspect --root <项目根目录> --theme <主题 ID>
esimu sync --root <项目根目录> --theme <主题 ID>
```

## 运行 Starter 开发栈

```powershell
cd <esimu 仓库根目录>
esimu dev --root . --theme zju-simplified
```

健康检查位于 `http://127.0.0.1:18001/healthz`。默认持久化是
`data/esimu.sqlite3`，默认主题是 `zju-simplified`；Vite 位于
`http://127.0.0.1:15175` 并代理 HTTP/WebSocket。

在第二个终端请求同步完整重启或生产构建：

```powershell
esimu reload --root . --theme zju-simplified
esimu build --root . --theme zju-simplified
```

在 `dev` 终端按 Ctrl+C 会同时停止两个服务。

前后端分域部署时，在前端 `.env` 设置：

```dotenv
VITE_ESIMU_API_BASE=https://api.example.com
VITE_ESIMU_WS_BASE=wss://api.example.com
```

后端通过 `ESIMU_CORS_ORIGINS=https://game.example.com` 放行前端来源。若使用
同域 Nginx 反向代理，则保持两个 `VITE_*` 变量为空即可。

## 生成独立项目

上面的 editable 安装提供 `0.4.0b1` 候选。在该版本发布前，将同一个 editable
依赖写入生成项目：

```powershell
esimu new D:\projects\my-simulator `
  --project-name "My Simulator" `
  --theme-id my-simulator `
  --core-dependency "-e D:\projects\esimu\packages\esimu-core[ai]"
```

默认 source theme 是浙大精简适配 `zju-simplified`；需要中性模板时增加
`--source-theme demo-campus`。

生成项目拥有自己的 Starter、主题、资源、兼容 helper、README、环境模板和
AGENTS.md，可完全离开 esimu 源码安装运行：

```powershell
cd D:\projects\my-simulator
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r apps\starter\backend\requirements.txt
esimu validate --root . --theme my-simulator
esimu doctor --root . --theme my-simulator
esimu dev --root . --theme my-simulator
```

框架贡献者测试未发布 core 时，可给 `esimu new` 传入 `--core-dependency`，
使用本地 editable 路径或刚构建的 wheel。

## 编辑和校验世界数据

```powershell
cd D:\projects\my-simulator
esimu add stat focus --root . --theme my-simulator --label 专注 --show-in-hud
esimu add item focus_card --root . --theme my-simulator --name 专注卡
esimu add achievement first_win --root . --theme my-simulator --name 第一次胜利
esimu sync --root . --theme my-simulator
esimu validate --root . --theme my-simulator
```

默认只预览或检查。审查 JSON 后显式加入 `--write`；写入会原子发布、同步前端
metadata、执行主题校验，并在失败时回滚。

## 发布候选验收

```powershell
cd esimu
python packages\esimu-core\scripts\release_smoke.py
```

该命令会构建 sdist/wheel、生成一次性项目、创建新 venv、从 wheel 安装
`esimu-core[ai]`、校验主题并运行生成的 FastAPI Starter。CI 也执行同一条
链，并在 tag 构建时校验 `esimu-core-v<version>` 与包版本一致。

## 构建文档站

```powershell
zensical build
```

文档工具链在 `docs/requirements.txt` 中固定为 Zensical 0.0.57。
