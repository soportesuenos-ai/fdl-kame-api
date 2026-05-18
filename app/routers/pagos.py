from fastapi import APIRouter, Query
from app.services.auth import kame_get

router = APIRouter()

@router.get("")
async def get_pagos(
    page: int = Query(1), per_page: int = Query(100),
    fechaDesde: str = Query(...), fechaHasta: str = Query(...)
):
    return await kame_get("/api/Pago/getInformePagos",
        {"page": page, "per_page": per_page, "fechaDesde": fechaDesde, "fechaHasta": fechaHasta})
