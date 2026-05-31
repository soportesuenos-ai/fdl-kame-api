import json
import sqlite3
import time
import os
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional

router = APIRouter()

DB_PATH = os.getenv("SESIONES_DB_PATH", "/tmp/fdl_sesiones.db")
_db_lock = asyncio.Lock()


def _init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS sesiones (
            sesion_id TEXT NOT NULL,
            bodega    TEXT NOT NULL,
            data      TEXT NOT NULL,
            ts        REAL NOT NULL,
            PRIMARY KEY (bodega, sesion_id)
        )
    """)
    con.commit()
    con.close()

_init_db()


def _db_upsert(bodega, sesion_id, data):
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "INSERT OR REPLACE INTO sesiones (sesion_id, bodega, data, ts) VALUES (?,?,?,?)",
        (sesion_id, bodega, json.dumps(data), time.time())
    )
    con.commit()
    con.close()


def _db_list(bodega):
    con = sqlite3.connect(DB_PATH)
    rows = con.execute(
        "SELECT data FROM sesiones WHERE bodega=? ORDER BY ts",
        (bodega,)
    ).fetchall()
    con.close()
    return [json.loads(r[0]) for r in rows]


def _db_delete(bodega):
    con = sqlite3.connect(DB_PATH)
    con.execute("DELETE FROM sesiones WHERE bodega=?", (bodega,))
    con.commit()
    con.close()


class ItemConteo(BaseModel):
    qty: float
    obs: Optional[str] = None

class SesionSubmit(BaseModel):
    sesion_id: str
    usuario:   str
    bodega:    str
    calle:     Optional[str] = None
    fecha:     str
    items:     Dict[str, ItemConteo]


@router.post("/sesiones")
async def submit_sesion(body: SesionSubmit):
    async with _db_lock:
        data = {**body.model_dump(), "ts_recibida": time.time()}
        _db_upsert(body.bodega, body.sesion_id, data)
    return {
        "ok": True,
        "bodega": body.bodega,
        "sesion_id": body.sesion_id,
        "items_recibidos": len(body.items),
    }


@router.get("/sesiones")
async def list_sesiones(bodega: str):
    sesiones = _db_list(bodega)
    return {"bodega": bodega, "sesiones": sesiones, "total": len(sesiones)}


@router.get("/sesiones/consolidado")
async def consolidar(bodega: str):
    sesiones = _db_list(bodega)
    if not sesiones:
        raise HTTPException(status_code=404, detail=f"No hay sesiones para bodega '{bodega}'")

    consolidado = {}
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
        "bodega":        bodega,
        "sesiones_base": len(sesiones),
        "skus_contados": len(items_out),
        "items":         items_out,
    }


@router.delete("/sesiones")
async def clear_sesiones(bodega: str):
    async with _db_lock:
        _db_delete(bodega)
    return {"ok": True, "bodega": bodega}
