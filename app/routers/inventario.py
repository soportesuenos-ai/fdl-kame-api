import asyncio
from fastapi import APIRouter, Path
from pydantic import BaseModel
from typing import List, Optional
from app.services.auth import kame_get, kame_post, kame_put, _safe_path_segment
from app.models.schemas import ArticuloUpdateFull
from app.models.schemas import ArticuloCreate, ArticuloUpdate, MovimientoInventario

router = APIRouter()

@router.get("/stock/articulo/{nombre_articulo}")
async def get_stock_articulo(nombre_articulo: str = Path(..., min_length=1, max_length=100)):
    safe = _safe_path_segment(nombre_articulo)
    return await kame_get(f"/api/Inventario/getStockArticulo/{safe}")

@router.get("/stock/bodega/{nombre_bodega}")
async def get_stock_bodega(nombre_bodega: str = Path(..., min_length=1, max_length=100)):
    safe = _safe_path_segment(nombre_bodega)
    return await kame_get(f"/api/Inventario/getStockBodega/{safe}")

@router.get("/stock/articulo/{nombre_articulo}/bodega/{nombre_bodega}")
async def get_stock_articulo_by_bodega(
    nombre_articulo: str = Path(..., min_length=1, max_length=100),
    nombre_bodega:   str = Path(..., min_length=1, max_length=100),
):
    safe_art = _safe_path_segment(nombre_articulo)
    safe_bod = _safe_path_segment(nombre_bodega)
    return await kame_get(f"/api/Inventario/getStockArticuloByBodega/{safe_art}/{safe_bod}")

@router.post("/movimiento")
async def add_inventario(body: MovimientoInventario):
    data = body.model_dump(exclude_none=True)
    raw_items = data.pop("items", [])
    data["detalle"] = [
        {
            "articulo": it["sku"],
            "cantidad": it["cantidad"],
            **({"precioUn":      it["precioUnitario"]} if "precioUnitario" in it else {}),
            **({"unidadNegocio": it["unidadNegocio"]} if "unidadNegocio"  in it else {}),
            **({"totalLinea":    it["totalLinea"]}    if "totalLinea"     in it else {}),
        }
        for it in raw_items
    ]
    return await kame_post("/api/Inventario/addInventario", data)

@router.post("/articulo")
async def add_articulo(body: ArticuloCreate):
    return await kame_post("/api/Inventario/addArticulo", body.model_dump(exclude_none=True))

@router.put("/articulo/{sku}")
async def update_articulo(
    sku: str = Path(..., min_length=1, max_length=100),
    body: ArticuloUpdateFull = ...,
):
    """
    Actualiza un artículo existente en KAME via PUT /api/Inventario/updArticulo/{sku}.
    Endpoint correcto confirmado por KAME soporte (updArticulo, no updateArticulo).
    """
    safe = _safe_path_segment(sku)
    data = body.model_dump(exclude_none=True)
    # No incluir sku en el body — KAME lo toma del path; si viene en body
    # lo interpreta como intento de crear y devuelve "ya se encuentra registrado"
    data.pop("sku", None)
    return await kame_put(f"/api/Inventario/updArticulo/{safe}", data)


# ─── BULK UPDATE ─────────────────────────────────────────────────────────────

class BulkUpdateItem(BaseModel):
    sku: str
    usuario: str
    unidadMedida: Optional[str] = None
    unidadEquivalente: Optional[str] = None
    factorUnidadEquivalente: Optional[float] = None
    precioVentaNeto: Optional[float] = None
    descripcion: Optional[str] = None
    familia: Optional[str] = None

class BulkUpdateRequest(BaseModel):
    items: List[BulkUpdateItem]
    delay_ms: int = 400   # Pausa entre requests para no saturar rate limit KAME

@router.put("/articulos/bulk")
async def bulk_update_articulos(body: BulkUpdateRequest):
    """
    Actualiza múltiples artículos en KAME de forma secuencial.
    Útil para corrección masiva de factorUnidadEquivalente u otros campos.
    Procesa de a uno con delay configurable (default 400ms) para respetar
    el rate limit de KAME (180 req/min).
    """
    resultados = []
    errores    = []

    for item in body.items:
        try:
            safe_sku = _safe_path_segment(item.sku)
            payload  = {k: v for k, v in item.model_dump().items()
                        if k != "sku" and v is not None}
            resp = await kame_put(f"/api/Maestro/updateArticulo/{safe_sku}", payload)
            resultados.append({"sku": item.sku, "ok": True, "resp": resp})
        except Exception as e:
            errores.append({"sku": item.sku, "ok": False, "error": str(e)})

        if body.delay_ms > 0:
            await asyncio.sleep(body.delay_ms / 1000)

    return {
        "total":      len(body.items),
        "ok":         len(resultados),
        "errores":    len(errores),
        "detalle_ok": resultados,
        "detalle_err": errores,
    }
