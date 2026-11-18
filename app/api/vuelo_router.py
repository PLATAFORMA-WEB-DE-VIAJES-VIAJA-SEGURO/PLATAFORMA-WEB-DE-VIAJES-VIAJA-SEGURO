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


# HU-011: Buscar vuelos
@router.get(
    "",
    response_model=FlightSearchOut,
    status_code=status.HTTP_200_OK,
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
    summary="Bloquear puestos temporalmente",
    description="Retiene temporalmente los cupos solicitados en AEX-01 durante un máximo de 20 minutos antes del cierre de compra (RN-15).",
)
def lock_flight_seats(
    payload: SeatLockCreate,
    flight_id: str = Path(..., alias="id_vuelo", min_length=3, max_length=20, description="Identificador del vuelo (ej. VL-101)"),
):
    try:
        return service.lock_flight_seats(flight_id=flight_id, data=payload)
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
