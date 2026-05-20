from pydantic import BaseModel, Field
from typing import Optional, List

class Atributo(BaseModel):
    key: str
    value: str

class ArticuloCreate(BaseModel):
    # Campos confirmados con la respuesta real de KAME (getListArticulo)
    usuario: str
    descripcion: str                                     # → Descripcion
    sku: str                                             # → SKU
    unidadMedida: str                                    # → UnidadMedida
    precioVentaNeto: float                               # → PrecioVentaNeto
    stockMin: Optional[float] = 0                        # → StockMin
    stockMax: Optional[float] = 0                        # → StockMax
    familia: Optional[str] = None                        # → Familia
    unidadEquivalente: Optional[str] = None              # → UnidadEquivalente (ej: "PULG")
    factorUnidadEquivalente: Optional[float] = None      # → FactorUnidadEquivalente (pulgadas)
    cuentaCostoVenta: Optional[str] = None               # → CuentaCostoVenta
    imprimeDetallesEnVentas: Optional[str] = None        # → ImprimeDetallesEnVentas ("S"/"N")
    imprimeDetallesEnCotizaciones: Optional[str] = None  # → ImprimeDetallesEnCotizaciones
    imprimeDetallesEnPedidos: Optional[str] = None       # → ImprimeDetallesEnPedidos
    esArticuloProduccion: Optional[str] = None           # → EsArticuloProduccion ("S"/"N")

class ArticuloUpdate(BaseModel):
    usuario: str
    descripcion: Optional[str] = None
    unidadMedida: Optional[str] = None
    precioVentaNeto: Optional[float] = None
    stockMin: Optional[float] = None
    stockMax: Optional[float] = None
    familia: Optional[str] = None
    unidadEquivalente: Optional[str] = None
    factorUnidadEquivalente: Optional[float] = None
    cuentaCostoVenta: Optional[str] = None
    imprimeDetallesEnVentas: Optional[str] = None
    imprimeDetallesEnCotizaciones: Optional[str] = None
    imprimeDetallesEnPedidos: Optional[str] = None
    esArticuloProduccion: Optional[str] = None

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
