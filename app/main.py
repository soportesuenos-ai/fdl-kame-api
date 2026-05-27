import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers import inventario, maestro, cobros, pagos
from app.services.auth import lifespan

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("fdl-kame-api")

app = FastAPI(title="FDL KAME API", version="1.0.0", lifespan=lifespan)

# â”€â”€â”€ CORS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
if not ALLOWED_ORIGINS:
    ALLOWED_ORIGINS = ["*"]

# allow_credentials=True es incompatible con allow_origins=["*"] en Starlette:
# cuando se usan juntos no se emite ningÃºn header CORS. Se usa credentials solo
# con orÃ­genes explÃ­citos.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=ALLOWED_ORIGINS != ["*"],
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["*"],
)

# â”€â”€â”€ API KEY AUTH â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
        return JSONResponse(status_code=401, content={"detail": "API key invÃ¡lida o ausente"})
    return await call_next(request)

# â”€â”€â”€ RUTAS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
