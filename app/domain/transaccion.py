from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class BusinessRuleRN47Exception(Exception):
    """Excepción para montos no coincidentes con AIN-15a o rechazo de pasarela (RN-47)."""
    def __init__(self, message: str = "El monto enviado no coincide con el saldo de la reserva o la transacción fue rechazada"):
        self.message = message
        super().__init__(self.message)


class InvalidPaymentDataException(Exception):
    """Excepción para datos de pago faltantes o inválidos (400)."""
    def __init__(self, message: str = "Datos de pago incompletos o token de tarjeta inválido"):
        self.message = message
        super().__init__(self.message)


class ExternalGatewayUnavailableException(Exception):
    """Excepción para cuando la pasarela AEX-04 no responde (503)."""
    def __init__(self, message: str = "La pasarela de pagos externa no responde en este momento"):
        self.message = message
        super().__init__(self.message)


class TransactionCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    reservation_code: str = Field(..., alias="codigo_reserva", min_length=3, description="Código de la reserva a liquidar")
    amount: float = Field(..., alias="monto", gt=0, description="Monto exacto a cobrar")
    currency: str = Field(..., alias="moneda", min_length=3, max_length=3, description="Código ISO de la moneda (ej. COP)")
    payment_method_code: str = Field(..., alias="codigo_medio_pago", min_length=2, description="Medio de pago seleccionado (ej. TC_VISA)")
    card_token: str = Field(..., alias="token_tarjeta", min_length=5, description="Token seguro de la tarjeta para AEX-04")

    @field_validator("reservation_code", "currency", "payment_method_code", "card_token")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("El campo no puede estar vacío.")
        return value.strip()


class TransactionData(BaseModel):
    id_transaccion: int
    referencia_pasarela: str
    codigo_reserva: str
    monto_cobrado: float
    moneda: str
    estado_transaccion: str
    estado_reserva: str


class TransactionResponse(BaseModel):
    mensaje: str
    data: Optional[TransactionData] = None
    success: bool
