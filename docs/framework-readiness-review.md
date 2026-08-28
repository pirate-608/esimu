# Beta Readiness Review

esimu `0.3.0b2` is the next source candidate. Published `0.2.0b5` already
passed TestPyPI and external-example gates; 0.3 adds the runtime closure and
installed authoring commands before its own release gate.

Ready locally: typed core, versioned theme/state/protocol contracts, wheel-owned
`esimu new`, installed authoring CLI, strict theme validation, optional AI,
Vue/Pinia Starter, non-blocking content tasks, automatic events/messenger,
cooldowns, declarative achievements, Game Over, ordered save/exit, SQLite
restart persistence, release smoke, and bilingual Zensical 0.0.57 docs.

Remaining before publishing 0.3: push the candidate, pass clean-checkout CI,
exercise the wheel in the external example, and validate the immutable
TestPyPI candidate before creating the final tag.

Deliberately deferred: runtime multi-theme, production identity, distributed
persistence, an npm package, and stable 1.0 guarantees. See the Beta support
policy and release policy for exact boundaries.
