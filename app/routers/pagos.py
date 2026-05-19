from datetime import date
from fastapi import APIRouter, Query
from app.services.auth import kame_get

router = APIRouter()

@router.get("")
async def get_pagos(
    fechaDesde: date = Query(..., description="Fecha inicio YYYY-MM-DD"),
    fechaHasta: date = Query(..., description="Fecha fin YYYY-MM-DD"),
    page:       int  = Query(1,   ge=1),
    per_page:   int  = Query(100, ge=1, le=500),
):
    retur