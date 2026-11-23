from datetime import date
from typing import Optional
from fastapi import APIRouter, Path, Query, status
from fastapi.responses import JSONResponse
from app.domain.paquete import (
    DestinationsQueryOut,
    ActivitiesQueryOut,
    ActivityAvailabilityOut,
)
from app.services.paquete_service import (
    PackageService,
    PackageParametersError,
    PackageBusinessRuleError,
)
from app.repositories.paquete_repository import package_repository

router = APIRouter(
    prefix="/api/v1/paquetes",
    tags=["Paquetes Turísticos"],
)

service = PackageService(repo=package_repository)

OPENAPI_DESTINATIONS_RESPONSES = {
    200: {
        "description": "Destinos turísticos consultados exitosamente",
        "model": DestinationsQueryOut,
    },
    400: {
        "description": "Código de país, municipio o tipo de paquete inválido en PAR-02/PAR-03/PAR-10",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "El código de país no es válido en el catálogo PAR-02",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    409: {
        "description": "No se encontraron destinos turísticos activos para los criterios consultados (RN-23)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "No se encontraron destinos turísticos activos para los criterios consultados",
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
        "description": "El servicio de catálogo de destinos no está disponible",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "El servicio de catálogo de destinos no está disponible en este momento",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
}

OPENAPI_ACTIVITIES_RESPONSES = {
    200: {
        "description": "Actividades del destino consultadas exitosamente",
        "model": ActivitiesQueryOut,
    },
    400: {
        "description": "Fechas inválidas o categoría de actividad no válida",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "La categoría de actividad no es válida (TOUR_GUIADO, AVENTURA, GASTRONOMIA, ACUATICA, CULTURAL)",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    409: {
        "description": "El destino no existe o no cuenta con actividades disponibles en AEX-03 (RN-26)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "No se encontraron actividades disponibles en AEX-03 para el destino y criterios indicados",
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
        "description": "El servicio de operadores locales (AEX-03) no está disponible",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "El servicio de operadores locales (AEX-03) no está disponible en este momento",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
}

OPENAPI_ACTIVITY_AVAILABILITY_RESPONSES = {
    200: {
        "description": "Cupo y tarifa de actividad verificados exitosamente",
        "model": ActivityAvailabilityOut,
    },
    400: {
        "description": "La fecha solicitada para la actividad es anterior a la fecha actual",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "La fecha solicitada para la actividad no puede ser anterior a la fecha actual",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    409: {
        "description": "La actividad no existe o no hay cupos suficientes disponibles (RN-27)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "No hay cupos suficientes disponibles para la cantidad de personas solicitada en esta actividad",
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
        "description": "Falla de disponibilidad al verificar cupo y tarifa en AEX-03",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "No fue posible verificar la disponibilidad y tarifa de la actividad en AEX-03",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
}


# HU-023: Consultar destinos
@router.get(
    "/destinos",
    response_model=DestinationsQueryOut,
    status_code=status.HTTP_200_OK,
    responses=OPENAPI_DESTINATIONS_RESPONSES,
    summary="Consultar destinos",
    description="Obtiene el catálogo de destinos turísticos activos validando país (PAR-02), municipio (PAR-03) y tipo de paquete (PAR-10) mediante AIN-04 (RN-23).",
)
def get_destinations(
    country: Optional[str] = Query(default=None, alias="pais", min_length=2, max_length=3, description="Código ISO de país opcional (ej. CO, US)"),
    municipality: Optional[str] = Query(default=None, alias="municipio", min_length=3, max_length=3, description="Código IATA/municipio opcional (ej. CTG, MDE, BOG)"),
    package_type: Optional[str] = Query(default=None, alias="tipo_paquete", min_length=3, max_length=20, description="Tipo opcional: TODO_INCLUIDO, AVENTURA, CULTURAL, PLAYA, FAMILIAR"),
):
    try:
        return service.get_destinations(
            country=country,
            municipality=municipality,
            package_type=package_type,
        )
    except PackageParametersError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except PackageBusinessRuleError as exc:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(exc), "data": None, "success": False},
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
    response_model=ActivitiesQueryOut,
    status_code=status.HTTP_200_OK,
    responses=OPENAPI_ACTIVITIES_RESPONSES,
    summary="Consultar actividades del destino",
    description="Consulta los tours y atracciones disponibles en operadores locales (AEX-03) para un destino y rango de fechas (RN-26).",
)
def get_destination_activities(
    destination_id: str = Query(..., alias="id_destino", min_length=3, max_length=20, description="Identificador del destino (ej. DST-301)"),
    start_date: date = Query(..., alias="fecha_inicio", description="Fecha inicial de viaje (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(default=None, alias="fecha_fin", description="Fecha final opcional (YYYY-MM-DD)"),
    category: Optional[str] = Query(default=None, alias="categoria", description="Categoría opcional: TOUR_GUIADO, AVENTURA, GASTRONOMIA, ACUATICA, CULTURAL"),
):
    try:
        return service.get_destination_activities(
            destination_id=destination_id,
            start_date=start_date,
            end_date=end_date,
            category=category,
        )
    except PackageParametersError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except PackageBusinessRuleError as exc:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(exc), "data": None, "success": False},
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
    response_model=ActivityAvailabilityOut,
    status_code=status.HTTP_200_OK,
    responses=OPENAPI_ACTIVITY_AVAILABILITY_RESPONSES,
    summary="Verificar cupo y tarifa de actividad",
    description="Valida en tiempo real el aforo disponible y calcula la tarifa total con impuestos en AEX-03 y moneda PAR-07 vía AIN-04 (RN-27).",
)
def check_activity_availability_and_fare(
    activity_id: str = Path(..., alias="id_actividad", min_length=3, max_length=20, description="Identificador de la actividad (ej. ACT-401)"),
    activity_date: date = Query(..., alias="fecha_actividad", description="Fecha programada de la actividad (YYYY-MM-DD)"),
    people_count: int = Query(default=2, alias="cantidad_personas", ge=1, le=20, description="Cantidad de asistentes (1 a 20)"),
):
    try:
        return service.check_activity_availability_and_fare(
            activity_id=activity_id,
            activity_date=activity_date,
            people_count=people_count,
        )
    except PackageParametersError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except PackageBusinessRuleError as exc:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(exc), "data": None, "success": False},
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
