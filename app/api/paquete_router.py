from datetime import date
from typing import Optional
from fastapi import APIRouter, Path, Query, status
from fastapi.responses import JSONResponse
from app.domain.paquete import (
    ConsultaDestinosOut,
    ConsultaActividadesOut,
    DisponibilidadActividadOut,
)
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


# HU-026: Consultar actividades del destino
@router.get(
    "/actividades",
    response_model=ConsultaActividadesOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar actividades del destino",
    description="Consulta los tours y atracciones disponibles en operadores locales (AEX-03) para un destino y rango de fechas (RN-26).",
)
def consultar_actividades_destino(
    id_destino: str = Query(..., min_length=3, max_length=20, description="Identificador del destino (ej. DST-301)"),
    fecha_inicio: date = Query(..., description="Fecha inicial de viaje (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(default=None, description="Fecha final opcional (YYYY-MM-DD)"),
    categoria: Optional[str] = Query(default=None, description="Categoría opcional: TOUR_GUIADO, AVENTURA, GASTRONOMIA, ACUATICA, CULTURAL"),
):
    try:
        return service.consultar_actividades_destino(
            id_destino=id_destino,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            categoria=categoria,
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
                "mensaje": "El servicio de operadores locales (AEX-03) no está disponible en este momento",
                "data": None,
                "success": False,
            },
        )


# HU-027: Verificar cupo y tarifa de actividad
@router.get(
    "/actividades/{id_actividad}/disponibilidad",
    response_model=DisponibilidadActividadOut,
    status_code=status.HTTP_200_OK,
    summary="Verificar cupo y tarifa de actividad",
    description="Valida en tiempo real el aforo disponible y calcula la tarifa total con impuestos en AEX-03 y moneda PAR-07 vía AIN-04 (RN-27).",
)
def verificar_cupo_tarifa_actividad(
    id_actividad: str = Path(..., min_length=3, max_length=20, description="Identificador de la actividad (ej. ACT-401)"),
    fecha_actividad: date = Query(..., description="Fecha programada de la actividad (YYYY-MM-DD)"),
    cantidad_personas: int = Query(default=2, ge=1, le=20, description="Cantidad de asistentes (1 a 20)"),
):
    try:
        return service.verificar_cupo_tarifa_actividad(
            id_actividad=id_actividad,
            fecha_actividad=fecha_actividad,
            cantidad_personas=cantidad_personas,
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
                "mensaje": "No fue posible verificar la disponibilidad y tarifa de la actividad en AEX-03",
                "data": None,
                "success": False,
            },
        )