from fastapi import APIRouter, Query
from app.services.auth import kame_get

router = APIRouter()

@router.get("")
async def get_cobros(
    page: int = Query(1), per_page: int = Query(100),
    fechaDesde: str = Query(...), fechaHasta: str = Query(...)
):
    return await kame_get("/api/Cobro/getInformeCobros",
        {"page": page, "per_page": per_page, "fechaDesde": fechaDesde, "fechaHasta": fechaHasta})
