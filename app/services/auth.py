import asyncio
import httpx
import logging
import re
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

_cache      = {"token": None, "expires_at": 0}
_token_lock = asyncio.Lock()

# ─── TOKEN AUTH0 ──────────────────────────────────────────────────────────────
async def get_token() -> str:
    now = time.time()
    if _cache["token"] and now < _cache["expires_at"] - 60:
        return _cache["token"]

    async with _token_lock:
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
        logger.info("Token renovado, expira en %ds", d.get("expires_in", 3600))
        return _cache["token"]

async def _headers() -> dict:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {await get_token()}",
    }

# ─── PATH SAFETY ──────────────────────────────────────────────────────────────
_SAFE_SEG = re.compile(r'^[\w\s\-\.]+$')

def _safe_path_segment(value: str) -> str:
    """Rechaza valores con caracteres que permiten path traversal."""
    if not _SAFE_SEG.match(value):
        raise HTTPException(status_code=400, detail="Parametro de ruta invalido")
    return value

# ─── HELPERS KAME ─────────────────────────────────────────────────────────────
def _raise_kame_error(r: httpx.Response, context: str) -> None:
    logger.error("KAME %s -> HTTP %d: %s", context, r.status_code, r.text[:200])
    raise HTTPException(status_code=r.status_code,
                        detail=f"Error KAME ({context}): {r.text[:200]}")

async def kame_get(path: str, params: dict = None):
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{KAME_BASE_URL}{path}", headers=await _headers(), params=params)
            if not r.is_success:
                _raise_kame_error(r, f"GET {path}")
            return r.json() if r.content else {}
    except HTTPException:
        raise
    except httpx.TimeoutException:
        logger.error("Timeout KAME GET %s", path)
        raise HTTPException(status_code=504, detail=f"Timeout KAME: GET {path}")
    except Exception as e:
        logger.exception("Error KAME GET %s", path)
        raise HTTPException(status_code=502, detail=f"Error KAME: {e}")

async def kame_post(path: str, body: dict):
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            logger.info("KAME POST %s payload=%s", path, body)
            r = await c.post(f"{KAME_BASE_URL}{path}", headers=await _headers(), json=body)
            logger.info("KAME POST %s → HTTP %d body=%s", path, r.status_code, r.text[:500])
            if not r.is_success:
                _raise_kame_error(r, f"POST {path}")
            data = r.json() if r.content else {}
            # KAME devuelve HTTP 200 con {"Estado":"Error"} para errores de negocio
            if isinstance(data, dict) and data.get("Estado") == "Error":
                errores = data.get("Error", [])
                msg = "; ".join(e.get("ErrorMessage", "") for e in errores) if errores else str(data)
                logger.error("KAME negocio error POST %s: %s", path, msg)
                raise HTTPException(status_code=422, detail=f"Error KAME: {msg}")
            return data
    except HTTPException:
        raise
    except httpx.TimeoutException:
        logger.error("Timeout KAME POST %s", path)
        raise HTTPException(status_code=504, detail=f"Timeout KAME: POST {path}")
    except Exception as e:
        logger.exception("Error KAME POST %s", path)
        raise HTTPException(status_code=502, detail=f"Error KAME: {e}")

async def kame_put(path: str, body: dict):
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            logger.info("KAME PUT %s payload=%s", path, body)
            r = await c.put(f"{KAME_BASE_URL}{path}", headers=await _headers(), json=body)
            logger.info("KAME PUT %s → HTTP %d body=%s", path, r.status_code, r.text[:500])
            if not r.is_success:
                _raise_kame_error(r, f"PUT {path}")
            data = r.json() if r.content else {}
            if isinstance(data, dict) and data.get("Estado") == "Error":
                errores = data.get("Error", [])
                msg = "; ".join(e.get("ErrorMessage", "") for e in errores) if errores else str(data)
                logger.error("KAME negocio error PUT %s: %s", path, msg)
                raise HTTPException(status_code=422, detail=f"Error KAME: {msg}")
            return data
    except HTTPException:
        raise
    except httpx.TimeoutException:
        logger.error("Timeout KAME PUT %s", path)
        raise HTTPException(status_code=504, detail=f"Timeout KAME: PUT {path}")
    except Exception as e:
        logger.exception("Error KAME PUT %s", path)
        raise HTTPException(status_code=502, detail=f"Error KAME: {e}")

# ─── LIFESPAN ─────────────────────────────────────────────────────────────────
async def _warmup_maestro():
    """Pre-calienta el caché del maestro en background tras el arranque."""
    await asyncio.sleep(3)   # espera breve para que KAME no colisione con get_token
    try:
        from app.routers.maestro import _get_cached_articulos   # import tardío → sin circular
        items = await _get_cached_articulos()
        logger.info("Cache maestro pre-calentado: %d artículos", len(items))
    except Exception as exc:
        logger.warning("No se pudo pre-calentar cache maestro: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando FDL KAME API...")
    try:
        await get_token()
        logger.info("Token inicial OK")
    except Exception as exc:
        logger.warning("No se pudo obtener token inicial: %s", exc)

    asyncio.create_task(_warmup_maestro())   # no bloquea el arranque
    yield
    logger.info("Cerrando FDL KAME API")
