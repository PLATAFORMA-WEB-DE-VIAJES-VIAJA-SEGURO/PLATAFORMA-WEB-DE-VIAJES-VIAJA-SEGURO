from typing import List
from fastapi import APIRouter, Path, status
from fastapi.responses import JSONResponse
from app.domain.documento_viaje import (
    DocumentoViajeCreate,
    DocumentoViajeDataOut,
    RegistroDocumentoViajeOut,
)
from app.services.documento_viaje_service import (
    DocumentoViajeService,
    ErrorCatalogoDocumentoInvalido,
    ErrorReglaNegocioDocumento,
)
from app.repositories.documento_viaje_repository import documento_viaje_repository
from app.repositories.usuario_repository import usuario_repository

router = APIRouter(
    prefix="/api/v1/usuarios/{id_usuario}/documentos",
    tags=["Usuarios - Documentos de Viaje"],
)

service = DocumentoViajeService(
    repo=documento_viaje_repository,
    usuario_repo=usuario_repository,
)


@router.post(
    "",
    response_model=RegistroDocumentoViajeOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar documento de viaje",
    description="Registra un documento legal (pasaporte, cédula, etc.) para el viajero validando catálogos (AIN-01) y vigencia (RN-08).",
)
def registrar_documento_viaje(
    datos: DocumentoViajeCreate,
    id_usuario: int = Path(..., gt=0, description="Identificador del usuario activo"),
):
    try:
        return service.registrar_documento(id_usuario, datos)
    except ErrorCatalogoDocumentoInvalido as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(e), "data": None, "success": False},
        )
    except ErrorReglaNegocioDocumento as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(e), "data": None, "success": False},
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible registrar el documento de viaje en este momento",
                "data": None,
                "success": False,
            },
        )


@router.get(
    "",
    response_model=List[DocumentoViajeDataOut],
    status_code=status.HTTP_200_OK,
    summary="Listar documentos de viaje activos del usuario",
)
def listar_documentos_viaje(
    id_usuario: int = Path(..., gt=0, description="Identificador del usuario activo"),
):
    return service.listar_documentos_usuario(id_usuario)
