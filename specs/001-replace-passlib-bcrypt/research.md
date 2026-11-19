# Research: Replace passlib with direct bcrypt

## Current behavior (measured against the running app, 2026-11-18)

| Case | Today (passlib + monkeypatch) |
|---|---|
| Hash format | `$2b$12$...` (cost 12) |
| 72 / 200-byte / empty / multibyte passwords | hash and verify OK; a 72-byte hash verifies the 200-byte original (truncation is by bytes) |
| Malformed stored hash (`notahash`, empty string) | raises `UnknownHashError` |
| Truncated bcrypt salt (`$2b$12$short`) | raises `ValueError` |
| `$2y$` prefixed hash | verifies without error |
| `None` stored hash | returns `False` |
| NUL byte in password | `PasswordValueError` (a `ValueError`) on hash |
| bcrypt 5.0.0 without the monkeypatch | passlib import-time backend probe crashes (`__about__` missing, then 72-byte `ValueError`) |

## Decisions

1. **Use `bcrypt` directly.**
   - Rationale: it is already installed, maintained, and the only backend passlib used. passlib adds nothing for a single scheme; `deprecated="auto"` is inert with one scheme.
   - Alternatives: pin `bcrypt<5` and keep the patch (still depends on abandoned code); `argon2-cffi` (requires rehashing every user, out of scope).
2. **Explicit byte truncation to 72.** bcrypt 5 raises on longer input; truncating preserves today's semantics for stored hashes of long passwords.
3. **Cost 12 explicit.** Same as existing hashes; stated in code so a library default change cannot silently alter it.
4. **Fail closed on `ValueError` in verify.** Removes a 500-able path; the NUL-byte and malformed-hash cases both land here.
5. **`get_password_hash` NUL byte still raises `ValueError`.** Preserves passlib's rejection; request schemas are the boundary validation layer.

## Not doing (YAGNI)

Rehash-on-login, configurable rounds, a hashing service class, `$2a$`/`$2y$` normalization beyond what the library does natively.
