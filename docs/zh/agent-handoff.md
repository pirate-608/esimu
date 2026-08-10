# Agent 交接

这页给后续接手 esimu lab 的 agent 使用。

## 第一件事

```powershell
cd esimu-lab
git status --short
```

不要假设工作树干净。实验仓经常保留尚未提交的抽取工作。

## 硬边界

除非用户明确要求跨仓库改动，否则不要修改 ZJUers Simulator 主游戏仓库。

ZJUers Simulator 是主产品；esimu 是实验仓。成熟通用改进只能经过 review 后再有意识地 cherry-pick 回主仓。

## 当前抽取状态

- `esimu_core.world`：主题路径、balance、stat、items、theme、story、prompt、world catalog 和 theme contract。
- `esimu_core.domain`：学期/GPA、effects、属性边界和 action gate。
- `esimu_core.runtime`：clock、action decision、snapshot、cooldown、task tracking。
- `esimu_core.lifecycle`：开局、学期转换、成就详情 payload。
- `esimu_core.content`：事件、论坛、私信 payload 契约。
- `esimu_core.ai`：可选 OpenAI-compatible transport、主题化生成、M2-her
  角色消息、输出校验与三模式降级。
- `apps/starter`：默认最小非 ZJU starter app。
- `apps/zju-reference`：可选完整参考适配器和回归目标，不是默认框架路径。

core 不能导入 Redis、FastAPI、SQLAlchemy、WebSocket 或 reference app service。
`esimu_core.ai.transport` 是 OpenAI SDK 的可选 extra 边界；基础包导入不得依赖它。

## 工作放哪里

- 主题内容：`themes/<theme_id>/`。
- 纯规则：`simulator-core/backend/esimu_core/domain/`。
- 运行时纯辅助：`esimu_core/runtime/`。
- 世界校验：`esimu_core/world/theme_contract.py`。
- 项目脚手架：`simulator-core/backend/scripts/`。
- 通用模型 transport、prompt 组装和降级：`esimu_core/ai/`；密钥、缓存、向量检索和
  WebSocket 副作用留在 app adapter。
- 文档站：`mkdocs.yml`、`docs/index.md`、`docs/assets/`。
- 外部 I/O 和兼容 glue：具体 app adapter。新项目优先看 `apps/starter/`；
  `apps/zju-reference/` 只用于 legacy-rich 兼容检查。

## 常用检查

```powershell
cd esimu-lab\simulator-core\backend
python -m pytest tests
python -m ruff check esimu_core scripts tests
python scripts\validate_world_data.py
$env:SIMULATOR_THEME='demo-campus'; python scripts\validate_world_data.py
```

文档站：

```powershell
cd esimu-lab
zensical build
```
