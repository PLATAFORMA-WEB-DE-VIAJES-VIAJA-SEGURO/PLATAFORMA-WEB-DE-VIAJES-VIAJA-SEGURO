from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


class BusinessRuleRN55Exception(Exception):
    """Excepción lanzada cuando se infringe la regla de negocio RN-55."""
    def __init__(self, message: str = "El destinatario ha bloqueado notificaciones o se superó el límite de reintentos"):
        self.message = message
        super().__init__(self.message)


class MessagingProviderUnavailableException(Exception):
    """Excepción lanzada cuando el proveedor externo AEX-06 no responde (503)."""
    def __init__(self, message: str = "El proveedor externo de mensajería no responde en este momento"):
        self.message = message
        super().__init__(self.message)


class NotificationParameterValidationException(Exception):
    """Excepción lanzada cuando los parámetros son inválidos (400)."""
    def __init__(self, message: str = "El canal de envío, destinatario o plantilla no son válidos"):
        self.message = message
        super().__init__(self.message)


class NotificationCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: int = Field(..., alias="id_usuario", gt=0, description="Identificador del usuario destinatario")
    channel: str = Field(..., alias="canal", min_length=1, description="Canal de envío (EMAIL o SMS)")
    recipient: str = Field(..., alias="destinatario", min_length=1, description="Dirección de correo o número telefónico")
    template: str = Field(..., alias="plantilla", min_length=1, description="Código de la plantilla activa")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Variables para interpolación")

    @field_validator("channel", "recipient", "template")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("El campo no puede estar vacío.")
        return value.strip()


class NotificationData(BaseModel):
    id_notificacion: int
    canal: str
    destinatario: str
    plantilla: str
    estado_envio: str
    fecha_envio: str


class NotificationResponse(BaseModel):
    mensaje: str
    data: Optional[NotificationData] = None
    success: bool
