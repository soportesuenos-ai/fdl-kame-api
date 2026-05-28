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
    cuentaEmpresaCostosVenta: Optional[str] = None
    imprimeDetallesEnVentas: Optional[bool] = None
    imprimeDetallesEnCotizaciones: Optional[bool] = None
    imprimeDetallesEnPedidos: Optional[bool] = None
    esArticuloProduccion: Optional[bool] = None
    actualizaStockShopify: Optional[bool] = None
    actualizaStockMeli: Optional[bool] = None
    actualizaStockWoo: Optional[bool] = None
    actualizaStockEnLinea: Optional[bool] = None
    atributos: Optional[List[Atributo]] = None


class ArticuloUpdateFull(BaseModel):
    """Schema completo para PUT /api/Inventario/updArticulo/{sku}.
    Campos confirmados por KAME soporte (mayo 2026)."""
    usuario: str                                    # Obligatorio
    descripcion: Optional[str] = None
    unidadMedida: Optional[str] = None
    precioVentaNeto: Optional[float] = None
    stockMin: Optional[float] = None
    stockMax: Optional[float] = None
    familia: Optional[str] = None
    skuInterno: Optional[str] = None
    descripcionDetallada: Optional[str] = None
    unidadEquivalente: Optional[str] = None
    factorUnidadEquivalente: Optional[float] = None
    cuentaEmpresaCostosVenta: Optional[str] = None
    impuestoEspecifico: Optional[str] = None
    productoCambioSujeto: Optional[str] = None
    archivoBinImagen: Optional[str] = None
    # Rentabilidad y descuento
    usaMinimoRentabilidad: Optional[bool] = None
    minimoRentabilidad: Optional[float] = None
    usaMaximoDescuento: Optional[bool] = None
    maximoDescuentoPorc: Optional[float] = None
    # Seguimiento
    usaSeguimientoSeries: Optional[bool] = None
    usaSeguimientoLotes: Optional[bool] = None
    esArticuloProduccion: Optional[bool] = None
    # Impresión
    imprimeEnCot: Optional[str] = None             # "Ambos", "Solo Descripción", etc.
    imprimeEnOC: Optional[str] = None
    imprimeDetallesEnVentas: Optional[bool] = None
    imprimeDetallesEnCotizaciones: Optional[bool] = None
    imprimeDetallesEnPedidos: Optional[bool] = None
    # Ecommerce
    actualizaStockMeli: Optional[bool] = None
    actualizaStockWoo: Optional[bool] = None
    actualizaStockShopify: Optional[bool] = None
    actualizaStockEnLinea: Optional[bool] = None
    # Atributos custom
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
    unidadNegocio: Optional[str] = None
    totalLinea: Optional[float] = None


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
