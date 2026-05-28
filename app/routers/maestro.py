import asyncio
import time
from fastapi import APIRouter
from app.services.auth import kame_get

router = APIRouter()

# ─── CACHE EN MEMORIA ─────────────────────────────────────────────────────────
# Evita re-fetchear 87+ páginas de KAME por cada usuario que abre la app.
# TTL: 30 minutos. Con 8.698+ artículos esto es crítico para no exceder
# el rate limit de 180 req/min cuando varios usuarios cargan simultáneamente.
_articles_cache: dict = {"items": [], "ts": 0.0}
CACHE_TTL = 30 * 60  # 30 minutos en segundos
_cache_lock = asyncio.Lock()


async def _fetch_page(page: int, per_page: int, retries: int = 3) -> list:
    """Descarga una página con reintentos. Nunca falla silenciosamente."""
    for attempt in range(retries):
        try:
            data = await kame_get("/api/Maestro/getListArticulo", {"page": page, "per_page": per_page})
            if isinstance(data, dict):
                return data.get("items", [])
        except Exception:
            if attempt < retries - 1:
                await asyncio.sleep(1)
    return []  # Solo si agotó reintentos


async def _fetch_first_page(per_page: int = 100, retries: int = 4) -> dict:
    """Primera página con backoff exponencial para sobrevivir 429 al arrancar."""
    for attempt in range(retries):
        try:
            data = await kame_get("/api/Maestro/getListArticulo", {"page": 1, "per_page": per_page})
            if isinstance(data, dict) and "items" in data:
                return data
        except Exception:
            pass
        if attempt < retries - 1:
            espera = 2 ** attempt   # 1s, 2s, 4s
            await asyncio.sleep(espera)
    return {}


async def _fetch_all_articulos() -> list:
    """Descarga todas las páginas de artículos desde KAME en paralelo (batch=5).
    Cada página tiene 3 reintentos. La primera página tiene backoff exponencial."""
    first = await _fetch_first_page()
    if not first:
        raise RuntimeError("No se pudo obtener la primera página del maestro tras reintentos")

    total       = first.get("total", 0)
    per_page    = first.get("per_page", 100)
    total_pages = max(1, (total + per_page - 1) // per_page)
    all_items   = list(first.get("items", []))

    # Batch de 5 para no saturar rate limit de KAME (180 req/min)
    for batch_start in range(2, total_pages + 1, 5):
        batch = list(range(batch_start, min(batch_start + 5, total_pages + 1)))
        results = await asyncio.gather(*[_fetch_page(p, per_page) for p in batch])
        for page_items in results:
            all_items.extend(page_items)

    return all_items


async def _get_cached_articulos() -> list:
    """Devuelve artículos desde caché si es válido, sino re-fetchea.
    Si el fetch falla pero hay datos stale, los retorna en vez de fallar."""
    async with _cache_lock:
        if time.time() - _articles_cache["ts"] < CACHE_TTL and _articles_cache["items"]:
            return _articles_cache["items"]
        try:
            items = await _fetch_all_articulos()
            _articles_cache["items"] = items
            _articles_cache["ts"]    = time.time()
            return items
        except Exception:
            if _articles_cache["items"]:
                # Datos expirados pero mejor que un error
                return _articles_cache["items"]
            raise


# ─── ENDPOINTS ────────────────────────────────────────────────────────────────

@router.get("/articulos")
async def get_list_articulo(page: int = 1, per_page: int = 100):
    return await kame_get("/api/Maestro/getListArticulo", {"page": page, "per_page": per_page})


@router.get("/articulos/todos")
async def get_all_articulos():
    """Todos los artículos con todos los campos. Usa caché 30 min."""
    items = await _get_cached_articulos()
    return {"items": items, "total": len(items)}


@router.get("/articulos/slim")
async def get_articulos_slim():
    """Solo SKU + Descripcion + Familia. Payload ~90% más liviano para la PWA.
    Ideal para carga inicial con 8.000+ artículos y usuarios simultáneos."""
    items = await _get_cached_articulos()
    slim = [
        {
            "SKU":        a.get("SKU") or a.get("sku") or "",
            "Descripcion": a.get("Descripcion") or a.get("descripcion") or "",
            "Familia":    a.get("Familia") or a.get("familia") or "",
        }
        for a in items
    ]
    return {"items": slim, "total": len(slim)}


@router.get("/articulos/cache-status")
async def cache_status():
    """Diagnóstico: cuándo se llenó el caché y cuántos artículos tiene."""
    age = int(time.time() - _articles_cache["ts"])
    return {
        "cached": bool(_articles_cache["items"]),
        "count":  len(_articles_cache["items"]),
        "age_seconds": age,
        "expires_in_seconds": max(0, CACHE_TTL - age),
    }


@router.delete("/articulos/cache")
async def invalidate_cache():
    """Fuerza refresco del caché en el próximo request."""
    async with _cache_lock:
        _articles_cache["ts"] = 0.0
    return {"invalidated": True}


@router.get("/vendedores")
async def get_list_vendedor():
    return await kame_get("/api/Maestro/getListVendedor")


@router.get("/unidades-negocio")
async def get_list_unidad_negocio():
    return await kame_get("/api/Maestro/getListUnidadNegocio")


@router.get("/fichas")
async def get_list_ficha():
    return await kame_get("/api/Maestro/getListFicha")
