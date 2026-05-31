"""
Gestión de usuarios PWA — persistencia en SQLite.
Sobrevive reinicios de proceso; se pierde en redeploy de Render.
"""
import json
import sqlite3
import asyncio
import os
from fastapi import APIRouter
from typing import List, Any
from pydantic import BaseModel

router = APIRouter()

DB_PATH  = os.getenv("SESIONES_DB_PATH", "/tmp/fdl_sesiones.db")
_db_lock = asyncio.Lock()


def _init_usuarios_table():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            user   TEXT PRIMARY KEY,
            data   TEXT NOT NULL
        )
    """)
    con.commit()
    con.close()

_init_usuarios_table()


def _db_get_all() -> List[dict]:
    con = sqlite3.connect(DB_PATH)
    rows = con.execute("SELECT data FROM usuarios ORDER BY user").fetchall()
    con.close()
    return [json.loads(r[0]) for r in rows]


def _db_replace_all(items: List[dict]):
    con = sqlite3.connect(DB_PATH)
    con.execute("DELETE FROM usuarios")
    for u in items:
        con.execute(
            "INSERT INTO usuarios (user, data) VALUES (?, ?)",
            (u["user"], json.dumps(u))
        )
    con.commit()
    con.close()


class UsuariosPayload(BaseModel):
    items: List[Any]


@router.get("/usuarios")
async def get_usuarios():
    usuarios = _db_get_all()
    return {"items": usuarios, "total": len(usuarios)}


@router.post("/usuarios")
async def set_usuarios(body: UsuariosPayload):
    items = [
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
    async with _db_lock:
        _db_replace_all(items)
    return {"ok": True, "total": len(items)}
