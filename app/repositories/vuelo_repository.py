import os
from datetime import date
from typing import List, Optional
from dotenv import load_dotenv
from app.domain.vuelo import Vuelo, BloqueoVuelo


def _verificar_disponibilidad_gds(valor_control: str = "", destino: str = "") -> None:
    load_dotenv(override=True)
    falla_env = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() == "true"
    if (
        falla_env
        or valor_control.upper() in {"503", "VL-503"}
        or destino.upper() == "503"
    ):
        raise RuntimeError("Fallo de conexión con el proveedor externo AEX-01 (GDS Aerolíneas)")


class VueloRepository:
    def __init__(self):
        self._vuelos: List[Vuelo] = []
        self._bloqueos: List[BloqueoVuelo] = []
        self._consecutivo_bloqueo: int = 15001
        self._seed()

    def _seed(self):
        self._vuelos = [
            Vuelo(
                id_vuelo="VL-101",
                aerolinea="Avianca",
                numero_vuelo="AV8520",
                origen="BOG",
                destino="CTG",
                fecha_salida=date(2026, 12, 15),
                hora_salida="07:30",
                hora_llegada="09:00",
                duracion="1h 30m",
                puestos_disponibles=12,
                precio_base=320000.0,
                moneda="COP",
            ),
            Vuelo(
                id_vuelo="VL-102",
                aerolinea="LATAM Airlines",
                numero_vuelo="LA4110",
                origen="BOG",
                destino="CTG",
                fecha_salida=date(2026, 12, 15),
                hora_salida="14:15",
                hora_llegada="15:45",
                duracion="1h 30m",
                puestos_disponibles=6,
                precio_base=295000.0,
                moneda="COP",
            ),
            Vuelo(
                id_vuelo="VL-103",
                aerolinea="Copa Airlines",
                numero_vuelo="CM302",
                origen="BOG",
                destino="MIA",
                fecha_salida=date(2026, 12, 20),
                hora_salida="10:00",
                hora_llegada="14:40",
                duracion="4h 40m",
                puestos_disponibles=8,
                precio_base=1450000.0,
                moneda="COP",
            ),
            Vuelo(
                id_vuelo="VL-104",
                aerolinea="Iberia",
                numero_vuelo="IB6588",
                origen="BOG",
                destino="MAD",
                fecha_salida=date(2026, 12, 22),
                hora_salida="18:10",
                hora_llegada="10:30",
                duracion="10h 20m",
                puestos_disponibles=0,
                precio_base=3100000.0,
                moneda="COP",
            ),
        ]

    # HU-011: Buscar vuelos disponibles en AEX-01
    def buscar_vuelos(
        self, origen: str, destino: str, fecha_salida: date, pasajeros: int
    ) -> List[Vuelo]:
        _verificar_disponibilidad_gds(origen, destino)
        return [
            v for v in self._vuelos
            if v.activo
            and v.origen == origen
            and v.destino == destino
            and v.fecha_salida == fecha_salida
            and v.puestos_disponibles >= pasajeros
        ]

    # HU-013 y HU-015: Obtener vuelo por ID
    def obtener_por_id(self, id_vuelo: str) -> Optional[Vuelo]:
        _verificar_disponibilidad_gds(id_vuelo)
        return next(
            (v for v in self._vuelos if v.id_vuelo == id_vuelo.strip().upper() and v.activo),
            None,
        )

    # HU-015: Registrar bloqueo temporal y descontar cupos disponibles en AEX-01
    def crear_bloqueo(
        self,
        vuelo: Vuelo,
        cantidad_puestos: int,
        tiempo_bloqueo_minutos: int = 20,
    ) -> BloqueoVuelo:
        _verificar_disponibilidad_gds(vuelo.id_vuelo)
        vuelo.puestos_disponibles -= cantidad_puestos
        nuevo_bloqueo = BloqueoVuelo(
            id_bloqueo=f"BLK-{self._consecutivo_bloqueo}",
            id_vuelo=vuelo.id_vuelo,
            numero_vuelo=vuelo.numero_vuelo,
            cantidad_puestos=cantidad_puestos,
            puestos_restantes_vuelo=vuelo.puestos_disponibles,
            tiempo_bloqueo_minutos=tiempo_bloqueo_minutos,
        )
        self._bloqueos.append(nuevo_bloqueo)
        self._consecutivo_bloqueo += 1
        return nuevo_bloqueo


vuelo_repository = VueloRepository()