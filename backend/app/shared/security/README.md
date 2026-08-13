# shared/security

## `permissions.py`

Department-based access control, used by `presentation/api/auth/__init__.py`:

- `is_admin_or_leadership(user)` — admins and Ban Giám đốc see every collection, unrestricted.
- `can_read_collection(user, collection_name)` — everyone else: their own department's folder plus shared/non-department folders.

JWT signing/verification is not here — it's inline in
`presentation/api/auth/__init__.py` (`_create_access_token`, `get_current_user`),
using `python-jose` with `JWT_SECRET_KEY`. No token revocation/denylist exists —
tokens are valid until they expire (`JWT_EXPIRE_MINUTES`, default 24h).
