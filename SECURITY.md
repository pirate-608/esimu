# Security Policy

Security fixes are provided for the latest published Beta line only. Do not
open a public issue for a vulnerability that could expose credentials, private
content, generated-project tokens, or deployment data. Report it privately
through GitHub Security Advisories for `pirate-608/esimu`.

The Starter is a local-profile reference application, not an account system.
Its opaque token grants access to the corresponding local save. Deployments
must use HTTPS, protect their SQLite file, keep model keys server-side, and add
their own authentication before accepting untrusted public users.

