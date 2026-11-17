from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

class ReglaNegocioRN55Exception(Exception):
    """Excepción lanzada cuando se infringe la regla de negocio RN-55."""
    def __init__(self, mensaje: str = "El destinatario ha bloqueado notificaciones o se superó el límite de reintentos"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)

class ProveedorNoDisponibleException(Exception):
    """Excepción lanzada cuando el proveedor externo AEX-06 no responde (503)."""
    def __init__(self, mensaje: str = "El proveedor externo de mensajería no responde en este momento"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)

class ValidacionParametrosException(Exception):
    """Excepción lanzada cuando los parámetros son inválidos (400)."""
    def __init__(self, mensaje: str = "El canal de envío, destinatario o plantilla no son válidos"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)

class NotificacionCreate(BaseModel):
    id_usuario: int = Field(..., gt=0, description="Identificador del usuario destinatario")
    canal: str = Field(..., min_length=1, description="Canal de envío (EMAIL o SMS)")
    destinatario: str = Field(..., min_length=1, description="Dirección de correo o número telefónico")
    plantilla: str = Field(..., min_length=1, description="Código de la plantilla activa")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Variables para interpolación")

    @field_validator("canal", "destinatario", "plantilla")
    @classmethod
    def validar_no_vacio(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("El campo no puede estar vacío.")
        return v.strip()

class NotificacionData(BaseModel):
    id_notificacion: int
    canal: str
    destinatario: str
    plantilla: str
    estado_envio: str
    fecha_envio: str

class NotificacionResponse(BaseModel):
    mensaje: str
    data: Optional[NotificacionData] = None
    success: bool
