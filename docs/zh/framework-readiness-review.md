# 框架就绪审查

日期：2026-07-04

## 结论

esimu 已经可以作为**基本完整的 alpha 框架**，用于创建单主题模拟器原型。

推荐形态是：

```text
esimu-core + starter app + theme pack
```

它还不是稳定公共框架，也不建议立刻发布到 PyPI。至少应等一个外部模拟器项目实际使用 starter 路线，并反馈缺失能力后，再考虑正式发布渠道。

## 已就绪

- `esimu-core` 是可安装 Python 包，包含版本元数据、typed package marker、changelog、release policy 和 CI。
- core 拥有主题/世界加载器、纯规则、运行时辅助、生命周期辅助和内容/消息标准化。
- core 不引入 FastAPI、Redis、SQLAlchemy 或 WebSocket 对象；可选
  `esimu_core.ai` extra 提供 OpenAI-compatible transport，密钥、缓存和持久化留在 adapter。
- 主题包有文档化契约，并通过 `validate_world_data.py` 严格校验。
- `demo-campus` 验证了非 ZJU 路径，覆盖事件、论坛、私信、道具、成就、story、prompt 和 runtime payload。
- `apps/starter` 提供默认内存态 FastAPI/WebSocket 后端、可选本地 JSON 文件 session store，以及很小的 Vite/TypeScript 前端。
- `new_project.py` 能生成独立 starter 项目。
- `scaffold_world_data.py` 和 `scaffold_game_stat.py` 降低世界数据创作成本。

## 尚未稳定

- 不支持运行时多主题部署。
- starter 后端默认仍是内存态，已有本地 JSON 文件开发存储；Redis/PostgreSQL/save-slot 仍只存在于参考应用中。
- starter 前端是皮肤，不是可复用前端包；目前已有 pnpm lockfile 和 CI build/typecheck，但还没有共享组件包化。
- `cc98` 和 `dingtalk` 仍是 ZJU reference adapter 的内部兼容 ID。
- AI 生成已成为可选 core/starter 能力；管理后台、生产 Docker、持久内容池、
  embedding 检索与部署加固仍属于项目级能力。

## 验证结果

Phase 9 验证结果：

```text
Core tests: 65 passed
Core ruff: passed
Default theme validation: passed
demo-campus validation: passed
Starter backend tests: 6 passed
Starter backend ruff: passed
Starter frontend typecheck/build: passed
Reference backend smoke/game-state tests: 28 passed
```

## 建议

保持 esimu 的定位为：

```text
library plus starter app
```

不要把它退化成纯模板仓库，因为 `esimu-core` 已经有清晰包边界和独立测试。也不要把它当作完全稳定的公共框架，因为生产级持久化、可复用前端包化和真实外部项目反馈仍然缺失。

下一阶段可优先推进：

- 生产级 starter 可选持久化适配器；
- starter 前端可复用包化；
- 在 starter surface 之外继续中性化 messenger/forum 协议 ID；
- 用 `new_project.py` 做一个真实第二非 ZJU 模拟器。

## 独立化判断

框架已经 alpha-ready，但仓库还没有彻底脱离 ZJU 母仓工作区。

接下来应按以下顺序推进：

- Phase 10：移除母仓路径和母仓 venv 假设，让 `pirate-608/esimu-lab` fresh clone 后可独立运行。
- Phase 11：让 ZJU reference app 变成可选兼容目标，而不是默认框架路径。
- Phase 12：加固 starter，使其能支撑真实下游原型。
- Phase 13：确定正式发布渠道。
- Phase 14：用真实外部非 ZJU 模拟器验证框架。

在 Phase 12 完成前，不建议把 esimu 称为“正式独立框架”。Phase 10 后可以称为“可独立 clone 的 lab”；Phase 14 后才适合称为“被外部模拟器验证过的框架”。

## 发布候选加固

当前 artifact-to-consumer smoke 已在本地通过：构建 wheel、生成独立项目、创建新 venv、安装 core、校验主题并访问 Starter API。首个匹配 Git tag 与远程 CI 仍待完成，因此尚不能宣称已经对外发布。
