from datetime import date, datetime, timedelta, timezone
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

# Catálogos transversales (MOD-03 / AIN-03: PAR-03, PAR-08, PAR-09, PAR-07)
VALID_HOTEL_MUNICIPALITIES = {"BOG", "MDE", "CLO", "BGA", "CTG", "MIA", "MAD", "MEX", "PTY"}
VALID_HOTEL_CATEGORIES = {"1_ESTRELLA", "2_ESTRELLAS", "3_ESTRELLAS", "4_ESTRELLAS", "5_ESTRELLAS", "BOUTIQUE"}
VALID_ROOM_TYPES = {"ESTANDAR", "DOBLE", "SUITE", "FAMILIAR"}
VALID_HOTEL_CURRENCIES_AIN03 = {"COP", "USD"}


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


class HotelSearchOut(BaseModel):
    mensaje: str
    data: Optional[List[HotelItemOut]] = None
    success: bool


# HU-019: Esquemas de consulta de habitaciones y tarifas
class RoomRateItemOut(BaseModel):
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


class RoomRatesQueryOut(BaseModel):
    mensaje: str
    data: Optional[List[RoomRateItemOut]] = None
    success: bool


# HU-021: Esquemas de bloqueo temporal de habitación
class RoomLockIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    hotel_id: str = Field(..., alias="id_hotel", min_length=3, max_length=20)
    room_type: str = Field(..., alias="tipo_habitacion", min_length=3, max_length=20)
    check_in_date: date = Field(..., alias="fecha_entrada")
    check_out_date: date = Field(..., alias="fecha_salida")
    room_count: int = Field(default=1, alias="cantidad_habitaciones", ge=1, le=5)
    guests: int = Field(default=2, alias="huespedes", ge=1, le=10)
    user_id: int = Field(..., alias="id_usuario", gt=0)
    lock_minutes: int = Field(default=15, alias="minutos_bloqueo", ge=5, le=30)


class RoomLockDataOut(BaseModel):
    codigo_bloqueo: str
    id_hotel: str
    nombre_hotel: str
    tipo_habitacion: str
    fecha_entrada: date
    fecha_salida: date
    noches: int
    cantidad_habitaciones: int
    huespedes: int
    id_usuario: int
    estado: str
    total_retenido: float
    moneda: str
    expira_en: str


class RoomLockOut(BaseModel):
    mensaje: str
    data: Optional[RoomLockDataOut] = None
    success: bool


# Entidad de dominio: Hotel
class Hotel:
    def __init__(
        self,
        hotel_id: str,
        name: str,
        municipality: str,
        category: str,
        address: str,
        rating: float,
        available_rooms: int,
        min_price_per_night: float,
        currency: str = "COP",
        active: bool = True,
    ):
        self.hotel_id = hotel_id
        self.name = name
        self.municipality = municipality
        self.category = category
        self.address = address
        self.rating = rating
        self.available_rooms = available_rooms
        self.min_price_per_night = min_price_per_night
        self.currency = currency
        self.active = active

    # HU-017: Serialización del hotel
    def to_response(self) -> dict:
        return {
            "id_hotel": self.hotel_id,
            "nombre": self.name,
            "municipio": self.municipality,
            "categoria": self.category,
            "direccion": self.address,
            "calificacion": self.rating,
            "habitaciones_disponibles": self.available_rooms,
            "precio_minimo_noche": self.min_price_per_night,
            "moneda": self.currency,
        }

    # HU-019: Cálculo de opciones de habitación y tarifas por estadía
    def generate_rooms_and_rates(
        self, nights: int, guests: int, room_type: Optional[str] = None
    ) -> List[dict]:
        room_catalog = [
            {
                "codigo_habitacion": f"{self.hotel_id}-HAB-EST",
                "tipo_habitacion": "ESTANDAR",
                "capacidad_maxima": 2,
                "incluye_desayuno": False,
                "politica_cancelacion": "Cancelación gratuita hasta 48h antes",
                "multiplier": 1.0,
            },
            {
                "codigo_habitacion": f"{self.hotel_id}-HAB-DOB",
                "tipo_habitacion": "DOBLE",
                "capacidad_maxima": 3,
                "incluye_desayuno": True,
                "politica_cancelacion": "Cancelación gratuita hasta 24h antes",
                "multiplier": 1.25,
            },
            {
                "codigo_habitacion": f"{self.hotel_id}-HAB-SUI",
                "tipo_habitacion": "SUITE",
                "capacidad_maxima": 4,
                "incluye_desayuno": True,
                "politica_cancelacion": "Reembolsable al 100% hasta el check-in",
                "multiplier": 1.75,
            },
            {
                "codigo_habitacion": f"{self.hotel_id}-HAB-FAM",
                "tipo_habitacion": "FAMILIAR",
                "capacidad_maxima": 6,
                "incluye_desayuno": True,
                "politica_cancelacion": "Cancelación gratuita hasta 48h antes",
                "multiplier": 2.1,
            },
        ]

        result = []
        for room in room_catalog:
            if room_type and room["tipo_habitacion"] != room_type:
                continue
            if room["capacidad_maxima"] < guests:
                continue
            rate_per_night = round(self.min_price_per_night * room["multiplier"], 2)
            subtotal = round(rate_per_night * nights, 2)
            taxes = round(subtotal * 0.19, 2)
            result.append({
                "codigo_habitacion": room["codigo_habitacion"],
                "tipo_habitacion": room["tipo_habitacion"],
                "capacidad_maxima": room["capacidad_maxima"],
                "incluye_desayuno": room["incluye_desayuno"],
                "politica_cancelacion": room["politica_cancelacion"],
                "tarifa_noche": rate_per_night,
                "noches": nights,
                "impuestos": taxes,
                "total_estadia": round(subtotal + taxes, 2),
                "moneda": self.currency,
            })
        return result

    # HU-021: Cálculo de total retenido para bloqueo temporal
    def calculate_lock_total(self, room_type: str, nights: int, room_count: int) -> float:
        multipliers = {
            "ESTANDAR": 1.0,
            "DOBLE": 1.25,
            "SUITE": 1.75,
            "FAMILIAR": 2.1,
        }
        rate_per_night = self.min_price_per_night * multipliers[room_type]
        subtotal = rate_per_night * nights * room_count
        return round(subtotal * 1.19, 2)


# HU-021: Entidad de dominio para retención temporal de habitación
class RoomLock:
    def __init__(
        self,
        lock_code: str,
        hotel: Hotel,
        room_type: str,
        check_in_date: date,
        check_out_date: date,
        nights: int,
        room_count: int,
        guests: int,
        user_id: int,
        retained_total: float,
        lock_minutes: int = 15,
    ):
        self.lock_code = lock_code
        self.hotel_id = hotel.hotel_id
        self.hotel_name = hotel.name
        self.room_type = room_type
        self.check_in_date = check_in_date
        self.check_out_date = check_out_date
        self.nights = nights
        self.room_count = room_count
        self.guests = guests
        self.user_id = user_id
        self.status = "BLOQUEADA_TEMPORALMENTE"
        self.retained_total = retained_total
        self.currency = hotel.currency
        self.expires_at = (
            datetime.now(timezone.utc) + timedelta(minutes=lock_minutes)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

    def to_response(self) -> dict:
        return {
            "codigo_bloqueo": self.lock_code,
            "id_hotel": self.hotel_id,
            "nombre_hotel": self.hotel_name,
            "tipo_habitacion": self.room_type,
            "fecha_entrada": self.check_in_date,
            "fecha_salida": self.check_out_date,
            "noches": self.nights,
            "cantidad_habitaciones": self.room_count,
            "huespedes": self.guests,
            "id_usuario": self.user_id,
            "estado": self.status,
            "total_retenido": self.retained_total,
            "moneda": self.currency,
            "expira_en": self.expires_at,
        }
