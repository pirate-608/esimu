# Beta Support Policy

`esimu-core 0.3.0b1` targets single-theme narrative simulator prototypes. It is
currently prepared on `main` and remains unpublished until the release gate.

Supported in this Beta:

- Python 3.11–3.13;
- one selected theme per deployment;
- theme schema v1 plus state/WebSocket protocol v2;
- automatic state-v1 migration and protocol-v1 client acceptance;
- the generated Vue/Pinia Starter;
- SQLite for single-node persistence;
- optional OpenAI-compatible content generation with local fallback.
- installed `new/validate/doctor/inspect/sync/add/version` commands.

Not promised by this Beta:

- runtime multi-theme switching;
- a production identity provider or multi-tenant authorization;
- Redis/PostgreSQL adapters, distributed locks, or horizontal scaling;
- a separately versioned npm component package;
- backward compatibility with arbitrary pre-release lab snapshots.

Breaking Beta changes increment the minor version and include a migration
guide. Patch releases may reject data that was already invalid under the
published contract.
