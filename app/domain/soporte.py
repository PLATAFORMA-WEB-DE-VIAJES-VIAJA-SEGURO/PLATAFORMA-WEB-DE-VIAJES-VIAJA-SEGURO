from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class BusinessRuleRN51Exception(Exception):
    """Excepción lanzada cuando se infringe la regla de negocio RN-51."""
    def __init__(self, message: str = "Ya existe un caso abierto idéntico para la misma reserva"):
        self.message = message
        super().__init__(self.message)


class SupportServiceUnavailableException(Exception):
    """Excepción lanzada ante fallos en dependencias o almacenamiento (503)."""
    def __init__(self, message: str = "No fue posible radicar el caso de soporte en este momento"):
        self.message = message
        super().__init__(self.message)


class SupportParameterValidationException(Exception):
    """Excepción lanzada cuando faltan parámetros o son inválidos (400)."""
    def __init__(self, message: str = "El tipo de caso, asunto o descripción son obligatorios"):
        self.message = message
        super().__init__(self.message)


class SupportCaseCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: int = Field(..., alias="id_usuario", gt=0, description="ID del usuario que radica el caso")
    reservation_code: Optional[str] = Field(None, alias="codigo_reserva", description="Código alfanumérico de la reserva asociada")
    case_type: str = Field(..., alias="tipo_caso", min_length=2, description="Categoría o tipo de solicitud de soporte")
    subject: str = Field(..., alias="asunto", min_length=3, description="Asunto resumido del caso")
    description: str = Field(..., alias="descripcion", min_length=5, description="Descripción detallada de la solicitud")

    @field_validator("case_type", "subject", "description")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("El campo no puede estar vacío.")
        return value.strip()

    @field_validator("reservation_code")
    @classmethod
    def clean_reservation_code(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            cleaned = value.strip()
            return cleaned if cleaned else None
        return None


class SupportCaseData(BaseModel):
    id_caso: int
    numero_radicado: str
    id_usuario: int
    tipo_caso: str
    estado: str
    fecha_radicacion: str


class SupportCaseResponse(BaseModel):
    mensaje: str
    data: Optional[SupportCaseData] = None
    success: bool
