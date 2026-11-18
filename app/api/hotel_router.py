from datetime import date
from typing import Optional
from fastapi import APIRouter, Path, Query, status
from fastapi.responses import JSONResponse
from app.domain.hotel import (
    HotelSearchOut,
    RoomRatesQueryOut,
    RoomLockIn,
    RoomLockOut,
)
from app.services.hotel_service import (
    HotelService,
    HotelParametersError,
    HotelBusinessRuleError,
)
from app.repositories.hotel_repository import hotel_repository

router = APIRouter(
    prefix="/api/v1/hoteles",
    tags=["Hoteles"],
)

service = HotelService(repo=hotel_repository)


# HU-017: Buscar hoteles
@router.get(
    "",
    response_model=HotelSearchOut,
    status_code=status.HTTP_200_OK,
    summary="Buscar hoteles",
    description="Consulta la oferta hotelera disponible en AEX-02 validando ciudad (PAR-03) y categoría (PAR-08) mediante AIN-03 (RN-17).",
)
def search_hotels(
    city: str = Query(..., alias="ciudad", min_length=3, max_length=3, description="Código IATA/municipio destino (ej. CTG)"),
    check_in_date: date = Query(..., alias="fecha_entrada", description="Fecha de check-in (YYYY-MM-DD)"),
    check_out_date: date = Query(..., alias="fecha_salida", description="Fecha de check-out (YYYY-MM-DD)"),
    guests: int = Query(default=1, alias="huespedes", ge=1, le=10, description="Cantidad de huéspedes (1 a 10)"),
    category: Optional[str] = Query(default=None, alias="categoria", description="Categoría opcional: 3_ESTRELLAS, 4_ESTRELLAS, 5_ESTRELLAS, BOUTIQUE"),
):
    try:
        return service.search_hotels(
            city=city,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            guests=guests,
            category=category,
        )
    except HotelParametersError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except HotelBusinessRuleError as exc:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "El servicio de oferta hotelera (AEX-02) no está disponible en este momento",
                "data": None,
                "success": False,
            },
        )


# HU-019: Consultar habitaciones y tarifas
@router.get(
    "/{id_hotel}/habitaciones",
    response_model=RoomRatesQueryOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar habitaciones y tarifas",
    description="Obtiene los tipos de habitación (PAR-09), capacidad máxima y total por estadía validando moneda (PAR-07) vía AIN-03 (RN-19).",
)
def get_rooms_and_rates(
    hotel_id: str = Path(..., alias="id_hotel", min_length=3, max_length=20, description="Identificador del hotel (ej. HT-201)"),
    check_in_date: date = Query(..., alias="fecha_entrada", description="Fecha de check-in (YYYY-MM-DD)"),
    check_out_date: date = Query(..., alias="fecha_salida", description="Fecha de check-out (YYYY-MM-DD)"),
    guests: int = Query(default=2, alias="huespedes", ge=1, le=6, description="Cantidad de huéspedes (1 a 6)"),
    room_type: Optional[str] = Query(default=None, alias="tipo_habitacion", description="Filtro opcional: ESTANDAR, DOBLE, SUITE, FAMILIAR"),
):
    try:
        return service.get_rooms_and_rates(
            hotel_id=hotel_id,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            guests=guests,
            room_type=room_type,
        )
    except HotelParametersError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except HotelBusinessRuleError as exc:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible consultar las habitaciones y tarifas del hotel en este momento",
                "data": None,
                "success": False,
            },
        )


# HU-021: Bloquear habitación temporalmente
@router.post(
    "/bloqueos",
    response_model=RoomLockOut,
    status_code=status.HTTP_201_CREATED,
    summary="Bloquear habitación temporalmente",
    description="Retiene temporalmente el inventario de habitaciones en AEX-02 validando tipo de habitación (PAR-09) y moneda (PAR-07) mediante AIN-03 (RN-21).",
)
def lock_room(payload: RoomLockIn):
    try:
        return service.lock_room(payload)
    except HotelParametersError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except HotelBusinessRuleError as exc:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "El proveedor hotelero (AEX-02) no está disponible para registrar el bloqueo temporal",
                "data": None,
                "success": False,
            },
        )
