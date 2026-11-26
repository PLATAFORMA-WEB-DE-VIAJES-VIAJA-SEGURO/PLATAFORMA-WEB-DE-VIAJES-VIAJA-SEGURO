"""
Módulo de Usuarios - Dominio y esquemas de validación.
Incluye reglas de negocio de registro (RN-01) e inicio de sesión (RN-02).
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from typing import Optional
import hashlib
import secrets

VALID_DOCUMENT_TYPES = {"CC", "CE", "PA", "TI"}
VALID_COUNTRIES = {"CO", "MX", "PE", "AR", "CL", "ES", "US"}
VALID_MUNICIPALITIES = {"BOG", "MDE", "CLO", "BGA", "CTG"}
VALID_ROLES = {"VIAJERO", "ASESOR", "ADMIN"}


# --- ESQUEMAS HU-001: REGISTRO ---
class UserCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    first_name: str = Field(..., alias="nombres", min_length=2, max_length=80)
    last_name: str = Field(..., alias="apellidos", min_length=2, max_length=80)
    email: EmailStr = Field(..., alias="correo")
    password: str = Field(..., min_length=8)
    document_type: str = Field(..., alias="tipo_documento")
    document_number: str = Field(..., alias="numero_documento", min_length=4, max_length=20)
    country: str = Field(..., alias="pais")
    municipality: str = Field(..., alias="municipio")
    role: Optional[str] = Field(default="VIAJERO", alias="rol")

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_letters_only(cls, value: str) -> str:
        if any(char.isdigit() for char in value):
            raise ValueError("Los nombres y apellidos no pueden contener números")
        return value.strip().title()

    @field_validator("document_type", "country", "municipality", "role")
    @classmethod
    def normalize_code(cls, value: Optional[str]) -> Optional[str]:
        return value.strip().upper() if value else value


class UserDataOut(BaseModel):
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


class UserRegistrationOut(BaseModel):
    mensaje: str
    data: Optional[UserDataOut] = None
    success: bool


# --- ESQUEMAS HU-002: INICIAR SESIÓN ---
class UserLogin(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: EmailStr = Field(..., alias="correo")
    password: str = Field(..., min_length=1)


class LoginDataOut(BaseModel):
    token: str
    tipo_token: str
    id_usuario: int
    nombres: str
    apellidos: str
    correo: str
    rol: str


class UserLoginOut(BaseModel):
    mensaje: str
    data: Optional[LoginDataOut] = None
    success: bool


# --- ENTIDAD DE DOMINIO ---
class User:
    def __init__(
        self,
        user_id: int,
        first_name: str,
        last_name: str,
        email: str,
        password_hash: str,
        document_type: str,
        document_number: str,
        country: str,
        municipality: str,
        role: str = "VIAJERO",
        status: str = "ACTIVO",
    ):
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email.lower().strip()
        self.password_hash = password_hash
        self.document_type = document_type
        self.document_number = document_number
        self.country = country
        self.municipality = municipality
        self.role = role
        self.status = status

    @staticmethod
    def hash_password(plain_password: str) -> str:
        return hashlib.sha256(plain_password.encode("utf-8")).hexdigest()

    def verify_password(self, plain_password: str) -> bool:
        return self.password_hash == self.hash_password(plain_password)

    @staticmethod
    def generate_session_token() -> str:
        return f"vs_tok_{secrets.token_urlsafe(32)}"

    def is_active(self) -> bool:
        return self.status == "ACTIVO"

    def to_response(self) -> dict:
        return {
            "id_usuario": self.user_id,
            "nombres": self.first_name,
            "apellidos": self.last_name,
            "correo": self.email,
            "tipo_documento": self.document_type,
            "numero_documento": self.document_number,
            "pais": self.country,
            "municipio": self.municipality,
            "rol": self.role,
            "estado": self.status,
        }
