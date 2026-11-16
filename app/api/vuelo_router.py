from datetime import date
from typing import Optional
from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse
from app.domain.vuelo import BusquedaVuelosOut
from app.services.vuelo_service import (
    VueloService,
    ErrorParametrosBusquedaVuelo,
    ErrorReglaNegocioVuelo,
)
from app.repositories.vuelo_repository import vuelo_repository

router = APIRouter(
    prefix="/api/v1/vuelos",
    tags=["Vuelos"],
)

service = VueloService(repo=vuelo_repository)


@router.get(
    "",
    response_model=BusquedaVuelosOut,
    status_code=status.HTTP_200_OK,
    summary="Buscar vuelos",
    description="Consulta la oferta aérea disponible en AEX-01 (GDS Aerolíneas) según origen, destino, fechas y pasajeros (RN-11).",
)
def buscar_vuelos(
    origen: str = Query(..., min_length=3, max_length=3, description="Código IATA de origen (ej. BOG)"),
    destino: str = Query(..., min_length=3, max_length=3, description="Código IATA de destino (ej. CTG)"),
    fecha_salida: date = Query(..., description="Fecha de salida (YYYY-MM-DD)"),
    fecha_regreso: Optional[date] = Query(default=None, description="Fecha de regreso opcional (YYYY-MM-DD)"),
    pasajeros: int = Query(default=1, ge=1, le=9, description="Cantidad de pasajeros (1 a 9)"),
):
    try:
        return service.buscar_vuelos(
            origen=origen,
            destino=destino,
            fecha_salida=fecha_salida,
            pasajeros=pasajeros,
            fecha_regreso=fecha_regreso,
        )
    except ErrorParametrosBusquedaVuelo as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(e), "data": None, "success": False},
        )
    except ErrorReglaNegocioVuelo as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(e), "data": None, "success": False},
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
    