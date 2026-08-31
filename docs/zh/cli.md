# CLI 参考

安装后的 `esimu` 命令负责项目生成、校验、诊断、metadata 同步和保守的世界数据
编辑。

`dev/reload/build` 已包含在公开 PyPI 版本 `0.4.0b2` 中。

## 项目命令

```powershell
esimu version
esimu new <target> --project-name "My Simulator" --theme-id my-simulator
esimu validate --root . --theme my-simulator
esimu doctor --root . --theme my-simulator
esimu inspect --root . --theme my-simulator
esimu dev --root . --theme my-simulator
esimu reload --root . --theme my-simulator
esimu build --root . --theme my-simulator
```

- `new` 从 wheel 复制 Starter 和源主题，生成独立项目并固定 core 依赖。
- `validate` 校验完整主题/世界契约，作者错误会返回非零状态。
- `doctor` 检查 Python/core、主题、生成 metadata、Starter 路径、
  Node/corepack/pnpm、SQLite 路径和 AI 配置状态，但不输出 secret。
- `inspect` 输出契约版本、解析后的路径、生成目标和世界数据数量。
- `dev` 会同步并校验主题、在缺少时安装前端依赖，然后以前台 supervisor
  同时运行 Uvicorn 与 Vite。
- `reload` 先同步并校验主题，再要求正在运行的 dev supervisor 以原端口重启
  两个服务。
- `build` 同步 metadata、校验世界数据、编译后端 Python，并生成
  `apps/starter/frontend/dist`。加入 `--no-install` 可在缺依赖时直接失败。

`doctor`、`inspect` 可加 `--json` 用于自动化。

## Metadata 同步

```powershell
esimu sync --root . --theme my-simulator
esimu sync --root . --theme my-simulator --write
```

不加 `--write` 时只检查 theme/story/stat TypeScript metadata，过期即失败。显式
写入会先校验主题，再原子替换全部生成文件；失败时恢复原文件。

## 世界数据编辑

```powershell
esimu add stat focus --root . --theme my-simulator --label 专注 --show-in-hud
esimu add item focus_card --root . --theme my-simulator --name 专注卡
esimu add achievement first_win --root . --theme my-simulator --name 第一次胜利
esimu add event campus_moment --root . --theme my-simulator --title 校园一刻
esimu add course systems --root . --theme my-simulator --plan GEN --semester 2
esimu add prompt graduation_instruction --root . --theme my-simulator --text "..."
```

`add` 默认只输出 JSON 预览。审查后才加入 `--write`；写入会更新一个源文件、同步
metadata、校验完整主题，并在失败时回滚源文件和生成文件。

属性常用参数包括 `--allocatable`、`--adjust-budget`、`--allow-item-effect`、
`--allow-event-effect` 和 `--llm-context`。成就条件使用
`--scope/--key/--op/--value`。事件草稿固定生成两个选项，以满足 Starter 契约。

## 兼容入口

`esimu-validate-world` 在 0.4 Beta 期间仍是 `esimu validate` 的别名。生成项目中的
源码脚本也保留一个 Beta 周期；新的 CI 和 Agent 自动化应调用安装后的 `esimu`。
