from datetime import date
from typing import Optional
from app.domain.hotel import (
    MUNICIPIOS_HOTEL_VALIDOS,
    CATEGORIAS_HOTEL_VALIDAS,
    HotelItemOut,
    BusquedaHotelesOut,
)
from app.repositories.hotel_repository import HotelRepository


class ErrorParametrosHotel(Exception):
    pass


class ErrorReglaNegocioHotel(Exception):
    pass


class HotelService:
    def __init__(self, repo: HotelRepository):
        self.repo = repo

    # HU-017: Buscar hoteles (RN-17)
    def buscar_hoteles(
        self,
        ciudad: str,
        fecha_entrada: date,
        fecha_salida: date,
        huespedes: int,
        categoria: Optional[str] = None,
    ) -> BusquedaHotelesOut:
        ciudad_norm = ciudad.strip().upper()
        categoria_norm = categoria.strip().upper() if categoria else None

        if ciudad_norm != "503" and ciudad_norm not in MUNICIPIOS_HOTEL_VALIDOS:
            raise ErrorParametrosHotel(
                "El código de ciudad/municipio no es válido en el catálogo PAR-03"
            )
        if categoria_norm and categoria_norm not in CATEGORIAS_HOTEL_VALIDAS:
            raise ErrorParametrosHotel(
                "La categoría hotelera no es válida en el catálogo PAR-08"
            )
        if fecha_entrada < date.today():
            raise ErrorParametrosHotel(
                "La fecha de entrada no puede ser anterior a la fecha actual"
            )
        if fecha_salida <= fecha_entrada:
            raise ErrorParametrosHotel(
                "La fecha de salida debe ser al menos un día posterior a la fecha de entrada"
            )

        resultados = self.repo.buscar_hoteles(
            municipio=ciudad_norm,
            huespedes=huespedes,
            categoria=categoria_norm,
        )

        # RN-17: Si no hay disponibilidad hotelera para los criterios solicitados
        if not resultados:
            raise ErrorReglaNegocioHotel(
                "No se encontraron hoteles disponibles para el destino, fechas y huéspedes solicitados"
            )

        return BusquedaHotelesOut(
            mensaje="Hoteles disponibles consultados exitosamente",
            data=[HotelItemOut(**h.to_response()) for h in resultados],
            success=True,
        )
    