# Starter App Shape

`apps/starter` is the only canonical application base. `esimu new` copies it
from the installed wheel and patches the selected theme, package dependency,
generated metadata, README, environment template, and Agent handoff.

Keep reusable pure logic in `esimu-core`; keep FastAPI, SQLite, WebSocket, and
Vue integration in the generated project. Projects may replace any adapter,
but should preserve versioned theme/state/protocol boundaries when upgrading.
