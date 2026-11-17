from datetime import date
from typing import Optional
from app.domain.vuelo import (
    AEROPUERTOS_VALIDOS,
    CABINAS_VALIDAS,
    MONEDAS_VALIDAS_AIN02,
    VueloItemOut,
    BusquedaVuelosOut,
    TarifaVueloItemOut,
    ConsultaTarifasVueloOut,
    BloqueoPuestosCreate,
    BloqueoPuestosDataOut,
    BloqueoPuestosOut,
)
from app.repositories.vuelo_repository import VueloRepository


class ErrorParametrosBusquedaVuelo(Exception):
    pass


class ErrorReglaNegocioVuelo(Exception):
    pass


class VueloService:
    def __init__(self, repo: VueloRepository):
        self.repo = repo

    # HU-011: Buscar vuelos (RN-11)
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

        resultados = self.repo.buscar_vuelos(
            origen=origen_norm,
            destino=destino_norm,
            fecha_salida=fecha_salida,
            pasajeros=pasajeros,
        )

        if not resultados:
            raise ErrorReglaNegocioVuelo(
                "No se encontraron vuelos disponibles para la ruta, fecha y cantidad de pasajeros solicitados"
            )

        return BusquedaVuelosOut(
            mensaje="Vuelos disponibles consultados exitosamente",
            data=[VueloItemOut(**v.to_response()) for v in resultados],
            success=True,
        )

    # HU-013: Consultar tarifas del vuelo (RN-13)
    def consultar_tarifas_vuelo(
        self,
        id_vuelo: str,
        cabina: Optional[str] = None,
        equipaje_bodega: int = 0,
    ) -> ConsultaTarifasVueloOut:
        cabina_norm = cabina.strip().upper() if cabina else None
        if cabina_norm and cabina_norm not in CABINAS_VALIDAS:
            raise ErrorParametrosBusquedaVuelo(
                "La cabina solicitada no es válida (use ECONOMICA, EJECUTIVA o PRIMERA)"
            )

        vuelo = self.repo.obtener_por_id(id_vuelo)
        if not vuelo:
            raise ErrorReglaNegocioVuelo(
                "El vuelo solicitado no existe o no cuenta con tarifas vigentes"
            )

        if vuelo.moneda not in MONEDAS_VALIDAS_AIN02:
            raise ErrorReglaNegocioVuelo(
                "La moneda configurada para la tarifa no se encuentra activa en AIN-02"
            )

        if vuelo.puestos_disponibles <= 0:
            raise ErrorReglaNegocioVuelo(
                "El vuelo ya no dispone de cupos para cotizar tarifas vigentes"
            )

        tarifas = vuelo.generar_familias_tarifarias(
            cabina=cabina_norm,
            equipaje_bodega=equipaje_bodega,
        )

        return ConsultaTarifasVueloOut(
            mensaje="Tarifas del vuelo consultadas exitosamente",
            data=[TarifaVueloItemOut(**t) for t in tarifas],
            success=True,
        )

    # HU-015: Bloquear puestos temporalmente (RN-15)
    def bloquear_puestos_vuelo(
        self, id_vuelo: str, datos: BloqueoPuestosCreate
    ) -> BloqueoPuestosOut:
        vuelo = self.repo.obtener_por_id(id_vuelo)
        if not vuelo:
            raise ErrorReglaNegocioVuelo(
                "El vuelo solicitado no existe o ya no se encuentra activo"
            )

        if vuelo.puestos_disponibles < datos.cantidad_puestos:
            raise ErrorReglaNegocioVuelo(
                "No hay suficientes puestos disponibles en el vuelo para realizar el bloqueo solicitado"
            )

        bloqueo = self.repo.crear_bloqueo(
            vuelo=vuelo,
            cantidad_puestos=datos.cantidad_puestos,
            tiempo_bloqueo_minutos=datos.tiempo_bloqueo_minutos,
        )

        return BloqueoPuestosOut(
            mensaje="Puestos bloqueados temporalmente exitosamente",
            data=BloqueoPuestosDataOut(**bloqueo.to_response()),
            success=True,
        )