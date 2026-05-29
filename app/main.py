import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers import inventario, maestro, cobros, pagos, sesiones, usuarios
from app.services.auth import lifespan

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("fdl-kame-api")

app = FastAPI(title="FDL KAME API", version="1.0.0", lifespan=lifespan)

# ─── CORS ──────────────────────────────────────────────────────────────────────
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
if not ALLOWED_ORIGINS:
    ALLOWED_ORIGINS = ["*"]
    logger.warning("ALLOWED_ORIGINS no configurado — CORS abierto a todos los origenes")

# allow_credentials=True es incompatible con allow_origins=["*"] en Starlette:
# cuando se usan juntos no se emite ningun header CORS. Se usa credentials solo
# con origenes explicitos.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=ALLOWED_ORIGINS != ["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# ─── API KEY AUTH ──────────────────────────────────────────────────────────────
API_KEY = os.getenv("FDL_API_KEY", "")
SKIP_AUTH_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc"}

if not API_KEY:
    logger.warning("FDL_API_KEY no configurada — todos los requests son aceptados")

@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    if not API_KEY:
        return await call_next(request)
    if request.url.path in SKIP_AUTH_PATHS:
        return await call_next(request)
    if request.method == "OPTIONS":
        return await call_next(request)
    key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    if key != API_KEY:
        return JSONResponse(
            status_code=401,
            content={"detail": "API key invalida o ausente"},
            headers={"Access-Control-Allow-Origin": request.headers.get("origin", "*")},
        )
    return await call_next(request)

# ─── ROUTERS ───────────────────────────────────────────────────────────────────
app.include_router(inventario.router, prefix="/inventario", tags=["Inventario"])
app.include_router(maestro.router,    prefix="/maestro",    tags=["Maestro"])
app.include_router(cobros.router,     prefix="/cobros",     tags=["Cobros"])
app.include_router(pagos.router,      prefix="/pagos",      tags=["Pagos"])
app.include_router(sesiones.router,   prefix="/inventario", tags=["Sesiones"])
app.include_router(usuarios.router,   prefix="",            tags=["Usuarios"])

@app.get("/")
async def root():
    return {"status": "ok", "app": "FDL KAME API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
