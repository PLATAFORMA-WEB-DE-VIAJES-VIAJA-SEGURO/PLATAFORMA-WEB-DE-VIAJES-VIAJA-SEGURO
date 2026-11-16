from datetime import date
from typing import List, Optional
from pydantic import BaseModel

# Catálogos transversales (MOD-03 / AIN-03: PAR-03, PAR-08, PAR-09, PAR-07)
MUNICIPIOS_HOTEL_VALIDOS = {"BOG", "MDE", "CLO", "BGA", "CTG", "MIA", "MAD", "MEX", "PTY"}
CATEGORIAS_HOTEL_VALIDAS = {"1_ESTRELLA", "2_ESTRELLAS", "3_ESTRELLAS", "4_ESTRELLAS", "5_ESTRELLAS", "BOUTIQUE"}
TIPOS_HABITACION_VALIDOS = {"ESTANDAR", "DOBLE", "SUITE", "FAMILIAR"}
MONEDAS_HOTEL_AIN03 = {"COP", "USD"}


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


# HU-019: Esquemas de consulta de habitaciones y tarifas
class HabitacionTarifaItemOut(BaseModel):
    codigo_habitacion: str
    tipo_habitacion: str
    capacidad_maxima: int
    incluye_desayuno: bool
    politica_cancelacion: str
    tarifa_noche: float
    noches: int
    impuestos: float
    total_estadia: float
    moneda: str


class ConsultaHabitacionesOut(BaseModel):
    mensaje: str
    data: Optional[List[HabitacionTarifaItemOut]] = None
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

    # HU-019: Cálculo de opciones de habitación y tarifas por estadía
    def generar_habitaciones_tarifas(
        self, noches: int, huespedes: int, tipo_habitacion: Optional[str] = None
    ) -> List[dict]:
        catalogo_habitaciones = [
            {
                "codigo_habitacion": f"{self.id_hotel}-HAB-EST",
                "tipo_habitacion": "ESTANDAR",
                "capacidad_maxima": 2,
                "incluye_desayuno": False,
                "politica_cancelacion": "Cancelación gratuita hasta 48h antes",
                "multiplicador": 1.0,
            },
            {
                "codigo_habitacion": f"{self.id_hotel}-HAB-DOB",
                "tipo_habitacion": "DOBLE",
                "capacidad_maxima": 3,
                "incluye_desayuno": True,
                "politica_cancelacion": "Cancelación gratuita hasta 24h antes",
                "multiplicador": 1.25,
            },
            {
                "codigo_habitacion": f"{self.id_hotel}-HAB-SUI",
                "tipo_habitacion": "SUITE",
                "capacidad_maxima": 4,
                "incluye_desayuno": True,
                "politica_cancelacion": "Reembolsable al 100% hasta el check-in",
                "multiplicador": 1.75,
            },
            {
                "codigo_habitacion": f"{self.id_hotel}-HAB-FAM",
                "tipo_habitacion": "FAMILIAR",
                "capacidad_maxima": 6,
                "incluye_desayuno": True,
                "politica_cancelacion": "Cancelación gratuita hasta 48h antes",
                "multiplicador": 2.1,
            },
        ]

        resultado = []
        for hab in catalogo_habitaciones:
            if tipo_habitacion and hab["tipo_habitacion"] != tipo_habitacion:
                continue
            if hab["capacidad_maxima"] < huespedes:
                continue
            tarifa_noche = round(self.precio_minimo_noche * hab["multiplicador"], 2)
            subtotal = round(tarifa_noche * noches, 2)
            impuestos = round(subtotal * 0.19, 2)
            resultado.append({
                "codigo_habitacion": hab["codigo_habitacion"],
                "tipo_habitacion": hab["tipo_habitacion"],
                "capacidad_maxima": hab["capacidad_maxima"],
                "incluye_desayuno": hab["incluye_desayuno"],
                "politica_cancelacion": hab["politica_cancelacion"],
                "tarifa_noche": tarifa_noche,
                "noches": noches,
                "impuestos": impuestos,
                "total_estadia": round(subtotal + impuestos, 2),
                "moneda": self.moneda,
            })
        return resultado
