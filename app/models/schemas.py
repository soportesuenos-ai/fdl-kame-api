from pydantic import BaseModel, Field
from typing import Optional, List

class Atributo(BaseModel):
    key: str
    value: str

class ArticuloCreate(BaseModel):
    # Campos confirmados con doc oficial KAME /api/Inventario/addArticulo
    usuario: str                                                   # Obligatorio
    descripcion: str                                               # Obligatorio
    sku: str                                                       # Obligatorio
    unidadMedida: str                                              # Obligatorio
    precioVentaNeto: float                                         # Obligatorio
    stockMin: Optional[float] = 0
    stockMax: Optional[float] = 0
    familia: Optional[str] = None
    descripcionDetallada: Optional[str] = None
    skuInterno: Optional[str] = None
    unidadEquivalente: Optional[str] = None
    factorUnidadEquivalente: Optional[float] = None
    cuentaEmpresaCostosVenta: Optional[str] = None                 # ej: "4.01.02.01"
    imprimeDetallesEnVentas: Optional[bool] = None                 # bool
    imprimeDetallesEnCotizaciones: Optional[bool] = None           # bool
    imprimeDetallesEnPedidos: Optional[bool] = None                # bool
    esArticuloProduccion: Optional[bool] = None                    # bool
    actualizaStockShopify: Optional[bool] = None
    actualizaStockMeli: Optional[bool] = None
    actualizaStockWoo: Optional[bool] = None
    actualizaStockEnLinea: Optional[bool] = None
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
    unidadEquivalente: Optional[str] = None
    factorUnidadEquivalente: Optional[float] = None
    cuentaEmpresaCostosVenta: Optional[str] = None
    imprimeDetallesEnVentas: Optional[bool] = None
    imprimeDetallesEnCotizaciones: Optional[bool] = None
    imprimeDetallesEnPedidos: Optional[bool] = None
    esArticuloProduccion: Optional[bool] = None
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
