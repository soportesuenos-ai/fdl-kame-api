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

_kame_client = None
_client_lock = asyncio.Lock()

async def _get_client():
    global _kame_client
    if _kame_client is None or _kame_client.is_closed:
        async with _client_lock:
            if _kame_client is None or _kame_client.is_closed:
                _kame_client = httpx.AsyncClient(
                    timeout=httpx.Timeout(30.0, connect=10.0),
                    limits=httpx.Limits(
                        max_connections=30,
                        max_keepalive_connections=15,
                        keepalive_expiry=30,
                    ),
                )
                logger.info("Cliente httpx compartido inicializado")
    return _kame_client


async def get_token():
    now = time.time()
    if _cache["token"] and now < _cache["expires_at"] - 60:
        return _cache["token"]

    async with _token_lock:
        now = time.time()
        if _cache["token"] and now < _cache["expires_at"] - 60:
            return _cache["token"]

        logger.info("Renovando token Auth0...")
        client = await _get_client()
        r = await client.post(
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

async def _headers():
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {await get_token()}",
    }

_SAFE_SEG = re.compile(r'^[\w\s\-\.]+$')

def _safe_path_segment(value):
    if not _SAFE_SEG.match(value):
        raise HTTPException(status_code=400, detail="Parametro de ruta invalido")
    return value

def _raise_kame_error(r, context):
    logger.error("KAME %s -> HTTP %d: %s", context, r.status_code, r.text[:200])
    raise HTTPException(status_code=r.status_code,
                        detail=f"Error KAME ({context}): {r.text[:200]}")

async def kame_get(path, params=None):
    try:
        client = await _get_client()
        r = await client.get(f"{KAME_BASE_URL}{path}", headers=await _headers(), params=params)
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

async def kame_post(path, body):
    try:
        client = await _get_client()
        logger.info("KAME POST %s payload=%s", path, body)
        r = await client.post(f"{KAME_BASE_URL}{path}", headers=await _headers(), json=body)
        logger.info("KAME POST %s -> HTTP %d body=%s", path, r.status_code, r.text[:500])
        if not r.is_success:
            _raise_kame_error(r, f"POST {path}")
        data = r.json() if r.content else {}
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

async def kame_put(path, body):
    try:
        client = await _get_client()
        logger.info("KAME PUT %s payload=%s", path, body)
        r = await client.put(f"{KAME_BASE_URL}{path}", headers=await _headers(), json=body)
        logger.info("KAME PUT %s -> HTTP %d body=%s", path, r.status_code, r.text[:500])
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
        raise HTTPException(status_code=502, detail=f"Timeout KAME: PUT {path}")
    except Exception as e:
        logger.exception("Error KAME PUT %s", path)
        raise HTTPException(status_code=502, detail=f"Error KAME: {e}")

async def _warmup_maestro():
    await asyncio.sleep(3)
    try:
        from app.routers.maestro import _get_cached_articulos
        items = await _get_cached_articulos()
        logger.info("Cache maestro pre-calentado: %d articulos", len(items))
    except Exception as exc:
        logger.warning("No se pudo pre-calentar cache maestro: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando FDL KAME API...")
    await _get_client()
    try:
        await get_token()
        logger.info("Token inicial OK")
    except Exception as exc:
        logger.warning("No se pudo obtener token inicial: %s", exc)

    asyncio.create_task(_warmup_maestro())
    yield
    global _kame_client
    if _kame_client and not _kame_client.is_closed:
        await _kame_client.aclose()
        logger.info("Cliente httpx cerrado")
    logger.info("Cerrando FDL KAME API")
