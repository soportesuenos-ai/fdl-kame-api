"""
Router de sesiones de inventario físico.

Almacena sesiones de conteo en memoria del servidor (suficiente para una
jornada de toma de inventario). Las sesiones se consolidan por bodega:
- Mismo SKU en distintas calles → se SUMAN (stock distribuido en la bodega)
- El admin revisa diferencias vs. stock KAME antes de generar movimientos
"""
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional

router = APIRouter()

# ─── STORAGE EN MEMORIA ───────────────────────────────────────────────────────
# Estructura: { bodega: { session_id: SesionData } }
_sesiones: Dict[str, Dict[str, dict]] = {}


# ─── SCHEMAS ──────────────────────────────────────────────────────────────────
class ItemConteo(BaseModel):
    qty: float
    obs: Optional[str] = None

class SesionSubmit(BaseModel):
    sesion_id: str          # ej: "usr_bodega1_2026-05-27"
    usuario:   str
    bodega:    str
    calle:     Optional[str] = None   # sección asignada al usuario
    fecha:     str
    items:     Dict[str, ItemConteo]  # { sku: { qty, obs } }


# ─── ENDPOINTS ────────────────────────────────────────────────────────────────

@router.post("/sesiones")
async def submit_sesion(body: SesionSubmit):
    """Recibe la sesión de conteo de un usuario y la almacena en servidor."""
    bodega = body.bodega
    if bodega not in _sesiones:
        _sesiones[bodega] = {}
    _sesiones[bodega][body.sesion_id] = {
        **body.model_dump(),
        "ts_recibida": time.time(),
    }
    return {
        "ok": True,
        "bodega": bodega,
        "sesion_id": body.sesion_id,
        "items_recibidos": len(body.items),
    }


@router.get("/sesiones")
async def list_sesiones(bodega: str):
    """Lista todas las sesiones enviadas para una bodega."""
    sesiones = list((_sesiones.get(bodega) or {}).values())
    return {"bodega": bodega, "sesiones": sesiones, "total": len(sesiones)}


@router.get("/sesiones/consolidado")
async def consolidar(bodega: str):
    """Consolida todas las sesiones de una bodega:
    - Suma cantidades del mismo SKU en distintas calles
    - Devuelve tabla lista para comparar con stock KAME
    """
    sesiones = (_sesiones.get(bodega) or {}).values()
    if not sesiones:
        raise HTTPException(status_code=404, detail=f"No hay sesiones para bodega '{bodega}'")

    # Sumar qty por SKU a través de todas las calles/usuarios
    consolidado: Dict[str, dict] = {}
    for ses in sesiones:
        for sku, item in (ses.get("items") or {}).items():
            qty = item.get("qty", 0) if isinstance(item, dict) else 0
            obs = item.get("obs", "") if isinstance(item, dict) else ""
            if sku not in consolidado:
                consolidado[sku] = {"qty_contada": 0, "obs": [], "calles": []}
            consolidado[sku]["qty_contada"] += qty
            if obs:
                consolidado[sku]["obs"].append(obs)
            calle = ses.get("calle") or ses.get("usuario", "")
            if calle and calle not in consolidado[sku]["calles"]:
                consolidado[sku]["calles"].append(calle)

    items_out = [
        {
            "sku":         sku,
            "qty_contada": round(v["qty_contada"], 4),
            "calles":      v["calles"],
            "obs":         "; ".join(v["obs"]) if v["obs"] else None,
        }
        for sku, v in consolidado.items()
    ]

    return {
        "bodega":          bodega,
        "sesiones_base":   len(list(sesiones)),
        "skus_contados":   len(items_out),
        "items":           items_out,
    }


@router.delete("/sesiones")
async def clear_sesiones(bodega: str):
    """Limpia las sesiones de una bodega (después de procesar en KAME)."""
    if bodega in _sesiones:
        del _sesiones[bodega]
    return {"ok": True, "bodega": bodega}
