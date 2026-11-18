from typing import List
from fastapi import APIRouter, Path, status
from fastapi.responses import JSONResponse
from app.domain.documento_viaje import (
    TravelDocumentCreate,
    TravelDocumentDataOut,
    TravelDocumentRegistrationOut,
)
from app.services.documento_viaje_service import (
    TravelDocumentService,
    InvalidDocumentCatalogError,
    DocumentBusinessRuleError,
)
from app.repositories.documento_viaje_repository import travel_document_repository
from app.repositories.usuario_repository import user_repository

router = APIRouter(
    prefix="/api/v1/usuarios/{id_usuario}/documentos",
    tags=["Usuarios - Documentos de Viaje"],
)

service = TravelDocumentService(
    repo=travel_document_repository,
    user_repo=user_repository,
)


@router.post(
    "",
    response_model=TravelDocumentRegistrationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar documento de viaje",
    description="Registra un documento legal (pasaporte, cédula, etc.) para el viajero validando catálogos (AIN-01) y vigencia (RN-08).",
)
def register_travel_document(
    payload: TravelDocumentCreate,
    user_id: int = Path(..., alias="id_usuario", gt=0, description="Identificador del usuario activo"),
):
    try:
        return service.register_document(user_id, payload)
    except InvalidDocumentCatalogError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except DocumentBusinessRuleError as exc:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(exc), "data": None, "success": False},
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
    response_model=List[TravelDocumentDataOut],
    status_code=status.HTTP_200_OK,
    summary="Listar documentos de viaje activos del usuario",
)
def list_travel_documents(
    user_id: int = Path(..., alias="id_usuario", gt=0, description="Identificador del usuario activo"),
):
    return service.list_user_documents(user_id)
