from typing import Optional, List
from pydantic import BaseModel, Field

class ReglaNegocioRN45Exception(Exception):
    """Excepción para cuando no hay medios de pago habilitados para la moneda (RN-45)."""
    def __init__(self, mensaje: str = "No hay medios de pago habilitados temporalmente para esta moneda"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)

class MonedaNoSoportadaException(Exception):
    """Excepción para códigos de moneda inválidos o no soportados (400)."""
    def __init__(self, mensaje: str = "Código de moneda no soportado"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)

class PasarelaNoDisponibleException(Exception):
    """Excepción para cuando la pasarela AEX-04 no responde (503)."""
    def __init__(self, mensaje: str = "La pasarela de pagos no se encuentra disponible"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)

class MedioPagoItem(BaseModel):
    codigo: str = Field(..., description="Código identificador del medio de pago")
    nombre: str = Field(..., description="Nombre comercial del medio de pago")
    tipo: str = Field(..., description="Tipo de medio (ej: TARJETA_CREDITO, DEBITO_BANCARIO)")
    activo: bool = Field(True, description="Indica si el medio está habilitado")

class MediosPagoData(BaseModel):
    moneda: str = Field(..., description="Código de la moneda consultada")
    medios_pago: List[MedioPagoItem] = Field(..., description="Listado de medios de pago activos")

class MediosPagoResponse(BaseModel):
    mensaje: str
    data: Optional[MediosPagoData] = None
    success: bool
