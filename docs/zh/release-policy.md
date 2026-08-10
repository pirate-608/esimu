# 发布策略

`esimu-core` 当前是 alpha 软件，可用于单主题模拟器原型，但还不是稳定公共框架。

## 版本与标签契约

- 包名：`esimu-core`
- 导入命名空间：`esimu_core`
- 版本来源：`simulator-core/backend/esimu_core/__init__.py`
- 标签格式：`esimu-core-v<version>`

生成器会把下游项目固定到这个精确 Git tag。因此，只有对应标签已经推送到
`pirate-608/esimu-lab`，且包含文档所述的 core/Starter 改动时，该版本才真正可供
外部安装。在分支和标签都推送前，不应宣称已经发布。

当前使用 Git tag，不发布 PyPI。待真实外部模拟器验证安装和升级后再评估 PyPI。

## 兼容范围

- `MAJOR`：破坏性 Python API 或主题/世界契约变化。
- `MINOR`：兼容的新 core API、validator 与 Starter 能力。
- `PATCH`：bug fix，或只拒绝原本就非法数据的更严格校验。

公共兼容范围包括文档化 Python API、主题/世界 JSON、安装后 CLI，以及 Starter
HTTP/WebSocket 表面。

## 必须通过的发布门禁

```powershell
python -m pip install -r requirements-dev.txt
cd simulator-core\backend
python -m pytest tests
python -m ruff check esimu_core scripts tests
python scripts\validate_world_data.py
$env:SIMULATOR_THEME='demo-campus'
python scripts\validate_world_data.py
Remove-Item Env:SIMULATOR_THEME

cd ..\..\apps\starter\backend
python -m pytest tests
python -m ruff check app tests
cd ..\frontend
corepack pnpm install --frozen-lockfile
corepack pnpm typecheck
corepack pnpm build

cd ..\..\..
python simulator-core\backend\scripts\release_smoke.py
zensical build
```

`release_smoke.py` 会构建 sdist/wheel、生成一次性项目、创建全新 venv、从 wheel
安装 `esimu-core[ai]`、执行安装后的 world validator，并访问生成项目的 Starter
API。它能捕获 editable 源码测试发现不了的打包与 import 顺序问题。

## CI 与打标签

先提交并推送 release commit，等待 clean-checkout CI 全绿，再确认版本和工作树：

```powershell
python -c "import esimu_core; print(esimu_core.__version__)"
git status --short
git log -1 --oneline
```

随后创建精确匹配的标签：

```powershell
git tag esimu-core-v0.1.0
git push origin master
git push origin esimu-core-v0.1.0
```

标签 CI 会拒绝与 `esimu-core-v<esimu_core.__version__>` 不一致的名称。通过后，
还应在不含 esimu-lab 的干净目录或另一台机器上，用生成项目的默认 requirements
完成一次安装。