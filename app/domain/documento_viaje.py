from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

VALID_TRAVEL_DOCUMENT_TYPES = {"PA", "CC", "CE", "TI"}
VALID_ISSUING_COUNTRIES = {"CO", "MX", "PE", "AR", "CL", "ES", "US"}


class TravelDocumentCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    document_type: str = Field(..., alias="tipo_documento")
    document_number: str = Field(..., alias="numero_documento", min_length=4, max_length=25)
    issuing_country: str = Field(..., alias="pais_emision")
    expiration_date: date = Field(..., alias="fecha_vencimiento")
    is_primary_document: bool = Field(default=False, alias="es_documento_principal")

    @field_validator("document_type", "issuing_country")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("document_number")
    @classmethod
    def normalize_number(cls, value: str) -> str:
        return value.strip().upper()


class TravelDocumentDataOut(BaseModel):
    id_documento: int
    id_usuario: int
    tipo_documento: str
    numero_documento: str
    pais_emision: str
    fecha_vencimiento: date
    es_documento_principal: bool
    estado: str


class TravelDocumentRegistrationOut(BaseModel):
    mensaje: str
    data: Optional[TravelDocumentDataOut] = None
    success: bool


class TravelDocument:
    def __init__(
        self,
        document_id: int,
        user_id: int,
        document_type: str,
        document_number: str,
        issuing_country: str,
        expiration_date: date,
        is_primary_document: bool = False,
        status: str = "ACTIVO",
    ):
        self.document_id = document_id
        self.user_id = user_id
        self.document_type = document_type
        self.document_number = document_number
        self.issuing_country = issuing_country
        self.expiration_date = expiration_date
        self.is_primary_document = is_primary_document
        self.status = status

    def is_active(self) -> bool:
        return self.status == "ACTIVO"

    def to_response(self) -> dict:
        return {
            "id_documento": self.document_id,
            "id_usuario": self.user_id,
            "tipo_documento": self.document_type,
            "numero_documento": self.document_number,
            "pais_emision": self.issuing_country,
            "fecha_vencimiento": self.expiration_date,
            "es_documento_principal": self.is_primary_document,
            "estado": self.status,
        }
