from typing import Optional, List
from pydantic import BaseModel, Field


class BusinessRuleRN45Exception(Exception):
    """Excepción para cuando no hay medios de pago habilitados para la moneda (RN-45)."""
    def __init__(self, message: str = "No hay medios de pago habilitados temporalmente para esta moneda"):
        self.message = message
        super().__init__(self.message)


class UnsupportedCurrencyException(Exception):
    """Excepción para códigos de moneda inválidos o no soportados (400)."""
    def __init__(self, message: str = "Código de moneda no soportado"):
        self.message = message
        super().__init__(self.message)


class PaymentGatewayUnavailableException(Exception):
    """Excepción para cuando la pasarela AEX-04 no responde (503)."""
    def __init__(self, message: str = "La pasarela de pagos no se encuentra disponible"):
        self.message = message
        super().__init__(self.message)


class PaymentMethodItem(BaseModel):
    codigo: str = Field(..., description="Código identificador del medio de pago")
    nombre: str = Field(..., description="Nombre comercial del medio de pago")
    tipo: str = Field(..., description="Tipo de medio (ej: TARJETA_CREDITO, DEBITO_BANCARIO)")
    activo: bool = Field(True, description="Indica si el medio está habilitado")


class PaymentMethodsData(BaseModel):
    moneda: str = Field(..., description="Código de la moneda consultada")
    medios_pago: List[PaymentMethodItem] = Field(..., description="Listado de medios de pago activos")


class PaymentMethodsResponse(BaseModel):
    mensaje: str
    data: Optional[PaymentMethodsData] = None
    success: bool
