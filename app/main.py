from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import inventario, maestro, cobros, pagos
from app.services.auth import lifespan

app = FastAPI(title="FDL KAME API", version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(inventario.router, prefix="/inventario", tags=["Inventario"])
app.include_router(maestro.router,    prefix="/maestro",    tags=["Maestro"])
app.include_router(cobros.router,     prefix="/cobros",     tags=["Cobros"])
app.include_router(pagos.router,      prefix="/pagos",      tags=["Pagos"])

@app.get("/")
def root():
    return {"status": "ok", "service": "FDL KAME API", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}
