# 创建新项目

这份清单用于生成一个离开 esimu-lab 后仍可独立安装运行的模拟器。生成器只复制
小型 Starter 和一个主题，不复制 ZJU reference 产品代码。

## 生成项目

```powershell
cd simulator-core\backend
python scripts\new_project.py D:\projects\my-simulator `
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
scripts/scaffold_game_stat.py
scripts/scaffold_world_data.py
docs/scaffold-checklist.md
.env.example
AGENTS.md
README.md
```

后端依赖默认固定到与 `esimu_core.__version__` 一致的 Git tag。其他开发者安装
前，该 tag 必须已推送。测试未发布 core 时，使用 `--core-dependency` 传入本地
editable 路径或刚构建的 wheel URL。

## 独立安装和校验

正式标签可用后：

```powershell
cd D:\projects\my-simulator
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r apps\starter\backend\requirements.txt
esimu-validate-world --root . --theme my-simulator
```

校验命令来自已安装的 `esimu-core`，读取当前项目自己的 `themes/`，不再需要回到 esimu-lab 查找脚本。

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
$env:SIMULATOR_LAB_ROOT=(Get-Location).Path
$env:SIMULATOR_THEME='my-simulator'
python scripts\scaffold_game_stat.py add focus --label 专注 --show-in-hud
python scripts\scaffold_world_data.py item focus_card --name 专注卡
python scripts\scaffold_world_data.py achievement first_win --name 第一次胜利
esimu-validate-world --root . --theme my-simulator
```

使用 `--write` 前先审查输出。Starter 默认内存存储和 library 内容；生产数据库、
admin、缓存、凭证与遥测仍由具体 adapter 负责。