"""
Gestión de usuarios PWA — almacenamiento en memoria.
Los datos persisten mientras el servidor esté activo.
Si Render Free reinicia, el admin re-sincroniza desde la PWA.
"""
from fastapi import APIRouter
from typing import List, Any
from pydantic import BaseModel

router = APIRouter()

# Almacenamiento en memoria
_usuarios: List[dict] = []


class UsuariosPayload(BaseModel):
    items: List[Any]


@router.get("/usuarios")
async def get_usuarios():
    """Devuelve la lista de usuarios sincronizados."""
    return {"items": _usuarios, "total": len(_usuarios)}


@router.post("/usuarios")
async def set_usuarios(body: UsuariosPayload):
    """Reemplaza la lista completa de usuarios."""
    global _usuarios
    # Filtrar campos sensibles mínimos requeridos
    _usuarios = [
        {
            "user":     u.get("user", ""),
            "nombre":   u.get("nombre", ""),
            "pin":      str(u.get("pin", "")),
            "rol":      u.get("rol", "bodega"),
            "kameUser": u.get("kameUser", ""),
        }
        for u in body.items
        if u.get("user") and u.get("pin")
    ]
    return {"ok": True, "total": len(_usuarios)}
