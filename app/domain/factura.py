from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class BusinessRuleRN48Exception(Exception):
    """Excepción cuando la transacción no está aprobada o ya tiene factura emitida (RN-48)."""
    def __init__(self, message: str = "La transacción no está aprobada o ya cuenta con una factura emitida"):
        self.message = message
        super().__init__(self.message)


class InvalidTaxDataException(Exception):
    """Excepción para datos fiscales del adquirente incompletos o inválidos (400)."""
    def __init__(self, message: str = "Datos fiscales del adquirente incompletos"):
        self.message = message
        super().__init__(self.message)


class BillingProviderUnavailableException(Exception):
    """Excepción para cuando el proveedor AEX-05 no está disponible (503)."""
    def __init__(self, message: str = "El proveedor de facturación electrónica no está disponible"):
        self.message = message
        super().__init__(self.message)


class InvoiceCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    transaction_id: int = Field(..., alias="id_transaccion", gt=0, description="ID de la transacción aprobada a facturar")
    tax_document_type: str = Field(..., alias="tipo_documento_fiscal", min_length=2, max_length=5, description="Tipo de documento fiscal (ej: CC, NIT, CE)")
    tax_document_number: str = Field(..., alias="numero_documento_fiscal", min_length=5, description="Número del documento fiscal del adquirente")
    company_name: str = Field(..., alias="razon_social", min_length=2, description="Nombre o razón social del adquirente")
    billing_email: str = Field(..., alias="correo_facturacion", min_length=5, description="Correo electrónico para envío de la factura")

    @field_validator("tax_document_type", "tax_document_number", "company_name", "billing_email")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("El campo no puede estar vacío.")
        return value.strip()


class InvoiceData(BaseModel):
    id_factura: int = Field(..., description="ID interno de la factura emitida")
    numero_factura: str = Field(..., description="Número de factura electrónica (ej: FE-VS-00125)")
    id_transaccion: int = Field(..., description="ID de la transacción facturada")
    cufe: str = Field(..., description="Código Único de Factura Electrónica asignado por AEX-05")
    total_facturado: float = Field(..., description="Monto total facturado")
    estado_dian: str = Field(..., description="Estado de validación ante la DIAN (ej: VALIDADA)")


class InvoiceResponse(BaseModel):
    mensaje: str
    data: Optional[InvoiceData] = None
    success: bool
