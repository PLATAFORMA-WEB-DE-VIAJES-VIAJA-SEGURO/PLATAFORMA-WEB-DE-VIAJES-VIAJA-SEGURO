from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ReglaNegocioRN38Exception(Exception):
    """Excepción cuando el carrito ya fue cerrado, el bloqueo caducó o la identidad no es válida (RN-38)."""
    def __init__(self, mensaje: str = "El carrito ya fue cerrado previamente o algún bloqueo de servicio caducó"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class DatosCierreCompraInvalidosException(Exception):
    """Excepción para datos de facturación o medio de pago incompletos o inválidos (400)."""
    def __init__(self, mensaje: str = "Datos de facturación o medio de pago incompletos"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class ServiciosCierreNoDisponiblesException(Exception):
    """Excepción cuando las dependencias AIN-08, AIN-09, AIN-10 o AIN-14 no responden (503)."""
    def __init__(self, mensaje: str = "No fue posible procesar el cierre de compra por indisponibilidad de servicios"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class CierreCarritoCreate(BaseModel):
    id_usuario: int = Field(..., gt=0, description="Identificador del viajero titular de la compra")
    id_carrito: int = Field(..., gt=0, description="Identificador del carrito de compras a cerrar")
    medio_pago: str = Field(..., min_length=2, description="Medio de pago seleccionado (ej: TARJETA_CREDITO, PSE)")
    direccion_facturacion: str = Field(..., min_length=5, description="Dirección física de facturación del viajero")

    @field_validator("medio_pago", "direccion_facturacion")
    @classmethod
    def validar_no_vacio(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("El campo no puede estar vacío.")
        return v.strip()


class CierreCarritoData(BaseModel):
    id_carrito: int = Field(..., description="Identificador del carrito cerrado")
    estado_carrito: str = Field(..., description="Nuevo estado del carrito (CERRADO)")
    codigo_reserva_preliminar: str = Field(..., description="Código de reserva preliminar generado (ej: VS-2026-8841)")
    total_liquidado: float = Field(..., description="Monto total congelado para el cobro")
    moneda: str = Field(..., description="Moneda de liquidación (ej: COP)")


class CierreCarritoResponse(BaseModel):
    mensaje: str
    data: Optional[CierreCarritoData] = None
    success: bool
