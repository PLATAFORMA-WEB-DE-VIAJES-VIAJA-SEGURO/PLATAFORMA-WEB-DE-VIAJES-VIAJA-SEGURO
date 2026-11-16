from datetime import date
from typing import Optional
from fastapi import APIRouter, Path, Query, status
from fastapi.responses import JSONResponse
from app.domain.vuelo import BusquedaVuelosOut, ConsultaTarifasVueloOut
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


# HU-011: Buscar vuelos
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


# HU-013: Consultar tarifas del vuelo
@router.get(
    "/{id_vuelo}/tarifas",
    response_model=ConsultaTarifasVueloOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar tarifas del vuelo",
    description="Obtiene las familias tarifarias del vuelo según cabina y equipaje validando moneda en AIN-02 y cupo vigente (RN-13).",
)
def consultar_tarifas_vuelo(
    id_vuelo: str = Path(..., min_length=3, max_length=20, description="Identificador del vuelo (ej. VL-101)"),
    cabina: Optional[str] = Query(default=None, description="Filtro opcional de cabina: ECONOMICA, EJECUTIVA o PRIMERA"),
    equipaje_bodega: int = Query(default=0, ge=0, le=3, description="Cantidad de maletas adicionales en bodega (0 a 3)"),
):
    try:
        return service.consultar_tarifas_vuelo(
            id_vuelo=id_vuelo,
            cabina=cabina,
            equipaje_bodega=equipaje_bodega,
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
                "mensaje": "No fue posible consultar las tarifas del vuelo en este momento",
                "data": None,
                "success": False,
            },
        )