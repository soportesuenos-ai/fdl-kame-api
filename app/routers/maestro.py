from fastapi import APIRouter
from app.services.auth import kame_get

router = APIRouter()

@router.get("/articulos")
async def get_list_articulo():
    return await kame_get("/api/Maestro/getListArticulo")

@router.get("/vendedores")
async def get_list_vendedor():
    return await kame_get("/api/Maestro/getListVendedor")

@router.get("/unidades-negocio")
async def get_list_unidad_negocio():
    return await kame_get("/api/Maestro/getListUnidadNegocio")

@router.get("/fichas")
async def get_list_ficha():
    return await kame_get("/api/Maestro/getListFicha")
