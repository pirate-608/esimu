# 参考应用兼容性

`apps/zju-reference/` 保留为可选的高兼容参考适配器。它不是默认框架路径。

当一个改动需要验证原 ZJUers Simulator 的复杂表面时，再使用它：例如
Redis 存档、SQLAdmin 管理页、兼容 DingTalk 的私信行为、兼容 CC98 的论坛行为，
或复制来的生产前端 shell。

## 默认路径

普通框架开发只应默认验证：

```text
esimu-core + apps/starter + theme pack + docs
```

这是新模拟器项目应该优先理解的路径。即使忽略 `apps/zju-reference/`，它也应继续可用。

## 什么时候运行 reference 检查

触碰以下内容时再运行 reference 检查：

- legacy `cc98` 或 `dingtalk` 内部 ID；
- reference backend adapter；
- reference frontend metadata/runtime 代码；
- Redis/PostgreSQL 存档兼容；
- admin 世界数据编辑器；
- 从 ZJUers Simulator 复制来的内容生成 fallback 行为。

## 命令

Reference backend：

```powershell
cd esimu-lab\apps\zju-reference\zjus-backend
python -m pytest tests\unit\test_demo_campus_reference_smoke.py
python -m pytest tests\unit\test_game_state.py tests\unit\test_dingtalk_state.py
python -m ruff check app tests\unit
```

Reference frontend：

```powershell
cd esimu-lab\apps\zju-reference\zjus-frontend
npx vitest run src\utils\theme.spec.ts
npx vitest run src\components\themeRuntime.spec.js
npx vue-tsc --noEmit
```

CI 中这些检查是手动可选路径。默认必跑 job 是 core、starter 和 docs。
