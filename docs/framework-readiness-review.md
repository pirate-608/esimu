# Beta Readiness Review

esimu `0.4.0b2` is the current public Beta. It passed the clean-checkout matrix,
TestPyPI installation, and the independent `esimu-beta-example` Docker trial
before its PyPI and GitHub prerelease.

Ready locally: typed core, versioned theme/state/protocol contracts, wheel-owned
`esimu new`, installed authoring CLI, strict theme validation, optional AI,
Vue/Pinia Starter, non-blocking content tasks, automatic events/messenger,
cooldowns, declarative achievements, Game Over, ordered save/exit, SQLite
restart persistence, release smoke, and bilingual Zensical 0.0.57 docs.

The 0.4 release gate is complete. Future releases must repeat the same
candidate, external-install, artifact, and clean-environment checks.

Deliberately deferred: runtime multi-theme, production identity, distributed
persistence, an npm package, and stable 1.0 guarantees. See the Beta support
policy and release policy for exact boundaries.
