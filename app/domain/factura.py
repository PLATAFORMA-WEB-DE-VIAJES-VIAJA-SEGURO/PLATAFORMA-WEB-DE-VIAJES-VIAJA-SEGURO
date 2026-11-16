from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ReglaNegocioRN48Exception(Exception):
    """Excepción cuando la transacción no está aprobada o ya tiene factura emitida (RN-48)."""
    def __init__(self, mensaje: str = "La transacción no está aprobada o ya cuenta con una factura emitida"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class DatosFiscalesInvalidosException(Exception):
    """Excepción para datos fiscales del adquirente incompletos o inválidos (400)."""
    def __init__(self, mensaje: str = "Datos fiscales del adquirente incompletos"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class FacturacionNoDisponibleException(Exception):
    """Excepción para cuando el proveedor AEX-05 no está disponible (503)."""
    def __init__(self, mensaje: str = "El proveedor de facturación electrónica no está disponible"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class FacturaCreate(BaseModel):
    id_transaccion: int = Field(..., gt=0, description="ID de la transacción aprobada a facturar")
    tipo_documento_fiscal: str = Field(..., min_length=2, max_length=5, description="Tipo de documento fiscal (ej: CC, NIT, CE)")
    numero_documento_fiscal: str = Field(..., min_length=5, description="Número del documento fiscal del adquirente")
    razon_social: str = Field(..., min_length=2, description="Nombre o razón social del adquirente")
    correo_facturacion: str = Field(..., min_length=5, description="Correo electrónico para envío de la factura")

    @field_validator("tipo_documento_fiscal", "numero_documento_fiscal", "razon_social", "correo_facturacion")
    @classmethod
    def validar_no_vacio(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("El campo no puede estar vacío.")
        return v.strip()


class FacturaData(BaseModel):
    id_factura: int = Field(..., description="ID interno de la factura emitida")
    numero_factura: str = Field(..., description="Número de factura electrónica (ej: FE-VS-00125)")
    id_transaccion: int = Field(..., description="ID de la transacción facturada")
    cufe: str = Field(..., description="Código Único de Factura Electrónica asignado por AEX-05")
    total_facturado: float = Field(..., description="Monto total facturado")
    estado_dian: str = Field(..., description="Estado de validación ante la DIAN (ej: VALIDADA)")


class FacturaResponse(BaseModel):
    mensaje: str
    data: Optional[FacturaData] = None
    success: bool
