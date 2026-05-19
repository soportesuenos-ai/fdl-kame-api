import asyncio
import httpx
import logging
import time
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException

logger = logging.getLogger("fdl-kame-api.auth")

AUTH0_DOMAIN        = os.getenv("AUTH0_DOMAIN", "")
AUTH0_CLIENT_ID     = os.getenv("AUTH0_CLIENT_ID", "")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET", "")
AUTH0_AUDIENCE      = os.getenv("AUTH0_AUDIENCE", "")
KAME_BASE_URL       = os.getenv("KAME_BASE_URL", "https://api.kameone.cl")

_cache = {"token": None, "expires_at": 0}
_token_lock = asyncio.Lock()

# ─── TOKEN AUTH0 ──────────────────────────────────────────────────────────────
async def get_token() -> str:
    now = time.time()
    if _cache["token"] and now < _cache["expires_at"] - 60:
        return _cache["token"]

    async with _token_lock:
        # Re-check dentro del lock para evitar doble refresh
        now = time.time()
        if _cache["token"] and now < _cache["expires_at"] - 60:
            return _cache["token"]

        logger.info("Renovando token Auth0...")
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(
                f"https://{AUTH0_DOMAIN}/oauth/token",
                json={
                    "client_id":     AUTH0_CLIENT_ID,
                    "client_secret": AUTH0_CLIENT_SECRET,
                    "audience":      AUTH0_AUDIENCE,
                    "grant_type":    "client_credentials",
                },
            )
            r.raise_for_status()
            d = r.json()

        _cache["token"]      = d["access_token"]
        _cache["expires_at"] = now + d.get("expires_in", 3600)
        logger.info("Token Auth0 renovado, expira en %ds", d.get("expires_in", 3600))
        return _cache["token"]

async def _headers() -> dict:
    return {"Content-Type": "application/json", "Authorization": f"Bearer {await get_token()}"}

# ─── HELPERS KAME ───────────────────────────────────────────────────────────�