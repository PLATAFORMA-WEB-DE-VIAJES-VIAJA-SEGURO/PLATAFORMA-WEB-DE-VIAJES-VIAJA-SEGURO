from typing import Optional
from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse
from app.domain.paquete import ConsultaDestinosOut
from app.services.paquete_service import (
    PaqueteService,
    ErrorParametrosPaquete,
    ErrorReglaNegocioPaquete,
)
from app.repositories.paquete_repository import paquete_repository

router = APIRouter(
    prefix="/api/v1/paquetes",
    tags=["Paquetes Turísticos"],
)

service = PaqueteService(repo=paquete_repository)


# HU-023: Consultar destinos
@router.get(
    "/destinos",
    response_model=ConsultaDestinosOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar destinos",
    description="Obtiene el catálogo de destinos turísticos activos validando país (PAR-02), municipio (PAR-03) y tipo de paquete (PAR-10) mediante AIN-04 (RN-23).",
)
def consultar_destinos(
    pais: Optional[str] = Query(default=None, description="Código ISO de país opcional (ej. CO, US)"),
    municipio: Optional[str] = Query(default=None, description="Código IATA/municipio opcional (ej. CTG, MDE, BOG)"),
    tipo_paquete: Optional[str] = Query(default=None, description="Tipo opcional: TODO_INCLUIDO, AVENTURA, CULTURAL, PLAYA, FAMILIAR"),
):
    try:
        return service.consultar_destinos(
            pais=pais,
            municipio=municipio,
            tipo_paquete=tipo_paquete,
        )
    except ErrorParametrosPaquete as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(e), "data": None, "success": False},
        )
    except ErrorReglaNegocioPaquete as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(e), "data": None, "success": False},
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "El servicio de catálogo de destinos no está disponible en este momento",
                "data": None,
                "success": False,
            },
        )