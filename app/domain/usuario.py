from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import hashlib

TIPOS_DOCUMENTO_VALIDOS = {"CC", "CE", "PA", "TI"}
PAISES_VALIDOS = {"CO", "MX", "PE", "AR", "CL", "ES", "US"}
MUNICIPIOS_VALIDOS = {"BOG", "MDE", "CLO", "BGA", "CTG"}
ROLES_VALIDOS = {"VIAJERO", "ASESOR", "ADMIN"}


class UsuarioCreate(BaseModel):
    nombres: str = Field(..., min_length=2, max_length=80)
    apellidos: str = Field(..., min_length=2, max_length=80)
    correo: EmailStr
    password: str = Field(..., min_length=8)
    tipo_documento: str
    numero_documento: str = Field(..., min_length=4, max_length=20)
    pais: str
    municipio: str
    rol: Optional[str] = Field(default="VIAJERO")

    @field_validator("nombres", "apellidos")
    @classmethod
    def validar_solo_letras(cls, v: str) -> str:
        if any(c.isdigit() for c in v):
            raise ValueError("Los nombres y apellidos no pueden contener números")
        return v.strip().title()

    @field_validator("tipo_documento", "pais", "municipio", "rol")
    @classmethod
    def normalizar_codigo(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().upper() if v else v


class UsuarioDataOut(BaseModel):
    id_usuario: int
    nombres: str
    apellidos: str
    correo: str
    tipo_documento: str
    numero_documento: str
    pais: str
    municipio: str
    rol: str
    estado: str


class RegistroUsuarioOut(BaseModel):
    mensaje: str
    data: Optional[UsuarioDataOut] = None
    success: bool


class Usuario:
    def __init__(
        self,
        id_usuario: int,
        nombres: str,
        apellidos: str,
        correo: str,
        password_hash: str,
        tipo_documento: str,
        numero_documento: str,
        pais: str,
        municipio: str,
        rol: str = "VIAJERO",
        estado: str = "ACTIVO",
    ):
        self.id_usuario = id_usuario
        self.nombres = nombres
        self.apellidos = apellidos
        self.correo = correo.lower().strip()
        self.password_hash = password_hash
        self.tipo_documento = tipo_documento
        self.numero_documento = numero_documento
        self.pais = pais
        self.municipio = municipio
        self.rol = rol
        self.estado = estado

    @staticmethod
    def encriptar_password(password_plano: str) -> str:
        return hashlib.sha256(password_plano.encode("utf-8")).hexdigest()

    def esta_activo(self) -> bool:
        return self.estado == "ACTIVO"

    def to_response(self) -> dict:
        return {
            "id_usuario": self.id_usuario,
            "nombres": self.nombres,
            "apellidos": self.apellidos,
            "correo": self.correo,
            "tipo_documento": self.tipo_documento,
            "numero_documento": self.numero_documento,
            "pais": self.pais,
            "municipio": self.municipio,
            "rol": self.rol,
            "estado": self.estado,
        }