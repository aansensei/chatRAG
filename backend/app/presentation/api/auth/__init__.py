import json
import os

from fastapi import Header, HTTPException

_DEV_MODE = os.environ.get("DEV_MODE", "true").lower() == "true"


def _load_keys() -> dict[str, list[str]]:
    raw = os.environ.get("API_KEYS", "")
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


async def get_collections(x_api_key: str = Header(default="")) -> list[str]:
    if _DEV_MODE:
        return []  # no filter — can see all collections

    keys = _load_keys()
    if not x_api_key or x_api_key not in keys:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return keys[x_api_key]
