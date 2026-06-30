# presentation/api/auth

Currently a utility module, not a router — no `/auth/*` HTTP endpoints exist.

## What's here

`__init__.py` exposes `get_collections`, a FastAPI dependency used by
`/chat` and `/ingest` to scope every request to the folders the caller
is allowed to see.

```python
async def get_collections(x_api_key: str = Header(default="")) -> list[str]:
    if _DEV_MODE: return []          # no filter — see everything
    keys = _load_keys()              # parsed from API_KEYS env var
    if not x_api_key or x_api_key not in keys:
        raise HTTPException(401, "Invalid or missing API key")
    return keys[x_api_key]           # list of allowed collection names
```

## Env vars

| Var | Purpose |
|---|---|
| `DEV_MODE` | `"true"` (default) skips API-key check, returns empty filter |
| `API_KEYS` | JSON: `{"sk_xxx": ["folder1", "folder2"], "sk_yyy": ["*"]}` |

## Planned

`POST /auth/login` (JWT), `POST /auth/refresh`, `POST /auth/logout` —
needed before multi-user mode goes live.
