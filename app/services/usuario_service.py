from typing import List
from app.domain.usuario import (
    User,
    UserCreate,
    UserDataOut,
    UserRegistrationOut,
    UserLogin,
    LoginDataOut,
    UserLoginOut,
    VALID_DOCUMENT_TYPES,
    VALID_COUNTRIES,
    VALID_MUNICIPALITIES,
    VALID_ROLES,
)
from app.repositories.usuario_repository import UserRepository


class InvalidCatalogError(Exception):
    pass


class DuplicateEmailError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class LoginParametersError(Exception):
    pass


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def _validate_references(self, data: UserCreate) -> None:
        if (
            data.document_type not in VALID_DOCUMENT_TYPES
            or data.country not in VALID_COUNTRIES
            or data.municipality not in VALID_MUNICIPALITIES
            or (data.role and data.role not in VALID_ROLES)
        ):
            raise InvalidCatalogError(
                "El tipo de documento, rol o ubicación proporcionada no son válidos"
            )

    def register_user(self, data: UserCreate) -> UserRegistrationOut:
        self._validate_references(data)

        if self.repo.get_active_by_email(data.email):
            raise DuplicateEmailError(
                "El correo electrónico ya se encuentra registrado en una cuenta activa"
            )

        password_hash = User.hash_password(data.password)
        created_user = self.repo.create(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            password_hash=password_hash,
            document_type=data.document_type,
            document_number=data.document_number,
            country=data.country,
            municipality=data.municipality,
            role=data.role or "VIAJERO",
        )

        return UserRegistrationOut(
            mensaje="Usuario registrado exitosamente",
            data=UserDataOut(**created_user.to_response()),
            success=True,
        )

    def login_user(self, data: UserLogin) -> UserLoginOut:
        if not data.password or not data.password.strip() or len(data.password.strip()) < 4:
            raise LoginParametersError(
                "Los parámetros de inicio de sesión son inválidos o incompletos"
            )

        user = self.repo.get_by_email(data.email)

        # RN-02: Verifica existencia, estado ACTIVO y coincidencia de hash
        if not user or not user.is_active() or not user.verify_password(data.password):
            raise InvalidCredentialsError(
                "Credenciales inválidas o cuenta inactiva"
            )

        token = User.generate_session_token()

        return UserLoginOut(
            mensaje="Inicio de sesión exitoso",
            data=LoginDataOut(
                token=token,
                tipo_token="Bearer",
                id_usuario=user.user_id,
                nombres=user.first_name,
                apellidos=user.last_name,
                correo=user.email,
                rol=user.role,
            ),
            success=True,
        )

    def list_users(self) -> List[UserDataOut]:
        return [
            UserDataOut(**user.to_response())
            for user in self.repo.get_all()
        ]
