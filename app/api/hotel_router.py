from datetime import date
from typing import Optional
from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse
from app.domain.hotel import BusquedaHotelesOut
from app.services.hotel_service import (
    HotelService,
    ErrorParametrosHotel,
    ErrorReglaNegocioHotel,
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
    response_model=BusquedaHotelesOut,
    status_code=status.HTTP_200_OK,
    summary="Buscar hoteles",
    description="Consulta la oferta hotelera disponible en AEX-02 validando ciudad (PAR-03) y categoría (PAR-08) mediante AIN-03 (RN-17).",
)
def buscar_hoteles(
    ciudad: str = Query(..., min_length=3, max_length=3, description="Código IATA/municipio destino (ej. CTG)"),
    fecha_entrada: date = Query(..., description="Fecha de check-in (YYYY-MM-DD)"),
    fecha_salida: date = Query(..., description="Fecha de check-out (YYYY-MM-DD)"),
    huespedes: int = Query(default=1, ge=1, le=10, description="Cantidad de huéspedes (1 a 10)"),
    categoria: Optional[str] = Query(default=None, description="Categoría opcional: 3_ESTRELLAS, 4_ESTRELLAS, 5_ESTRELLAS, BOUTIQUE"),
):
    try:
        return service.buscar_hoteles(
            ciudad=ciudad,
            fecha_entrada=fecha_entrada,
            fecha_salida=fecha_salida,
            huespedes=huespedes,
            categoria=categoria,
        )
    except ErrorParametrosHotel as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(e), "data": None, "success": False},
        )
    except ErrorReglaNegocioHotel as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(e), "data": None, "success": False},
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
    