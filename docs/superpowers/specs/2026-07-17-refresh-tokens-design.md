# Refresh Tokens Design

## Context

Part of Phase 1 backend hardening (see `2026-07-16-backend-phase1-hardening-design.md`, section C, closes #69). Today the API issues a single JWT access token with an 8-day expiry and no revocation mechanism short of rotating `SECRET_KEY`, which invalidates every token for every user at once. The upcoming admin panel (Phase 2) needs a way to keep a session alive across the 8-day window without forcing a full re-login, and needs an actual logout action.

## Goals

- A `POST /auth/refresh` endpoint that exchanges a valid refresh token for a new access token.
- Refresh tokens are rotated on every use (single-use in practice) to bound the blast radius of a leaked token.
- Access and refresh tokens are unambiguously typed so one can never be substituted for the other.
- A real logout action that revokes the current session's refresh token.

## Non-goals

- Multi-device / multi-session support. This project has a small admin user base (superuser + a handful of accounts via the Phase 2 admin panel); single-session-per-user is sufficient and keeps the storage model and revocation logic simple. A `refresh_tokens` table supporting concurrent sessions is explicitly deferred — not needed at this scale.
- Refresh-token-family tracking / theft detection beyond "does the presented token match what's stored." At single-session scale, a mismatch already means the token is stale (rotated or logged out), which is enough signal.

## Design

### Data model

Add one nullable column to `User`:

```python
hashed_refresh_token: Mapped[str | None] = mapped_column(String, nullable=True)
```

Stores `sha256(refresh_token).hexdigest()` — not the raw token. SHA-256, not bcrypt: the refresh token is already a high-entropy random JWT (not a human-chosen, guessable secret), so bcrypt's deliberate key-stretching cost buys nothing here and would add latency to every `/auth/refresh` call for no security benefit. One Alembic migration adds the column (nullable, no backfill needed — existing sessions simply have no refresh token until their next login).

### Token claims

Both token-creation functions in `app/core/security.py` embed an explicit `"type"` claim:

```python
def create_access_token(subject, expires_delta=None) -> str:
    # existing behavior, plus: to_encode["type"] = "access"

def create_refresh_token(subject, expires_delta=None) -> str:
    # new function, mirrors create_access_token but: to_encode["type"] = "refresh",
    # plus a "jti": uuid.uuid4().hex claim (see note below)
```

Any endpoint that decodes a token checks `payload["type"]` matches what it expects, rejecting a token of the wrong type with 401. This closes the "a refresh token can be used anywhere an access token works, and vice versa" gap the earlier security review flagged as a token-confusion risk.

**Uniqueness note:** `create_refresh_token` must include a unique claim (`jti`, a random UUID) in its payload. JWT encoding is deterministic — two refresh tokens minted for the same user within the same second-resolution `exp` would otherwise produce byte-identical JWTs, which silently defeats the rotation guarantee below (an "old" token that's byte-identical to the "new" one trivially still matches). This was missed in the initial design pass and only surfaced once `/auth/refresh`'s rotation tests were written.

### Settings

Add `REFRESH_TOKEN_EXPIRE_DAYS: int = 30` to `app/core/config.py`'s `Settings`, following the existing pattern for `ACCESS_TOKEN_EXPIRE_MINUTES`.

### `Token` schema

`app/api/v1/domains/users/schemas/token.py`'s `Token` model gains:

```python
refresh_token: str = Field(..., title="Refresh Token", description="...", examples=[...])
```

### `POST /auth/login` (existing endpoint, extended)

On successful authentication: issue both an access token (unchanged 8-day expiry) and a refresh token (30-day expiry). Compute `sha256(refresh_token)` and store it in `User.hashed_refresh_token`. Return both tokens in the `Token` response.

### `POST /auth/refresh` (new endpoint)

Request body: `{"refresh_token": "<jwt>"}`.

Flow:
1. Decode the JWT. Invalid signature or malformed → 401.
2. Check `type == "refresh"` → else 401 ("wrong token type").
3. Check not expired (the `jose` library raises on decode for expired tokens by default) → 401 if expired.
4. Look up the user by `sub`. Not found or inactive → 401.
5. Compute `sha256(presented_token)` and compare against `user.hashed_refresh_token`. Mismatch → 401. This is what makes rotation double as reuse-detection: once a refresh token has been used (and the stored hash overwritten with the new one), presenting the old token again can never match.
6. On all checks passing: issue a *new* access token and a *new* refresh token, overwrite `hashed_refresh_token` with the new hash, return both in a `Token` response.

**Concurrency note:** steps 5–6 must be a single atomic compare-and-swap (`UPDATE ... WHERE hashed_refresh_token = <the hash just verified>`, checking the affected-row count), not a plain read-then-write. Two concurrent `/auth/refresh` calls presenting the same not-yet-rotated token would otherwise both pass step 5 before either commits step 6, both minting a valid pair from what should be a single-use token. This was missed in the initial design pass and only caught during an exhaustive post-implementation review.

Not rate-limited beyond the general 60/min limit — this endpoint requires possession of a valid refresh token already, unlike `/login` which accepts a guessable password, so it doesn't need the stricter 10/min auth limit.

### `POST /auth/logout` (new endpoint)

Gated by `get_current_user` (valid access token required). Sets `user.hashed_refresh_token = None` and commits. This is the actual revocation trigger the storage design exists to support — without it, the only way to invalidate a refresh token early is a password change (which already implicitly should clear it too — see Testing below).

**Scope limitation:** this revokes the refresh token only — it does not and cannot invalidate the caller's already-issued access token, which remains valid until its own expiry (up to `ACCESS_TOKEN_EXPIRE_MINUTES`) like any stateless JWT. "Logout" here means "this session can't be refreshed past its current access token," not "immediately revoke all access." Full access-token revocation would require a server-side blocklist, which is out of scope for this design (see Non-goals).

### Side effect: password change also revokes

`POST /reset-password/` should also clear `hashed_refresh_token` when it updates `hashed_password`, since a password reset is a natural point to kill any outstanding session. Small addition to an existing endpoint, not a new one.

## Testing

- Login returns both an access token and a refresh token, both correctly typed.
- `/auth/refresh` with a valid refresh token returns a new access + refresh pair; the new access token is usable against a protected endpoint.
- Reuse-after-rotation: calling `/auth/refresh` twice with the *same* (first) refresh token — second call is rejected 401.
- Type confusion: presenting an access token to `/auth/refresh` → 401. Presenting a refresh token as a Bearer access token to a protected endpoint → 401.
- Expired refresh token → 401.
- `/auth/logout` clears the stored hash; a subsequent `/auth/refresh` with the now-revoked token → 401.
- `/reset-password/` also revokes any outstanding refresh token (verify a pre-reset refresh token fails after the reset).

## Risks / open questions for planning

The single open question from the parent spec (session model) and the hashing algorithm were both resolved during this design's brainstorming. Three further risks were *not* caught at design time — noted here for the record, all found and fixed during implementation/review rather than during this design pass:

- **Same-second token collision** (see the "Uniqueness note" under Token claims above) — required adding a `jti` claim.
- **Rotation race condition** (see the "Concurrency note" under `POST /auth/refresh` above) — required an atomic compare-and-swap instead of a plain read-then-write.
- **Logout doesn't revoke the access token** (see the "Scope limitation" under `POST /auth/logout` above) — an inherent tradeoff of stateless JWTs, not a bug, but worth stating explicitly rather than letting "ending their session" imply more than it delivers.

None of these changed the overall design — they're implementation-level corrections within the shape already described above — but a future design pass in this codebase should treat "is token generation collision-resistant" and "is this read-check-write atomic under concurrency" as standard checklist items, not afterthoughts.
