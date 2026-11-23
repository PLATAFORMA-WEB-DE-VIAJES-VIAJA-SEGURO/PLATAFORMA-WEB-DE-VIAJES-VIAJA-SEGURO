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
    LoginParametersError,
)
from app.repositories.usuario_repository import user_repository

router = APIRouter(
    prefix="/api/v1/usuarios",
    tags=["Usuarios"],
)

service = UserService(repo=user_repository)

OPENAPI_REGISTER_USER_RESPONSES = {
    201: {
        "description": "Usuario registrado exitosamente",
        "model": UserRegistrationOut,
    },
    400: {
        "description": "El tipo de documento, rol o ubicación proporcionada no son válidos",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "El tipo de documento, rol o ubicación proporcionada no son válidos",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    409: {
        "description": "El correo electrónico ya se encuentra registrado en una cuenta activa (RN-01)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "El correo electrónico ya se encuentra registrado en una cuenta activa",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    422: {
        "description": "Parámetros de entrada inválidos o incompletos (validación de esquema)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Parámetros de entrada inválidos o incompletos",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    503: {
        "description": "Falla de disponibilidad en el almacenamiento de MOD-01",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "No fue posible completar el registro en este momento",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
}

OPENAPI_LOGIN_USER_RESPONSES = {
    200: {
        "description": "Inicio de sesión exitoso",
        "model": UserLoginOut,
    },
    400: {
        "description": "Los parámetros de inicio de sesión son inválidos o incompletos",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Los parámetros de inicio de sesión son inválidos o incompletos",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    409: {
        "description": "Credenciales inválidas o cuenta inactiva (RN-02)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Credenciales inválidas o cuenta inactiva",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    422: {
        "description": "Parámetros de entrada inválidos o incompletos (validación de esquema)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Parámetros de entrada inválidos o incompletos",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    503: {
        "description": "Falla de disponibilidad en el servicio de autenticación",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "No fue posible iniciar sesión en este momento",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
}


@router.post(
    "/registro",
    response_model=UserRegistrationOut,
    status_code=status.HTTP_201_CREATED,
    responses=OPENAPI_REGISTER_USER_RESPONSES,
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
    responses=OPENAPI_LOGIN_USER_RESPONSES,
    summary="Iniciar sesión",
    description="Autentica al usuario verificando que la cuenta esté activa (RN-02) y retorna un token de sesión.",
)
def login_user(payload: UserLogin):
    try:
        return service.login_user(payload)
    except LoginParametersError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except InvalidCredentialsError as exc:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
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
