# 创建新项目

这份清单用于生成一个离开 esimu 后仍可独立安装运行的模拟器。生成器会复制标准
Starter 和一个主题，形成独立项目。

## 生成项目

```powershell
esimu new D:\projects\my-simulator `
  --project-name "My Simulator" `
  --theme-id my-simulator `
  --institution "星河学院" `
  --institution-short "星河"
```

生成结果包括：

```text
apps/starter/backend/
apps/starter/frontend/
themes/my-simulator/
scripts/
docs/scaffold-checklist.md
.env.example
AGENTS.md
README.md
```

生成的 scripts 只作为 Beta 兼容 wrapper；新自动化优先使用安装后的
`esimu add` 与 `esimu sync`。

后端依赖固定到与 `esimu_core.__version__` 一致的精确包版本。其他开发者安装
前，该版本必须已存在于所选 package index。测试未发布 core 时，使用
`--core-dependency` 传入本地 editable 路径或刚构建的 wheel URL。

## 独立安装和校验

对应包版本可用后：

```powershell
cd D:\projects\my-simulator
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r apps\starter\backend\requirements.txt
esimu validate --root . --theme my-simulator
esimu doctor --root . --theme my-simulator
```

校验命令来自已安装的 `esimu-core`，读取当前项目自己的 `themes/`，不再需要回到 esimu 查找脚本。

## 运行 Starter

```powershell
cd apps\starter\backend
python -m uvicorn app.main:app --reload --port 18001
```

第二个终端：

```powershell
cd apps\starter\frontend
corepack pnpm install --frozen-lockfile
corepack pnpm dev
```

打开 `http://127.0.0.1:15175`。Vite 会代理 HTTP 与 WebSocket。

## 编辑主题与世界数据

保持启动期单主题，主要编辑：

```text
themes/my-simulator/theme.json
themes/my-simulator/story.json
themes/my-simulator/prompts.json
themes/my-simulator/world/
themes/my-simulator/assets/
```

推荐顺序是属性/平衡、道具、专业/课程、成就/角色、事件库、叙事资源与 prompt。

生成项目已复制 scaffold helper：

```powershell
cd D:\projects\my-simulator
$env:ESIMU_PROJECT_ROOT=(Get-Location).Path
$env:ESIMU_THEME='my-simulator'
esimu add stat focus --root . --theme my-simulator --label 专注 --show-in-hud
esimu add item focus_card --root . --theme my-simulator --name 专注卡
esimu add achievement first_win --root . --theme my-simulator --name 第一次胜利
esimu sync --root . --theme my-simulator
esimu validate --root . --theme my-simulator
```

使用 `--write` 前先审查输出。Starter 默认 SQLite 存储和 library 内容；生产数据库、
admin、缓存、凭证与遥测仍由具体 adapter 负责。
