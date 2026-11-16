import os
from typing import List, Optional
from dotenv import load_dotenv
from app.domain.hotel import Hotel


def _verificar_disponibilidad_hoteles(valor_control: str = "") -> None:
    load_dotenv(override=True)
    falla_env = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() == "true"
    if falla_env or valor_control.strip().upper() in {"503", "HT-503"}:
        raise RuntimeError("Fallo de conexión con el proveedor externo AEX-02 (Servicio de oferta hotelera)")


class HotelRepository:
    def __init__(self):
        self._hoteles: List[Hotel] = []
        self._seed()

    def _seed(self):
        self._hoteles = [
            Hotel(
                id_hotel="HT-201",
                nombre="Hotel Caribe Histórico",
                municipio="CTG",
                categoria="5_ESTRELLAS",
                direccion="Cra. 1 # 2-87, Bocagrande",
                calificacion=4.8,
                habitaciones_disponibles=10,
                precio_minimo_noche=450000.0,
                moneda="COP",
            ),
            Hotel(
                id_hotel="HT-202",
                nombre="Hotel Muralla Boutique",
                municipio="CTG",
                categoria="BOUTIQUE",
                direccion="Calle de la Factoría # 36-57",
                calificacion=4.7,
                habitaciones_disponibles=4,
                precio_minimo_noche=380000.0,
                moneda="COP",
            ),
            Hotel(
                id_hotel="HT-203",
                nombre="Hotel Capital Ejecutivo",
                municipio="BOG",
                categoria="4_ESTRELLAS",
                direccion="Av. Calle 26 # 69-76",
                calificacion=4.5,
                habitaciones_disponibles=15,
                precio_minimo_noche=290000.0,
                moneda="COP",
            ),
            Hotel(
                id_hotel="HT-204",
                nombre="Hotel Costa Sol",
                municipio="MIA",
                categoria="4_ESTRELLAS",
                direccion="1200 Ocean Drive, Miami Beach",
                calificacion=4.6,
                habitaciones_disponibles=0,
                precio_minimo_noche=680000.0,
                moneda="COP",
            ),
        ]

    # HU-017: Buscar hoteles disponibles en AEX-02
    def buscar_hoteles(
        self,
        municipio: str,
        huespedes: int,
        categoria: Optional[str] = None,
    ) -> List[Hotel]:
        _verificar_disponibilidad_hoteles(municipio)
        habitaciones_necesarias = (huespedes + 1) // 2
        return [
            h for h in self._hoteles
            if h.activo
            and h.municipio == municipio
            and h.habitaciones_disponibles >= habitaciones_necesarias
            and (categoria is None or h.categoria == categoria)
        ]

    # HU-019: Obtener hotel por ID
    def obtener_por_id(self, id_hotel: str) -> Optional[Hotel]:
        _verificar_disponibilidad_hoteles(id_hotel)
        return next(
            (h for h in self._hoteles if h.id_hotel == id_hotel.strip().upper() and h.activo),
            None,
        )


hotel_repository = HotelRepository()