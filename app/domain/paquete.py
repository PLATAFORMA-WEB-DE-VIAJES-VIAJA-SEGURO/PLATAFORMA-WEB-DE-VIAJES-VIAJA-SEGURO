from datetime import date
from typing import List, Optional
from pydantic import BaseModel

# Catálogos transversales (MOD-04 / AIN-04: PAR-02, PAR-03, PAR-10, PAR-07)
VALID_PACKAGE_COUNTRIES = {"CO", "US", "ES", "MX", "PA"}
VALID_PACKAGE_MUNICIPALITIES = {"BOG", "MDE", "CLO", "BGA", "CTG", "MIA", "MAD", "MEX", "PTY"}
VALID_PACKAGE_TYPES = {"TODO_INCLUIDO", "AVENTURA", "CULTURAL", "PLAYA", "FAMILIAR"}
VALID_ACTIVITY_CATEGORIES = {"TOUR_GUIADO", "AVENTURA", "GASTRONOMIA", "ACUATICA", "CULTURAL"}
VALID_PACKAGE_CURRENCIES_AIN04 = {"COP", "USD"}


# HU-023: Esquemas de consulta de destinos
class DestinationItemOut(BaseModel):
    id_destino: str
    nombre: str
    pais: str
    municipio: str
    tipo_paquete: str
    descripcion: str
    temporada_recomendada: str
    precio_desde: float
    moneda: str


class DestinationsQueryOut(BaseModel):
    mensaje: str
    data: Optional[List[DestinationItemOut]] = None
    success: bool


# HU-026: Esquemas de consulta de actividades del destino
class ActivityItemOut(BaseModel):
    id_actividad: str
    id_destino: str
    nombre: str
    categoria: str
    duracion_horas: int
    punto_encuentro: str
    incluye_guia: bool
    cupos_diarios: int
    precio_persona: float
    moneda: str


class ActivitiesQueryOut(BaseModel):
    mensaje: str
    data: Optional[List[ActivityItemOut]] = None
    success: bool


# HU-027: Esquemas de verificación de cupo y tarifa de actividad
class ActivityAvailabilityDataOut(BaseModel):
    id_actividad: str
    nombre_actividad: str
    id_destino: str
    fecha_actividad: date
    cantidad_personas: int
    cupos_disponibles: int
    tarifa_unitaria: float
    impuestos: float
    total_actividad: float
    moneda: str
    disponible: bool


class ActivityAvailabilityOut(BaseModel):
    mensaje: str
    data: Optional[ActivityAvailabilityDataOut] = None
    success: bool


# Entidad de dominio: Destino
class Destination:
    def __init__(
        self,
        destination_id: str,
        name: str,
        country: str,
        municipality: str,
        package_type: str,
        description: str,
        recommended_season: str,
        price_from: float,
        currency: str = "COP",
        active: bool = True,
    ):
        self.destination_id = destination_id
        self.name = name
        self.country = country
        self.municipality = municipality
        self.package_type = package_type
        self.description = description
        self.recommended_season = recommended_season
        self.price_from = price_from
        self.currency = currency
        self.active = active

    # HU-023: Serialización del destino
    def to_response(self) -> dict:
        return {
            "id_destino": self.destination_id,
            "nombre": self.name,
            "pais": self.country,
            "municipio": self.municipality,
            "tipo_paquete": self.package_type,
            "descripcion": self.description,
            "temporada_recomendada": self.recommended_season,
            "precio_desde": self.price_from,
            "moneda": self.currency,
        }


# Entidad de dominio: Actividad Turística (AEX-03)
class Activity:
    def __init__(
        self,
        activity_id: str,
        destination_id: str,
        name: str,
        category: str,
        duration_hours: int,
        meeting_point: str,
        includes_guide: bool,
        daily_quota: int,
        price_per_person: float,
        currency: str = "COP",
        active: bool = True,
    ):
        self.activity_id = activity_id
        self.destination_id = destination_id
        self.name = name
        self.category = category
        self.duration_hours = duration_hours
        self.meeting_point = meeting_point
        self.includes_guide = includes_guide
        self.daily_quota = daily_quota
        self.price_per_person = price_per_person
        self.currency = currency
        self.active = active

    # HU-026: Serialización de la actividad
    def to_response(self) -> dict:
        return {
            "id_actividad": self.activity_id,
            "id_destino": self.destination_id,
            "nombre": self.name,
            "categoria": self.category,
            "duracion_horas": self.duration_hours,
            "punto_encuentro": self.meeting_point,
            "incluye_guia": self.includes_guide,
            "cupos_diarios": self.daily_quota,
            "precio_persona": self.price_per_person,
            "moneda": self.currency,
        }

    # HU-027: Cálculo de tarifa consolidada y verificación de aforo
    def calculate_availability_and_fare(self, activity_date: date, people_count: int) -> dict:
        subtotal = round(self.price_per_person * people_count, 2)
        taxes = round(subtotal * 0.19, 2)
        return {
            "id_actividad": self.activity_id,
            "nombre_actividad": self.name,
            "id_destino": self.destination_id,
            "fecha_actividad": activity_date,
            "cantidad_personas": people_count,
            "cupos_disponibles": self.daily_quota,
            "tarifa_unitaria": self.price_per_person,
            "impuestos": taxes,
            "total_actividad": round(subtotal + taxes, 2),
            "moneda": self.currency,
            "disponible": self.daily_quota >= people_count,
        }
