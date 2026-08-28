# AI Integration

esimu includes an optional framework AI module for theme-aware content
generation. Model access remains reusable without becoming mandatory for
deterministic or library-mode games.

## Package Boundary

The module lives under `esimu_core.ai` and provides:

- validated OpenAI-compatible provider/model configuration;
- generic and MiniMax M2-her role profiles;
- lazy optional OpenAI SDK transport;
- shared-platform versus session-sensitive client lifecycle helpers;
- defensive JSON/fenced-output parsing;
- theme-aware event, forum, messenger, reply, and graduation generation;
- stat-registry effect allowlists and delta clamps;
- `library`, `hybrid`, and `ai` resolution with local degradation.

The base package still depends only on Pydantic. Install the AI extra for the
bundled transport:

```powershell
python -m pip install -e ".[ai]"
```

Applications may instead implement the small `ChatTransport` protocol.

## Starter Configuration

The starter is local-library-first by default. The environment selects the
initial mode and available transports; each persisted player session may then
switch its own mode through the `set_mode` action without affecting others.

```text
ESIMU_CONTENT_MODE=library
```

Enable a general OpenAI-compatible endpoint:

```powershell
$env:ESIMU_CONTENT_MODE='hybrid' # library, hybrid, or ai
$env:ESIMU_LLM_PROVIDER='qwen'
$env:ESIMU_LLM_MODEL='qwen-plus'
$env:ESIMU_LLM_API_KEY='...'
$env:ESIMU_LLM_BASE_URL='https://example.com/v1' # optional custom endpoint
$env:ESIMU_LLM_TIMEOUT_SECONDS='20'
$env:ESIMU_HYBRID_AI_PROBABILITY='0.35'
```

Local Ollama needs no API key:

```powershell
$env:ESIMU_CONTENT_MODE='ai'
$env:ESIMU_LLM_PROVIDER='ollama'
$env:ESIMU_LLM_MODEL='qwen3:8b'
```

Optionally route messenger role play through MiniMax M2-her:

```powershell
$env:ESIMU_RP_PROVIDER='minimax'
$env:ESIMU_RP_MODEL='M2-her'
$env:ESIMU_RP_API_KEY='...'
$env:ESIMU_RP_BASE_URL='https://api.minimaxi.com/v1'
```

M2-her keeps its documented `user_system`, `group`, and sample-message roles.
Its transport uses `max_completion_tokens`; generic endpoints use `max_tokens`.

## Degradation Rules

| Mode | Behavior |
| --- | --- |
| `library` | Never calls a model. |
| `hybrid` | Selects AI by configured probability and falls back to the other source. |
| `ai` | Calls AI first; timeout, exception, empty, or invalid output falls back locally. |

Generated event and messenger effects are filtered through
`world/stat_definitions.json`. Unknown fields are discarded and accepted
deltas are clamped before they reach an application session.

Messenger replies use a two-phase flow: the player message is persisted and
emitted immediately, then model generation runs in a per-contact deduplicated
background task. Every third player reply closes and settles one round.

## Adapter Responsibilities

Core does not own Redis/database content caches, browser-submitted API keys,
billing, quotas, moderation, pgvector retrieval, WebSocket emission, or save
schemas. Use `OpenAITransportRegistry.shared()` only for deployment credentials.
Use `session()` for player-provided credentials, close it after use, and never
put that player's generated content into a shared content pool.

Production-specific adapters may add Redis pools or vector retrieval while
retaining the same transport, parsing, and role contracts.
