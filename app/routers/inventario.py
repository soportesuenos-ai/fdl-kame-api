from fastapi import APIRouter, Path, Query
from app.services.auth import kame_get, kame_post, kame_put
from app.models.schemas import ArticuloCreate, ArticuloUpdate, MovimientoInventario

router = APIRouter()

@router.get("/stock/articulo/{nombre_articulo}")
async def get_stock_articulo(nombre_articulo: str = Path(...)):
    return await kame_get(f"/api/Inventario/getStockArticulo/{nombre_articulo}")

@router.get("/stock/bodega/{nombre_bodega}")
async def get_stock_bodega(nombre_bodega: str = Path(...)):
    return await kame_get(f"/api/Inventario/getStockBodega/{nombre_bodega}")

@router.get("/stock/articulo/{nombre_articulo}/bodega/{nombre_bodega}")
async def get_stock_articulo_by_bodega(nombre_articulo: str = Path(...), nombre_bodega: str = Path(...)):
    return await kame_get(f"/api/Inventario/getStockArticuloByBodega/{nombre_articulo}/{nombre_bodega}")

@router.post("/movimiento")
async def add_inventario(body: MovimientoInventario):
    return await kame_post("/api/Inventario/addInventario", body.model_dump(exclude_none=True))

@router.post("/articulo")
async def add_articulo(body: ArticuloCreate):
    return await kame_post("/api/Inventario/addArticulo", body.model_dump(exclude_none=True))

@router.put("/articulo/{sku}")
async def upd_articulo(sku: str = Path(...), body: ArticuloUpdate = ...):
    return await kame_put(f"/api/Inventario/updArticulo/{sku}", body.model_dump(exclude_none=True))
