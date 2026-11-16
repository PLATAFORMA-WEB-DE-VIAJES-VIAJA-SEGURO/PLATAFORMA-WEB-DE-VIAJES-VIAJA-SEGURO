from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, field_validator

TIPOS_DOCUMENTO_VIAJE_VALIDOS = {"PA", "CC", "CE", "TI"}
PAISES_EMISION_VALIDOS = {"CO", "MX", "PE", "AR", "CL", "ES", "US"}


class DocumentoViajeCreate(BaseModel):
    tipo_documento: str
    numero_documento: str = Field(..., min_length=4, max_length=25)
    pais_emision: str
    fecha_vencimiento: date
    es_documento_principal: bool = Field(default=False)

    @field_validator("tipo_documento", "pais_emision")
    @classmethod
    def normalizar_codigo(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("numero_documento")
    @classmethod
    def normalizar_numero(cls, v: str) -> str:
        return v.strip().upper()


class DocumentoViajeDataOut(BaseModel):
    id_documento: int
    id_usuario: int
    tipo_documento: str
    numero_documento: str
    pais_emision: str
    fecha_vencimiento: date
    es_documento_principal: bool
    estado: str


class RegistroDocumentoViajeOut(BaseModel):
    mensaje: str
    data: Optional[DocumentoViajeDataOut] = None
    success: bool


class DocumentoViaje:
    def __init__(
        self,
        id_documento: int,
        id_usuario: int,
        tipo_documento: str,
        numero_documento: str,
        pais_emision: str,
        fecha_vencimiento: date,
        es_documento_principal: bool = False,
        estado: str = "ACTIVO",
    ):
        self.id_documento = id_documento
        self.id_usuario = id_usuario
        self.tipo_documento = tipo_documento
        self.numero_documento = numero_documento
        self.pais_emision = pais_emision
        self.fecha_vencimiento = fecha_vencimiento
        self.es_documento_principal = es_documento_principal
        self.estado = estado

    def esta_activo(self) -> bool:
        return self.estado == "ACTIVO"

    def to_response(self) -> dict:
        return {
            "id_documento": self.id_documento,
            "id_usuario": self.id_usuario,
            "tipo_documento": self.tipo_documento,
            "numero_documento": self.numero_documento,
            "pais_emision": self.pais_emision,
            "fecha_vencimiento": self.fecha_vencimiento,
            "es_documento_principal": self.es_documento_principal,
            "estado": self.estado,
        }
    