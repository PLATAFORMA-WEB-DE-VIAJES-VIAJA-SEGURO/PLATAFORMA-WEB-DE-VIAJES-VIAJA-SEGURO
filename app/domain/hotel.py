from typing import List, Optional
from pydantic import BaseModel

# Catálogos transversales (MOD-03 / AIN-03: PAR-03, PAR-08, PAR-07)
MUNICIPIOS_HOTEL_VALIDOS = {"BOG", "MDE", "CLO", "BGA", "CTG", "MIA", "MAD", "MEX", "PTY"}
CATEGORIAS_HOTEL_VALIDAS = {"1_ESTRELLA", "2_ESTRELLAS", "3_ESTRELLAS", "4_ESTRELLAS", "5_ESTRELLAS", "BOUTIQUE"}


# HU-017: Esquemas de búsqueda de hoteles
class HotelItemOut(BaseModel):
    id_hotel: str
    nombre: str
    municipio: str
    categoria: str
    direccion: str
    calificacion: float
    habitaciones_disponibles: int
    precio_minimo_noche: float
    moneda: str


class BusquedaHotelesOut(BaseModel):
    mensaje: str
    data: Optional[List[HotelItemOut]] = None
    success: bool


# Entidad de dominio: Hotel
class Hotel:
    def __init__(
        self,
        id_hotel: str,
        nombre: str,
        municipio: str,
        categoria: str,
        direccion: str,
        calificacion: float,
        habitaciones_disponibles: int,
        precio_minimo_noche: float,
        moneda: str = "COP",
        activo: bool = True,
    ):
        self.id_hotel = id_hotel
        self.nombre = nombre
        self.municipio = municipio
        self.categoria = categoria
        self.direccion = direccion
        self.calificacion = calificacion
        self.habitaciones_disponibles = habitaciones_disponibles
        self.precio_minimo_noche = precio_minimo_noche
        self.moneda = moneda
        self.activo = activo

    # HU-017: Serialización del hotel
    def to_response(self) -> dict:
        return {
            "id_hotel": self.id_hotel,
            "nombre": self.nombre,
            "municipio": self.municipio,
            "categoria": self.categoria,
            "direccion": self.direccion,
            "calificacion": self.calificacion,
            "habitaciones_disponibles": self.habitaciones_disponibles,
            "precio_minimo_noche": self.precio_minimo_noche,
            "moneda": self.moneda,
        }