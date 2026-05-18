import httpx, time, os
from contextlib import asynccontextmanager
from fastapi import FastAPI

AUTH0_DOMAIN        = os.getenv("AUTH0_DOMAIN", "")
AUTH0_CLIENT_ID     = os.getenv("AUTH0_CLIENT_ID", "")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET", "")
AUTH0_AUDIENCE      = os.getenv("AUTH0_AUDIENCE", "")
KAME_BASE_URL       = os.getenv("KAME_BASE_URL", "https://api.kameone.cl")

_cache = {"token": None, "expires_at": 0}

async def get_token() -> str:
    now = time.time()
    if _cache["token"] and now < _cache["expires_at"] - 60:
        return _cache["token"]
    async with httpx.AsyncClient() as c:
        r = await c.post(
            f"https://{AUTH0_DOMAIN}/oauth/token",
            json={"client_id": AUTH0_CLIENT_ID, "client_secret": AUTH0_CLIENT_SECRET,
                  "audience": AUTH0_AUDIENCE, "grant_type": "client_credentials"}
        )
        r.raise_for_status()
        d = r.json()
    _cache["token"] = d["access_token"]
    _cache["expires_at"] = now + d.get("expires_in", 3600)
    return _cache["token"]

async def _headers():
    return {"Content-Type": "application/json", "Authorization": f"Bearer {await get_token()}"}

async def kame_get(path: str, params: dict = None):
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(f"{KAME_BASE_URL}{path}", headers=await _headers(), params=params)
        r.raise_for_status()
        return r.json() if r.content else {}

async def kame_post(path: str, body: dict):
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{KAME_BASE_URL}{path}", headers=await _headers(), json=body)
        r.raise_for_status()
        return r.json() if r.content else {}

async def kame_put(path: str, body: dict):
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.put(f"{KAME_BASE_URL}{path}", headers=await _headers(), json=body)
        r.raise_for_status()
        return r.json() if r.content else {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    if AUTH0_CLIENT_ID and AUTH0_CLIENT_SECRET:
        try:
            await get_token()
            print("✅ Token Auth0 OK")
        except Exception as e:
            print(f"⚠️  Token error: {e}")
    yield
