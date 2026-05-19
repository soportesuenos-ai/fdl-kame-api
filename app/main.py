import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.routers import inventario, maestro, cobros, pagos
from app.services.auth import lifespan

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("fdl-kame-api")

app = FastAPI(title="FDL KAME API", version="1.0.0", lifespan=lifespan)

# ─── CORS ─────────────────────────────────────────────────────────────────────
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
if not ALLOWED_ORIGINS:
    ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["*"],
)

# ─── API KEY AUTH ──────────────────────────────────────────────────────────────
API_KEY = os.getenv("FDL_API_KEY", "")
SKIP_AUTH_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc"}

@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    if not API_KEY:
        return await call_next(request)
    if request.url.path in SKIP_AUTH_PATHS:
        return await call_next(request)
    if request.method == "OPTIONS":  # dejar pasar preflight CORS
        return await call_next(request)
    key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida o ausente")
    return await call_next(request)

# ─── RUTAS ────────────────────────────────────────────────────────────────────
app.include_router(inventario.router, prefix="/inventario", tags=["Inventario"])
app.include_router(maestro.router,    prefix="/maestro",    tags=["Maestro"])
app.include_router(cobros.router,     prefix="/cobros",     tags=["Cobros"])
app.include_router(pagos.router,      prefix="/pagos",      tags=["Pagos"])

@app.get("/")
async def root():
    return {"status": "ok", "app": "FDL KAME API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
