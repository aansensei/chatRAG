# presentation/api/auth

JWT auth + user management. Mounted at `/auth`.

## Endpoints

| Method | Path | Access | Purpose |
|---|---|---|---|
| POST | `/auth/login` | public | Email + password -> `{access_token, user}` |
| GET | `/auth/me` | any logged-in user | Current user profile |
| PATCH | `/auth/me` | any logged-in user | Self-service email/password change (requires current password) |
| GET | `/auth/users` | admin | List all users |
| POST | `/auth/users` | admin | Create a user (email, password, role, department, expiry) |
| PATCH | `/auth/users/{id}/expiry` | admin | Set/clear account expiry |
| PATCH | `/auth/users/{id}/department` | admin | Assign department (scopes which folders the user can see) |
| PATCH | `/auth/users/{id}/department-head` | admin | Toggle department-head flag |
| DELETE | `/auth/users/{id}` | admin | Remove a user (cannot self-delete) |

Every admin action on another user's account is logged via
`admin_audit_store.log_admin_action` — see `GET /metrics/admin-audit`.

## Auth model

- Tokens: HS256 JWT, `JWT_SECRET_KEY`/`JWT_ALGORITHM`/`JWT_EXPIRE_MINUTES` env vars. No refresh endpoint, no revocation/denylist — a token is valid until it expires (default 24h) even if the account is later deleted mid-session (checked lazily on next request via `get_current_user`, which 401s once the user row is gone).
- Passwords: bcrypt via `passlib`, 8-char minimum, no self-service reset flow (admin must set a new password by re-creating credentials — there is currently no admin "reset another user's password" endpoint either).
- First run: `bootstrap_admin()` seeds one admin account from `ADMIN_EMAIL`/`ADMIN_PASSWORD` if `users.db` is empty.
- Permissions: `get_collections` (used by `/chat`, `/ingest`) resolves to `None` (unrestricted) for admins/Ban Giám đốc, otherwise the caller's department folder + shared folders — see `shared/security/permissions.py`.
- Rate-limited: `/auth/*` shares the same per-IP budget as `/chat`/`/ingest`/`/memory` (`presentation/middleware/rate_limit.py`), which caps brute-force login attempts.

## Known gaps

No self-service password reset, no bulk/CSV user import, no session/device
visibility or forced logout, no cascade cleanup when a department/folder is
deleted while users still reference it.
