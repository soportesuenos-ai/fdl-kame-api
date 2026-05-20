import asyncio
from fastapi import APIRouter
from app.services.auth import kame_get

router = APIRouter()

@router.get("/articulos")
async def get_list_articulo(page: int = 1, per_page: int = 100):
    return await kame_get("/api/Maestro/getListArticulo", {"page": page, "per_page": per_page})

@router.get("/articulos/todos")
async def get_all_articulos():
    """Devuelve todos los artículos paginando la API de KAME en paralelo."""
    first = await kame_get("/api/Maestro/getListArticulo", {"page": 1, "per_page": 100})
    total    = first.get("total", 0)
    per_page = first.get("per_page", 100)
    total_pages = max(1, (total + per_page - 1) // per_page)

    all_items = list(first.get("items", []))

    # Fetch remaining pages en lotes de 10 para no saturar KAME
    for batch_start in range(2, total_pages + 1, 10):
        batch = range(batch_start, min(batch_start + 10, total_pages + 1))
        pages = await asyncio.gather(
            *[kame_get("/api/Maestro/getListArticulo", {"page": p, "per_page": 100}) for p in batch],
            return_exceptions=True,
        )
        for page in pages:
            if isinstance(page, dict):
                all_items.extend(page.get("items", []))

    return {"items": all_items, "total": len(all_items)}

@router.get("/vendedores")
async def get_list_vendedor():
    return await kame_get("/api/Maestro/getListVendedor")

@router.get("/unidades-negocio")
async def get_list_unidad_negocio():
    return await kame_get("/api/Maestro/getListUnidadNegocio")

@router.get("/fichas")
async def get_list_ficha():
    return await kame_get("/api/Maestro/getListFicha")
