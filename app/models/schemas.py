from pydantic import BaseModel, Field
from typing import Optional, List

class Atributo(BaseModel):
    key: str
    value: str

class ArticuloCreate(BaseModel):
    usuario: str
    descripcion: str
    sku: str
    unidadMedida: str
    precioVentaNeto: float
    stockMin: Optional[float] = None
    stockMax: Optional[float] = None
    familia: Optional[str] = None
    descripcionDetallada: Optional[str] = None
    skuInterno: Optional[str] = None
    esArticuloProduccion: Optional[bool] = None
    actualizaStockShopify: Optional[bool] = None
    actualizaStockMeli: Optional[bool] = None
    actualizaStockWoo: Optional[bool] = None
    actualizaStockEnLinea: Optional[bool] = None
    unidadEquivalente: Optional[str] = None
    factorUnidadEquivalente: Optional[float] = None
    cuentaEmpresaCostosVenta: Optional[str] = None
    atributos: Optional[List[Atributo]] = None

class ArticuloUpdate(BaseModel):
    usuario: str
    descripcion: Optional[str] = None
    unidadMedida: Optional[str] = None
    precioVentaNeto: Optional[float] = None
    stockMin: Optional[float] = None
    stockMax: Optional[float] = None
    familia: Optional[str] = None
    descripcionDetallada: Optional[str] = None
    atributos: Optional[List[Atributo]] = None

class MovimientoItem(BaseModel):
    sku: str
    cantidad: float
    precioUnitario: Optional[float] = None

class MovimientoInventario(BaseModel):
    usuario: str
    tipoDocumento: str
    folio: Optional[str] = None
    fecha: str
    motivoMovimiento: str
    rutFicha: Optional[str] = None
    bodegaEntrada: Optional[str] = None
    bodegaSalida: Optional[str] = None
    comentario: Optional[str] = None
    IdOrdenCompra: Optional[str] = None
    items: List[MovimientoItem]
