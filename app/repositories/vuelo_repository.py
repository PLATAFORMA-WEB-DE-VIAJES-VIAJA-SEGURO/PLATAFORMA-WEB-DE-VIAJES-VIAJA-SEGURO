import os
from datetime import date
from typing import List, Optional
from dotenv import load_dotenv
from app.domain.vuelo import Vuelo


def _verificar_disponibilidad_gds(origen: str = "", destino: str = "") -> None:
    load_dotenv(override=True)
    falla_env = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() == "true"
    if falla_env or origen == "503" or destino == "503":
        raise RuntimeError("Fallo de conexión con el proveedor externo AEX-01 (GDS Aerolíneas)")


class VueloRepository:
    def __init__(self):
        self._vuelos: List[Vuelo] = []
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
        ]

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

    def obtener_por_id(self, id_vuelo: str) -> Optional[Vuelo]:
        _verificar_disponibilidad_gds()
        return next(
            (v for v in self._vuelos if v.id_vuelo == id_vuelo and v.activo),
            None,
        )


vuelo_repository = VueloRepository()