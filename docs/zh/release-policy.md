# 发布策略

esimu 面向单主题叙事模拟器发布 `esimu-core` 预发布版本。当前公开基线是
`0.2.0b5`，下一版源码候选是 `0.3.0b2`。

## 版本与契约

- 包名：`esimu-core`
- Python 命名空间：`esimu_core`
- 版本来源：`packages/esimu-core/esimu_core/__init__.py`
- 标签：`esimu-core-v<version>`
- 主题 schema：v1
- Starter 状态与 WebSocket 协议：v2

加载时自动迁移 v1 状态，并继续接受 v1 客户端。文档化 Python API、主题/世界
数据、安装后 CLI 或 Starter HTTP/WebSocket 的破坏性变化必须提升 Beta 次版本
并提供迁移说明；补丁版本可以拒绝原本就非法的数据。

## 发布渠道

- `release-candidate.yml` 通过 Trusted Publishing 手动发布 TestPyPI 候选。
- 推送精确 `esimu-core-v<version>` 标签后，`release.yml` 发布 PyPI 和 GitHub
  prerelease，并附带同一构建产生的 wheel/sdist。
- 仓库不得保存长期 PyPI token。

标签 workflow、PyPI、GitHub prerelease 和外部安装验证全部成功前，不得宣称
版本已发布。

## 必须通过的门禁

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest packages\esimu-core\tests
python -m pytest apps\starter\backend\tests
python -m ruff check packages\esimu-core\esimu_core packages\esimu-core\scripts packages\esimu-core\tests apps\starter\backend\app apps\starter\backend\tests
python packages\esimu-core\scripts\validate_world_data.py
python packages\esimu-core\scripts\sync_scaffold_bundle.py

cd apps\starter\frontend
corepack pnpm install --frozen-lockfile
corepack pnpm typecheck
corepack pnpm test
corepack pnpm build
cd ..\..\..
zensical build
python packages\esimu-core\scripts\release_smoke.py
```

release smoke 会构建 wheel/sdist，在一次性环境安装 wheel，执行
`esimu new/validate/doctor/inspect/sync/add`，启动生成项目、完成两个学期，并
验证 SQLite 重启恢复。

## 候选到发布

1. 提交并推送候选到 `main`，等待必需 CI。
2. 在无源码 checkout 的 `esimu-beta-example` 中做外部验证。
3. 发布 TestPyPI 候选并从外部安装精确版本。
4. 修复框架问题；若候选已上传，递增不可覆盖的 Beta 后缀。
5. 外部验收后才创建并推送精确版本标签。
6. 核对 PyPI、GitHub assets/checksum、Pages 和干净安装。

Zensical 精确版本固定在 `docs/requirements.txt`，文档 CI 必须安装该版本并严格
构建。
