# esimu-core

`esimu-core` is the typed, I/O-independent core and project CLI for esimu.

```powershell
python -m pip install -e ".[ai]"  # 0.4.0b2 source candidate
esimu version
esimu new D:\projects\my-simulator --theme-id my-simulator
esimu validate --root D:\projects\my-simulator --theme my-simulator
esimu doctor --root D:\projects\my-simulator --theme my-simulator
esimu inspect --root D:\projects\my-simulator --theme my-simulator
esimu sync --root D:\projects\my-simulator --theme my-simulator
esimu dev --root D:\projects\my-simulator --theme my-simulator
esimu reload --root D:\projects\my-simulator --theme my-simulator
esimu build --root D:\projects\my-simulator --theme my-simulator
```

`esimu new` defaults to the self-contained `zju-simplified` source theme. Pass
`--source-theme demo-campus` for the neutral template.

The base dependency is Pydantic. The optional `ai` extra adds the OpenAI SDK
transport. FastAPI, SQLite, WebSocket, and Vue live in the generated Starter,
not in the core package.

Core owns:

- theme and world-data contracts;
- stat, item, effect, semester, and lifecycle rules;
- runtime timing, state, payload, cooldown, and task helpers;
- neutral event, forum, and messenger content contracts;
- optional AI configuration, parsing, generation, and fallback policy;
- the self-contained `esimu new` scaffold bundle.
- installed diagnostics, metadata sync, and safe world-entry authoring commands.

See `https://esimu.67656.fun/` for the authoring and compatibility guides.
