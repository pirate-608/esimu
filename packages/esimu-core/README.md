# esimu-core

`esimu-core` is the typed, I/O-independent core and project CLI for esimu.

```powershell
python -m pip install "esimu-core[ai]==0.2.0b4"
esimu version
esimu new D:\projects\my-simulator --theme-id my-simulator
esimu validate --root D:\projects\my-simulator --theme my-simulator
```

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

See `https://esimu.67656.fun/` for the authoring and compatibility guides.
