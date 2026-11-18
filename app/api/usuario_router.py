from typing import List
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.domain.usuario import (
    UserCreate,
    UserDataOut,
    UserRegistrationOut,
    UserLogin,
    UserLoginOut,
)
from app.services.usuario_service import (
    UserService,
    InvalidCatalogError,
    DuplicateEmailError,
    InvalidCredentialsError,
)
from app.repositories.usuario_repository import user_repository

router = APIRouter(
    prefix="/api/v1/usuarios",
    tags=["Usuarios"],
)

service = UserService(repo=user_repository)


@router.post(
    "/registro",
    response_model=UserRegistrationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar usuario",
    description="Crea una cuenta nueva validando catálogos y que el correo no esté registrado en otra cuenta activa.",
)
def register_user(payload: UserCreate):
    try:
        return service.register_user(payload)
    except InvalidCatalogError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except DuplicateEmailError as exc:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible completar el registro en este momento",
                "data": None,
                "success": False,
            },
        )


@router.post(
    "/login",
    response_model=UserLoginOut,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión",
    description="Autentica al usuario verificando que la cuenta esté activa (RN-02) y retorna un token de sesión.",
)
def login_user(payload: UserLogin):
    try:
        return service.login_user(payload)
    except InvalidCredentialsError as exc:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible iniciar sesión en este momento",
                "data": None,
                "success": False,
            },
        )


@router.get(
    "/",
    response_model=List[UserDataOut],
    status_code=status.HTTP_200_OK,
    summary="Listar usuarios activos",
)
def list_users():
    return service.list_users()
