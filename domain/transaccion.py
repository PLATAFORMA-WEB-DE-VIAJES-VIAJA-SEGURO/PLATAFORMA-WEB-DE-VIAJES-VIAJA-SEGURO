from typing import Optional
from pydantic import BaseModel, Field, field_validator

class ReglaNegocioRN47Exception(Exception):
    """Excepción para montos no coincidentes con AIN-15a o rechazo de pasarela (RN-47)."""
    def __init__(self, mensaje: str = "El monto enviado no coincide con el saldo de la reserva o la transacción fue rechazada"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)

class DatosPagoInvalidosException(Exception):
    """Excepción para datos de pago faltantes o inválidos (400)."""
    def __init__(self, mensaje: str = "Datos de pago incompletos o token de tarjeta inválido"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)

class PasarelaNoDisponibleException(Exception):
    """Excepción para cuando la pasarela AEX-04 no responde (503)."""
    def __init__(self, mensaje: str = "La pasarela de pagos externa no responde en este momento"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)

class TransaccionCreate(BaseModel):
    codigo_reserva: str = Field(..., min_length=3, description="Código de la reserva a liquidar")
    monto: float = Field(..., gt=0, description="Monto exacto a cobrar")
    moneda: str = Field(..., min_length=3, max_length=3, description="Código ISO de la moneda (ej. COP)")
    codigo_medio_pago: str = Field(..., min_length=2, description="Medio de pago seleccionado (ej. TC_VISA)")
    token_tarjeta: str = Field(..., min_length=5, description="Token seguro de la tarjeta para AEX-04")

    @field_validator("codigo_reserva", "moneda", "codigo_medio_pago", "token_tarjeta")
    @classmethod
    def validar_no_vacio(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("El campo no puede estar vacío.")
        return v.strip()

class TransaccionData(BaseModel):
    id_transaccion: int
    referencia_pasarela: str
    codigo_reserva: str
    monto_cobrado: float
    moneda: str
    estado_transaccion: str
    estado_reserva: str

class TransaccionResponse(BaseModel):
    mensaje: str
    data: Optional[TransaccionData] = None
    success: bool
