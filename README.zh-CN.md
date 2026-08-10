# Simulator Framework Lab

[English](README.md) | [简体中文](README.zh-CN.md)

`esimu` 是一个实验性项目：它从 ZJUers Simulator 中提取可复用的叙事模拟器框架，同时不干扰仍在持续开发和运行的 ZJU 主游戏。

当前仓库处于 Alpha 候选阶段。核心包、Starter、项目生成器和隔离 wheel 安装 smoke 均可运行，但只有推送与版本匹配的 Git tag 后，对应版本才视为正式对外发布。框架的推荐组成是：

```text
esimu-core + Starter 应用 + 选定的主题包
```

## 当前状态

- `apps/starter/` 是首个不依赖 ZJU 语境的最小 Starter 应用，默认使用 `demo-campus`，后端状态保存在内存中。新项目应从这里开始。
- `apps/zju-reference/` 是可选的高兼容性参考适配器，由 ZJUers Simulator 主工作区复制并隔离而来。它适合回归验证，但运行 esimu 并不依赖它。
- `simulator-core/backend/` 包含可安装的 Python 包 `esimu-core`，代码通过 `esimu_core.*` 导入。
- `esimu_core.ai` 提供可选的 OpenAI-compatible 与 MiniMax M2-her 内容生成能力，并包括主题 Prompt、输出校验和本地降级策略。
- `themes/zju/` 是第一套完整参考主题。
- `themes/demo-campus/` 是用于发现隐藏 ZJU 假设的最小可移植性验证主题。
- `docs/` 包含架构、路线图、主题契约、快速开始、发布策略、就绪审查和项目创建指南。
- `mkdocs.yml` 是此框架 Zensical 文档站的配置文件。

ZJUers Simulator 始终是主产品。实验仓中的成熟改进必须经过审查后有意地移植回主仓；主游戏不得意外依赖此实验仓。

## 十分钟快速开始

第一次打开实验仓时，从这里开始：

```powershell
git clone https://github.com/pirate-608/esimu-lab.git
cd esimu-lab
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements-dev.txt
git status --short
```

随后阅读：

1. `AGENTS.md`：工作区规则与 Agent 交接说明。
2. `docs/zh/quickstart.md`：环境搭建与验证命令。
3. `docs/zh/architecture.md`：当前 core、主题和适配器边界。
4. `docs/zh/new-project-bootstrap.md`：创建新的模拟器主题或应用。
5. `docs/zh/starter-app-shape.md`：复制参考应用前先了解 Starter 形态。
6. `docs/zh/starter-contract.md`：Starter 的 HTTP、WebSocket 与持久化接口。
7. `docs/zh/release-policy.md`：为 `esimu-core` 创建 tag 前的发布要求。
8. `docs/zh/framework-readiness-review.md`：框架当前的成熟度判断。
9. `docs/zh/ai-integration.md`：可选模型接入及其安全边界。

活动主题在构建或启动时选定：

```powershell
$env:SIMULATOR_THEME='zju'
$env:SIMULATOR_THEME='demo-campus'
```

当前阶段有意不支持在运行时切换多个主题。

## 常用命令

在 `simulator-core/backend/` 中检查核心包：

```powershell
python -m pytest tests
python -m ruff check esimu_core scripts tests
python scripts\validate_world_data.py
$env:SIMULATOR_THEME='demo-campus'; python scripts\validate_world_data.py
```

在 `apps/zju-reference/zjus-backend/` 中进行可选的参考后端检查：

```powershell
python -m pytest tests\unit
python -m ruff check app tests\unit
```

在 `apps/zju-reference/zjus-frontend/` 中进行可选的参考前端检查：

```powershell
npx vue-tsc --noEmit
npx vitest run
npx vite build
```

这些参考应用检查只用于兼容性验证，与默认的 core、Starter 和文档路径相互独立。安装说明、editable package 备用方式和主题元数据生成命令详见 `docs/zh/quickstart.md`。

在 `apps/starter/frontend/` 中检查 Starter 前端：

```powershell
corepack pnpm install --frozen-lockfile
corepack pnpm typecheck
corepack pnpm build
```

在实验仓根目录进行发布候选和文档检查：

```powershell
python simulator-core\backend\scripts\release_smoke.py
zensical build
```

发布 smoke 会构建 wheel，将其安装进一次性虚拟环境，生成独立模拟器，校验主题，并调用 Starter API。只有与 `esimu_core.__version__` 匹配的 Git tag 已推送时，最终安装命令才可直接使用。

## 仓库结构

```text
apps/
  starter/            # 最小的非 ZJU Starter 后端与前端。
  zju-reference/      # 可选的高兼容性参考适配器。
simulator-core/
  backend/            # esimu-core Python 包、脚本和测试。
  frontend/           # 未来提取的 Vue/运行时前端模块。
themes/
  zju/                # 完整的 ZJU 参考主题。
  demo-campus/        # 最小可移植性验证主题。
docs/
  index.md
  zh/index.md
  quickstart.md
  zh/quickstart.md
  new-project-bootstrap.md
  starter-app-shape.md
  starter-contract.md
  release-policy.md
  framework-readiness-review.md
  agent-handoff.md
  architecture.md
  roadmap.md
  theme-pack-contract.md
templates/
  agent/AGENTS.md     # 可复制的 Starter 交接模板。
mkdocs.yml            # 与 Zensical 兼容的文档站配置。
requirements-dev.txt  # 全新克隆后的开发依赖入口。
```

## 创建新的模拟器

请以 `docs/zh/new-project-bootstrap.md` 为主清单。简要流程如下：

1. 使用 `simulator-core/backend/scripts/new_project.py` 生成 Starter 项目。
2. 编辑生成的 `theme.json`、`story.json`、`prompts.json` 和 `world/`。
3. 对生成的主题运行 world-data validation。
4. 继续使用生成的 `apps/starter/`，或先阅读 `docs/zh/starter-app-shape.md`，再决定是否采用完整参考适配器。
5. 在路线图明确迁移前，保留 `cc98`、`dingtalk` 等 ZJU 专用协议 ID 作为兼容 ID。

示例：

```powershell
cd esimu-lab\simulator-core\backend
python scripts\new_project.py <target-project> --project-name "My Simulator" --theme-id my-simulator
cd <target-project>
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r apps\starter\backend\requirements.txt
esimu-validate-world --root . --theme my-simulator
```

最终安装命令要求与 `esimu_core.__version__` 匹配的 Git tag 已推送。在测试尚未发布的框架改动时，请通过 `--core-dependency` 指向本地 wheel 或 editable path。

## 命名约定

- 框架简称：`esimu`
- 核心包名：`esimu-core`
- Python 导入命名空间：`esimu_core`

除历史说明外，不应再引入旧的临时 framework-core 名称。

## 发布

`esimu-core` 计划使用独立 `esimu-lab` 仓库中的 Git tag 作为 Alpha 发布通道。版本事实源位于 `simulator-core/backend/esimu_core/__init__.py`；只有推送匹配的 `esimu-core-v<version>` tag 且 tag CI 通过后，该版本才视为可从外部安装。完整发布门槛见 `docs/zh/release-policy.md`。
