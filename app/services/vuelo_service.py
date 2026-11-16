from datetime import date
from typing import Optional
from app.domain.vuelo import (
    AEROPUERTOS_VALIDOS,
    VueloItemOut,
    BusquedaVuelosOut,
)
from app.repositories.vuelo_repository import VueloRepository


class ErrorParametrosBusquedaVuelo(Exception):
    pass


class ErrorReglaNegocioVuelo(Exception):
    pass


class VueloService:
    def __init__(self, repo: VueloRepository):
        self.repo = repo

    def buscar_vuelos(
        self,
        origen: str,
        destino: str,
        fecha_salida: date,
        pasajeros: int,
        fecha_regreso: Optional[date] = None,
    ) -> BusquedaVuelosOut:
        origen_norm = origen.strip().upper()
        destino_norm = destino.strip().upper()

        if origen_norm != "503" and origen_norm not in AEROPUERTOS_VALIDOS:
            raise ErrorParametrosBusquedaVuelo(
                "El código IATA de origen o destino no es válido"
            )
        if destino_norm != "503" and destino_norm not in AEROPUERTOS_VALIDOS:
            raise ErrorParametrosBusquedaVuelo(
                "El código IATA de origen o destino no es válido"
            )
        if origen_norm == destino_norm:
            raise ErrorParametrosBusquedaVuelo(
                "La ciudad de origen y destino no pueden ser iguales"
            )
        if fecha_salida < date.today():
            raise ErrorParametrosBusquedaVuelo(
                "La fecha de salida no puede ser anterior a la fecha actual"
            )
        if fecha_regreso and fecha_regreso < fecha_salida:
            raise ErrorParametrosBusquedaVuelo(
                "La fecha de regreso no puede ser anterior a la fecha de salida"
            )

        # Consulta simulada al proveedor externo AEX-01 (GDS Aerolíneas)
        resultados = self.repo.buscar_vuelos(
            origen=origen_norm,
            destino=destino_norm,
            fecha_salida=fecha_salida,
            pasajeros=pasajeros,
        )

        # RN-11: Si no hay disponibilidad suficiente para la ruta/fecha/pasajeros, retorna 409
        if not resultados:
            raise ErrorReglaNegocioVuelo(
                "No se encontraron vuelos disponibles para la ruta, fecha y cantidad de pasajeros solicitados"
            )

        return BusquedaVuelosOut(
            mensaje="Vuelos disponibles consultados exitosamente",
            data=[VueloItemOut(**v.to_response()) for v in resultados],
            success=True,
        )