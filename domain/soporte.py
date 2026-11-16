from typing import Optional
from pydantic import BaseModel, Field, field_validator

class ReglaNegocioRN51Exception(Exception):
    """Excepción lanzada cuando se infringe la regla de negocio RN-51."""
    def __init__(self, mensaje: str = "Ya existe un caso abierto idéntico para la misma reserva"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)

class ServicioNoDisponibleException(Exception):
    """Excepción lanzada ante fallos en dependencias o almacenamiento (503)."""
    def __init__(self, mensaje: str = "No fue posible radicar el caso de soporte en este momento"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)

class ValidacionParametrosException(Exception):
    """Excepción lanzada cuando faltan parámetros o son inválidos (400)."""
    def __init__(self, mensaje: str = "El tipo de caso, asunto o descripción son obligatorios"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)

class CasoSoporteCreate(BaseModel):
    id_usuario: int = Field(..., gt=0, description="ID del usuario que radica el caso")
    codigo_reserva: Optional[str] = Field(None, description="Código alfanumérico de la reserva asociada")
    tipo_caso: str = Field(..., min_length=2, description="Categoría o tipo de solicitud de soporte")
    asunto: str = Field(..., min_length=3, description="Asunto resumido del caso")
    descripcion: str = Field(..., min_length=5, description="Descripción detallada de la solicitud")

    @field_validator("tipo_caso", "asunto", "descripcion")
    @classmethod
    def validar_no_vacio(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("El campo no puede estar vacío.")
        return v.strip()

    @field_validator("codigo_reserva")
    @classmethod
    def limpiar_codigo_reserva(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_limpio = v.strip()
            return v_limpio if v_limpio else None
        return None

class CasoSoporteData(BaseModel):
    id_caso: int
    numero_radicado: str
    id_usuario: int
    tipo_caso: str
    estado: str
    fecha_radicacion: str

class CasoSoporteResponse(BaseModel):
    mensaje: str
    data: Optional[CasoSoporteData] = None
    success: bool
