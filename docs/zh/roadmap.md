# 路线图

esimu 的路线目标，是从 ZJUers Simulator 中抽出一个基本完整的单主题模拟器框架。

## Phase 15：运行时闭环与安装后作者 CLI

状态：已在 `main` 实现，目标版本为尚未发布的 `0.3.0b1`。

- Starter 状态与协议升级到 v2，同时迁移 v1 状态并接受 v1 客户端。
- 持久化冷却、自动内容、声明式成就、Game Over、session 内容模式和有序保存退出
  补齐运行时闭环。
- 私聊采用立即显示玩家消息、后台生成 NPC 回复的两阶段流程，并支持未读、联系人
  多样性/复用和三回复结算。
- 安装后的 `doctor/inspect/sync/add` 取代源码路径脚本；兼容 wrapper 保留一个
  Beta 周期。
- 剩余门禁：wheel-only 生成项目 smoke 和外部 trial，通过后才能 tag/发布。

以下提取阶段作为历史保留；归档 reference app 路径不属于当前正式分支。

## 已完成阶段

### Phase 0-1：实验仓与参考副本

- 建立独立实验仓。
- 复制 ZJU reference app，并做端口、容器、存储 key 隔离。
- 保持主游戏不受实验影响。

### Phase 2-3：主题与核心规则

- 引入 `theme.json`、`story.json`、`prompts.json`。
- 将属性、道具、平衡、世界目录加载迁移到 active theme。
- 抽出 `esimu_core.domain`、`runtime`、`lifecycle` 和 `content`。

### Phase 4：demo-campus

- 建立最小第二主题。
- 验证非 ZJU world data、story、prompt、事件、论坛、私信、道具和成就路径。
- reference backend 能用 demo theme 做 smoke。

### Phase 5：主题契约加固

- 增加 `theme_contract` 校验。
- 让 `validate_world_data.py` 成为主题 CI/本地检查入口。
- 文档化必需文件、字段语义和新主题清单。

### Phase 6：最小 starter app

- 新增 `apps/starter/backend` 和 `apps/starter/frontend`。
- 后端以内存态跑通 auth、角色创建、WebSocket init/tick、事件、论坛、私信、道具和考试结算。
- 前端用生成的 theme/story/stat metadata 渲染最小界面。

### Phase 7：包化与版本

- `esimu-core` 变成可安装 Python 包。
- 增加 `__version__`、`py.typed`、changelog、release policy 和 CI。

### Phase 8：项目脚手架

- 新增 `new_project.py` 生成 starter 项目。
- 新增 `scaffold_world_data.py` 生成/追加世界数据片段。
- 新增 bootstrap smoke，验证生成项目能通过 world validation。

### Phase 9：框架就绪审查

- 结论：esimu 已可作为 alpha 级 library plus starter app。
- 当前不建议发布到 PyPI，继续使用 Git tag 作为 release channel。

## 当前框架决策

esimu 的推荐形态是：

```text
esimu-core + starter app + theme pack
```

其中：

- `esimu-core` 是版本化 Python 包。
- `apps/starter` 是新项目默认起点。
- `themes/<theme_id>` 是项目内容边界。
- `apps/zju-reference` 是高级参考适配器和回归目标，不是默认模板。

## 后续方向

优先考虑：

- starter 可选 Redis/PostgreSQL 持久化；
- starter 前端依赖锁定和 CI build/typecheck；
- 中性化 `cc98`/`dingtalk` 协议 ID；
- 用脚手架生成一个真实第二非 ZJU 模拟器；
- 再评估是否发布到 PyPI 或 GitHub Packages。

## 独立化路线图

接下来要把 esimu 从 ZJU 母仓子模块，推进成可以独立 clone、独立测试、独立发版的正式框架项目。

这里有两个不同终点：

- **仓库独立**：`pirate-608/esimu-lab` 不依赖 ZJU 母仓工作区也能安装、测试、构建文档和发布。
- **框架正式化**：esimu 具备清晰 starter 保证、版本文档、CI、发布策略和下游迁移路径。

仓库独立预计 Phase 10-11 可完成；框架正式化需要 Phase 12-14。

### Phase 10：移除母仓路径假设

目标：fresh clone 后无需 ZJU 母仓即可运行。

状态：core/starter/docs 路径已完成；reference app 兼容路径作为可选项留到 Phase 11 继续处理。

工作：

- 把 README、docs、测试和生成清单里的母仓路径改为仓库相对命令。
- 增加独立 `.venv`/Python 版本/安装说明。
- 让 quickstart 从 `git clone https://github.com/pirate-608/esimu-lab.git` 开始。
- 确保主题图片和 validation 不依赖 ZJU reference frontend public images。
- 修复假设 lab 位于 ZJU 母仓内部的测试。

完成标准：在 ZJU 仓库外 fresh clone 后，可运行 core tests、world validation 和 Zensical docs build。

进展：

- 根目录新增 `requirements-dev.txt`，作为 fresh clone 后的统一依赖入口。
- Quickstart 和 README 改为从 `git clone`、本仓 `.venv` 和相对命令开始。
- story 图片校验不再回退到 ZJU reference frontend public images，而是要求主题自带 assets。
- `zju` 与 `demo-campus` 主题已携带自己引用的 story 图片。
- `new_project.py` 现在校验源主题是否自带 story assets，不再借 reference frontend 文件。

### Phase 11：把 reference app 从默认框架路径中剥离

目标：不要让人误以为 ZJU reference app 是框架必需部分。

工作：

- 决定 `apps/zju-reference/` 是保留为兼容 fixture、移到 archival branch，还是变成可选下载测试资源。
- 默认 quickstart 只依赖 `esimu-core`、`apps/starter` 和主题包。
- CI 分成 required core/starter/docs 与 optional reference compatibility。
- 新项目生成和首页不再默认提 ZJU 路径。

完成标准：忽略 `apps/zju-reference/` 也不影响 core、starter、docs、主题校验和项目脚手架。

进展：

- README、quickstart、agent handoff 和发布检查都已把 `apps/starter/` 作为默认应用路径。
- 默认 CI 只必跑 core、starter 和 docs；ZJU reference backend job 只在手动
  `workflow_dispatch` 且 `run-reference=true` 时运行。
- CI 增加了 starter 与首页文档的 ZJU 可见专名扫描。
- reference 检查移入维护者附录：`reference-compatibility.md`。

### Phase 12：Starter 加固

目标：starter 足够支撑真实原型，而不只是玩具 demo。

进展补充：

- 原模拟器可复用的 AI 核心已迁入 `esimu_core.ai`，覆盖 OpenAI-compatible
  配置/transport、M2-her 角色消息、事件/论坛/私信/毕业生成、输出校验、effects
  限幅和三模式降级。
- starter 可通过 `ESIMU_CONTENT_MODE`、`ESIMU_LLM_*`、`ESIMU_RP_*` 选择性
  启用模型；默认 library 模式不访问网络。
- ZJU reference 复用 core provider、JSON parser 和 M2-her role contract，Redis
  内容池、向量检索和玩家密钥策略仍由兼容 adapter 持有。

工作：

- 加 starter 前端 lockfile 策略和 CI build/typecheck。
- 增加可选持久化方案：memory-only 默认、file/dev persistence、可选 Redis/PostgreSQL 示例。
- 扩展 starter smoke：auth、角色创建、tick、事件、论坛、私信、道具、考试、结局。
- 中性化 forum/messenger public IDs，把 `cc98`/`dingtalk` 留在 reference-only 兼容层。

完成标准：下游项目可以长期基于 starter 继续做原型，而不必立即复制 ZJU reference app。

进展：

- Starter backend 已有 `SessionStore` protocol、默认 memory store，以及
  `ESIMU_STARTER_SESSION_STORE=file` 控制的本地 JSON 文件开发存储。
- Starter WebSocket smoke 覆盖 init、relax、event、event choice、forum、
  messenger、item buy/sell、exam 和 ending。
- Starter public action 使用中性的 `forum`、`messenger` 命名；legacy
  `cc98`/`dingtalk` 留在 reference compatibility 范围。
- Starter frontend 已提交 pnpm lockfile，并进入 CI typecheck/build。
- `starter-contract.md` 记录 starter HTTP/WebSocket 表面、持久化扩展点和
  前端依赖策略。

### Phase 13：正式发布渠道

目标：确定 `esimu-core` 的官方分发方式。

工作：

- 决定继续 Git tag、GitHub Packages，还是 PyPI。
- 增加 release workflow。
- 发布版本化文档站。
- 明确 Python API、主题契约、starter 行为和脚手架输出的兼容政策。

完成标准：下游项目可以 pin `esimu-core` 版本、阅读对应文档并有意识升级。

### Phase 14：真实外部模拟器试炼

目标：用一个真正非 ZJU 模拟器证明 esimu 独立性。

工作：

- 在 esimu 仓库外用 `new_project.py` 创建第二个非 ZJU 模拟器。
- 将 demo-campus 占位内容替换成小而完整的可玩主题。
- 记录缺失 hook、契约不清晰、硬编码假设和 bootstrap 痛点。
- 将通用修复反馈回 esimu。

完成标准：外部模拟器无需复制 ZJU 专有产品代码即可运行。

### 独立里程碑

- Phase 10 后：**独立 clone 可运行**。
- Phase 11 后：**默认框架路径不依赖 ZJU reference**。
- Phase 12 后：**starter 可用于真实原型**。
- Phase 13 后：**版本化框架发布可信**。
- Phase 14 后：**被真实外部模拟器验证**。
