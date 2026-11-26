from datetime import date
from typing import Optional
from fastapi import APIRouter, Path, Query, status
from fastapi.responses import JSONResponse
from app.domain.vuelo import (
    FlightSearchOut,
    FlightFaresQueryOut,
    SeatLockCreate,
    SeatLockOut,
)
from app.services.vuelo_service import (
    FlightService,
    FlightSearchParametersError,
    FlightBusinessRuleError,
)
from app.repositories.vuelo_repository import flight_repository

router = APIRouter(
    prefix="/api/v1/vuelos",
    tags=["Vuelos"],
)

service = FlightService(repo=flight_repository)

OPENAPI_SEARCH_FLIGHTS_RESPONSES = {
    200: {
        "description": "Vuelos disponibles consultados exitosamente",
        "model": FlightSearchOut,
    },
    400: {
        "description": "Código IATA inválido, origen igual a destino o fechas inválidas",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "El código IATA de origen o destino no es válido",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    409: {
        "description": "Sin vuelos o sin cupos suficientes para la ruta, fecha y pasajeros solicitados (RN-11)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "No se encontraron vuelos disponibles para la ruta, fecha y cantidad de pasajeros solicitados",
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
        "description": "El servicio de búsqueda de vuelos (GDS Aerolíneas) no está disponible",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "El servicio de búsqueda de vuelos (GDS Aerolíneas) no está disponible en este momento",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
}

OPENAPI_FLIGHT_FARES_RESPONSES = {
    200: {
        "description": "Tarifas del vuelo consultadas exitosamente",
        "model": FlightFaresQueryOut,
    },
    400: {
        "description": "La cabina solicitada no es válida",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "La cabina solicitada no es válida (use ECONOMICA, EJECUTIVA o PRIMERA)",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    409: {
        "description": "El vuelo no existe, no dispone de cupos o moneda inactiva (RN-13)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "El vuelo ya no dispone de cupos para cotizar tarifas vigentes",
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
        "description": "Falla de disponibilidad al consultar tarifas en AEX-01",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "No fue posible consultar las tarifas del vuelo en este momento",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
}

OPENAPI_SEAT_LOCK_RESPONSES = {
    201: {
        "description": "Puestos bloqueados temporalmente exitosamente",
        "model": SeatLockOut,
    },
    400: {
        "description": "El código de tarifa proporcionado no es válido",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "El código de tarifa proporcionado no es válido",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    409: {
        "description": "El vuelo no existe o no hay suficientes puestos disponibles (RN-15)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "No hay suficientes puestos disponibles en el vuelo para realizar el bloqueo solicitado",
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
        "description": "Falla de disponibilidad al bloquear puestos en AEX-01",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "No fue posible bloquear los puestos del vuelo en este momento",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
}


# HU-011: Buscar vuelos
@router.get(
    "",
    response_model=FlightSearchOut,
    status_code=status.HTTP_200_OK,
    responses=OPENAPI_SEARCH_FLIGHTS_RESPONSES,
    summary="Buscar vuelos",
    description="Consulta la oferta aérea disponible en AEX-01 (GDS Aerolíneas) según origen, destino, fechas y pasajeros (RN-11).",
)
def search_flights(
    origin: str = Query(..., alias="origen", min_length=3, max_length=3, description="Código IATA de origen (ej. BOG)"),
    destination: str = Query(..., alias="destino", min_length=3, max_length=3, description="Código IATA de destino (ej. CTG)"),
    departure_date: date = Query(..., alias="fecha_salida", description="Fecha de salida (YYYY-MM-DD)"),
    return_date: Optional[date] = Query(default=None, alias="fecha_regreso", description="Fecha de regreso opcional (YYYY-MM-DD)"),
    passengers: int = Query(default=1, alias="pasajeros", ge=1, le=9, description="Cantidad de pasajeros (1 a 9)"),
):
    try:
        return service.search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            passengers=passengers,
            return_date=return_date,
        )
    except FlightSearchParametersError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except FlightBusinessRuleError as exc:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "El servicio de búsqueda de vuelos (GDS Aerolíneas) no está disponible en este momento",
                "data": None,
                "success": False,
            },
        )


# HU-013: Consultar tarifas del vuelo
@router.get(
    "/{id_vuelo}/tarifas",
    response_model=FlightFaresQueryOut,
    status_code=status.HTTP_200_OK,
    responses=OPENAPI_FLIGHT_FARES_RESPONSES,
    summary="Consultar tarifas del vuelo",
    description="Obtiene las familias tarifarias del vuelo según cabina y equipaje validando moneda en AIN-02 y cupo vigente (RN-13).",
)
def get_flight_fares(
    flight_id: str = Path(..., alias="id_vuelo", min_length=3, max_length=20, description="Identificador del vuelo (ej. VL-101)"),
    cabin: Optional[str] = Query(default=None, alias="cabina", description="Filtro opcional de cabina: ECONOMICA, EJECUTIVA o PRIMERA"),
    checked_baggage: int = Query(default=0, alias="equipaje_bodega", ge=0, le=3, description="Cantidad de maletas adicionales en bodega (0 a 3)"),
):
    try:
        return service.get_flight_fares(
            flight_id=flight_id,
            cabin=cabin,
            checked_baggage=checked_baggage,
        )
    except FlightSearchParametersError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except FlightBusinessRuleError as exc:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible consultar las tarifas del vuelo en este momento",
                "data": None,
                "success": False,
            },
        )


# HU-015: Bloquear puestos temporalmente
@router.post(
    "/{id_vuelo}/bloqueo",
    response_model=SeatLockOut,
    status_code=status.HTTP_201_CREATED,
    responses=OPENAPI_SEAT_LOCK_RESPONSES,
    summary="Bloquear puestos temporalmente",
    description="Retiene temporalmente los cupos solicitados en AEX-01 durante un máximo de 20 minutos antes del cierre de compra (RN-15).",
)
def lock_flight_seats(
    payload: SeatLockCreate,
    flight_id: str = Path(..., alias="id_vuelo", min_length=3, max_length=20, description="Identificador del vuelo (ej. VL-101)"),
):
    try:
        return service.lock_flight_seats(flight_id=flight_id, data=payload)
    except FlightSearchParametersError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except FlightBusinessRuleError as exc:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible bloquear los puestos del vuelo en este momento",
                "data": None,
                "success": False,
            },
        )
