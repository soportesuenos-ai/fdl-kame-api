from datetime import date
from fastapi import APIRouter, Query
from app.services.auth import kame_get

router = APIRouter()

@router.get("")
async def get_cobros(
    fechaDesde: date = Query(..., description="Fecha inicio YYYY-MM-DD"),
    fechaHasta: date = Query(..., description="Fecha fin YYYY-MM-DD"),
    page:       int  = Query(1,   ge=1),
    per_page:   int  = Query(100, ge=1, le=500),
):
    return await kame_get("/api/Cobros/getCobros", params={
        "fechaDesde": fechaDesde.isoformat(),
        "fechaHasta": fechaHasta.isoformat(),
        "page":       page,
        "per_page":   per_page,
    })
