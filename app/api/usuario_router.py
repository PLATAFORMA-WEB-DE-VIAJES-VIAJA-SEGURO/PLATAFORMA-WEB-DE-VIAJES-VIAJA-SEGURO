from typing import List
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.domain.usuario import (
    UsuarioCreate,
    UsuarioDataOut,
    RegistroUsuarioOut,
    UsuarioLogin,
    LoginUsuarioOut,
)
from app.services.usuario_service import (
    UsuarioService,
    ErrorCatalogoInvalido,
    ErrorCorreoDuplicado,
    ErrorCredencialesInvalidas,
)
from app.repositories.usuario_repository import usuario_repository

router = APIRouter(
    prefix="/api/v1/usuarios",
    tags=["Usuarios"],
)

service = UsuarioService(repo=usuario_repository)


@router.post(
    "/registro",
    response_model=RegistroUsuarioOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar usuario",
    description="Crea una cuenta nueva validando catálogos y que el correo no esté registrado en otra cuenta activa.",
)
def registrar_usuario(datos: UsuarioCreate):
    try:
        return service.registrar_usuario(datos)
    except ErrorCatalogoInvalido as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(e), "data": None, "success": False},
        )
    except ErrorCorreoDuplicado as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(e), "data": None, "success": False},
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
    response_model=LoginUsuarioOut,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión",
    description="Autentica al usuario verificando que la cuenta esté activa (RN-02) y retorna un token de sesión.",
)
def iniciar_sesion(datos: UsuarioLogin):
    try:
        return service.iniciar_sesion(datos)
    except ErrorCredencialesInvalidas as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"mensaje": str(e), "data": None, "success": False},
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
    response_model=List[UsuarioDataOut],
    status_code=status.HTTP_200_OK,
    summary="Listar usuarios activos",
)
def listar_usuarios():
    return service.listar_usuarios()