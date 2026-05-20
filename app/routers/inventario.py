from fastapi import APIRouter, Path
from app.services.auth import kame_get, kame_post, kame_put, _safe_path_segment
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
    # Mapear "items" → "detalle" y "sku" → "articulo" según esquema KAME
    raw_items = data.pop("items", [])
    data["detalle"] = [
        {
            "articulo":     it["sku"],
            "cantidad":     it["cantidad"],
            **({"precioUn": it["precioUnitario"]} if "precioUnitario" in it else {}),
        }
        for it in raw_items
    ]
    return await kame_post("/api/Inventario/addInventario", data)

@router.post("/articulo")
async def add_articulo(body: ArticuloCreate):
    raw = body.model_dump(exclude_none=True)
    # Mapear camelCase nuestro → PascalCase que usa KAME en addArticulo
    mapping = {
        "descripcion":               "Descripcion",
        "sku":                       "SKU",
        "unidadMedida":              "UnidadMedida",
        "precioVentaNeto":           "PrecioVentaNeto",
        "stockMin":                  "StockMin",
        "stockMax":                  "StockMax",
        "familia":                   "Familia",
        "unidadEquivalente":         "UnidadEquivalente",
        "factorUnidadEquivalente":   "FactorUnidadEquivalente",
        "cuentaCostoVenta":          "CuentaCostoVenta",
        "imprimeDetallesEnVentas":       "ImprimeDetallesEnVentas",
        "imprimeDetallesEnCotizaciones": "ImprimeDetallesEnCotizaciones",
        "imprimeDetallesEnPedidos":      "ImprimeDetallesEnPedidos",
        "esArticuloProduccion":      "EsArticuloProduccion",
    }
    data = {mapping.get(k, k): v for k, v in raw.items()}
    return await kame_post("/api/Maestro/addArticulo", data)

@router.put("/articulo/{sku}")
async def update_articulo(
    sku: str = Path(..., min_length=1, max_length=100),
    body: ArticuloUpdate = ...,
):
    raw = body.model_dump(exclude_none=True)
    mapping = {
        "descripcion":               "Descripcion",
        "unidadMedida":              "UnidadMedida",
        "precioVentaNeto":           "PrecioVentaNeto",
        "stockMin":                  "StockMin",
        "stockMax":                  "StockMax",
        "familia":                   "Familia",
        "unidadEquivalente":         "UnidadEquivalente",
        "factorUnidadEquivalente":   "FactorUnidadEquivalente",
        "cuentaCostoVenta":          "CuentaCostoVenta",
        "imprimeDetallesEnVentas":       "ImprimeDetallesEnVentas",
        "imprimeDetallesEnCotizaciones": "ImprimeDetallesEnCotizaciones",
        "imprimeDetallesEnPedidos":      "ImprimeDetallesEnPedidos",
        "esArticuloProduccion":      "EsArticuloProduccion",
    }
    data = {mapping.get(k, k): v for k, v in raw.items()}
    safe_sku = _safe_path_segment(sku)
    return await kame_put(f"/api/Maestro/updateArticulo/{safe_sku}", data)
