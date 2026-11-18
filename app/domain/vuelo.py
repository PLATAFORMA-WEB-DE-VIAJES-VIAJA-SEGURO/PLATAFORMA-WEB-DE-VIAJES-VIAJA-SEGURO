from datetime import date, datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

# Catálogos y reglas transversales (MOD-02 / AIN-02)
VALID_AIRPORTS = {"BOG", "MDE", "CLO", "BGA", "CTG", "MIA", "MAD", "MEX", "PTY"}
VALID_CABINS = {"ECONOMICA", "EJECUTIVA", "PRIMERA"}
VALID_CURRENCIES_AIN02 = {"COP", "USD"}


# HU-011: Esquemas de búsqueda de vuelos
class FlightItemOut(BaseModel):
    id_vuelo: str
    aerolinea: str
    numero_vuelo: str
    origen: str
    destino: str
    fecha_salida: date
    hora_salida: str
    hora_llegada: str
    duracion: str
    puestos_disponibles: int
    precio_base: float
    moneda: str


class FlightSearchOut(BaseModel):
    mensaje: str
    data: Optional[List[FlightItemOut]] = None
    success: bool


# HU-013: Esquemas de consulta de tarifas del vuelo
class FlightFareItemOut(BaseModel):
    codigo_tarifa: str
    nombre_tarifa: str
    cabina: str
    equipaje_incluido: str
    permite_cambios: bool
    precio_unitario: float
    impuestos: float
    precio_total_pasajero: float
    moneda: str


class FlightFaresQueryOut(BaseModel):
    mensaje: str
    data: Optional[List[FlightFareItemOut]] = None
    success: bool


# HU-015: Esquemas de bloqueo temporal de puestos
class SeatLockCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    seat_count: int = Field(..., alias="cantidad_puestos", ge=1, le=9)
    lock_time_minutes: int = Field(default=20, alias="tiempo_bloqueo_minutos", ge=5, le=20)
    fare_code: Optional[str] = Field(default=None, alias="codigo_tarifa")


class SeatLockDataOut(BaseModel):
    id_bloqueo: str
    id_vuelo: str
    numero_vuelo: str
    cantidad_puestos: int
    puestos_restantes_vuelo: int
    tiempo_bloqueo_minutos: int
    fecha_expiracion: str
    estado: str


class SeatLockOut(BaseModel):
    mensaje: str
    data: Optional[SeatLockDataOut] = None
    success: bool


# Entidad de dominio: Bloqueo de puestos (HU-015)
class FlightLock:
    def __init__(
        self,
        lock_id: str,
        flight_id: str,
        flight_number: str,
        seat_count: int,
        remaining_seats: int,
        lock_time_minutes: int = 20,
    ):
        self.lock_id = lock_id
        self.flight_id = flight_id
        self.flight_number = flight_number
        self.seat_count = seat_count
        self.remaining_seats = remaining_seats
        self.lock_time_minutes = lock_time_minutes
        self.expiration_date = (
            datetime.utcnow() + timedelta(minutes=lock_time_minutes)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.status = "ACTIVO"

    def to_response(self) -> dict:
        return {
            "id_bloqueo": self.lock_id,
            "id_vuelo": self.flight_id,
            "numero_vuelo": self.flight_number,
            "cantidad_puestos": self.seat_count,
            "puestos_restantes_vuelo": self.remaining_seats,
            "tiempo_bloqueo_minutos": self.lock_time_minutes,
            "fecha_expiracion": self.expiration_date,
            "estado": self.status,
        }


# Entidad de dominio: Vuelo
class Flight:
    def __init__(
        self,
        flight_id: str,
        airline: str,
        flight_number: str,
        origin: str,
        destination: str,
        departure_date: date,
        departure_time: str,
        arrival_time: str,
        duration: str,
        available_seats: int,
        base_price: float,
        currency: str = "COP",
        active: bool = True,
    ):
        self.flight_id = flight_id
        self.airline = airline
        self.flight_number = flight_number
        self.origin = origin
        self.destination = destination
        self.departure_date = departure_date
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.duration = duration
        self.available_seats = available_seats
        self.base_price = base_price
        self.currency = currency
        self.active = active

    # HU-011: Serialización del vuelo
    def to_response(self) -> dict:
        return {
            "id_vuelo": self.flight_id,
            "aerolinea": self.airline,
            "numero_vuelo": self.flight_number,
            "origen": self.origin,
            "destino": self.destination,
            "fecha_salida": self.departure_date,
            "hora_salida": self.departure_time,
            "hora_llegada": self.arrival_time,
            "duracion": self.duration,
            "puestos_disponibles": self.available_seats,
            "precio_base": self.base_price,
            "moneda": self.currency,
        }

    # HU-013: Cálculo de familias tarifarias
    def generate_fare_families(self, cabin: Optional[str] = None, checked_baggage: int = 0) -> List[dict]:
        baggage_fee = checked_baggage * 85000.0
        fare_families = [
            {
                "codigo_tarifa": f"{self.flight_id}-ECO-BASIC",
                "nombre_tarifa": "Económica Básica",
                "cabina": "ECONOMICA",
                "equipaje_incluido": "1 artículo personal" + (f" + {checked_baggage} maleta(s) 23kg" if checked_baggage > 0 else ""),
                "permite_cambios": False,
                "multiplier": 1.0,
            },
            {
                "codigo_tarifa": f"{self.flight_id}-ECO-FLEX",
                "nombre_tarifa": "Económica Flexible",
                "cabina": "ECONOMICA",
                "equipaje_incluido": f"1 equipaje de mano + {max(1, checked_baggage)} maleta(s) 23kg",
                "permite_cambios": True,
                "multiplier": 1.25,
            },
            {
                "codigo_tarifa": f"{self.flight_id}-EJE-PLUS",
                "nombre_tarifa": "Ejecutiva Plus",
                "cabina": "EJECUTIVA",
                "equipaje_incluido": "2 maletas 32kg + sala VIP" + (f" + {checked_baggage} extra" if checked_baggage > 0 else ""),
                "permite_cambios": True,
                "multiplier": 1.85,
            },
            {
                "codigo_tarifa": f"{self.flight_id}-PRI-SUITE",
                "nombre_tarifa": "Primera Clase Suite",
                "cabina": "PRIMERA",
                "equipaje_incluido": "3 maletas 32kg + embarque prioritario",
                "permite_cambios": True,
                "multiplier": 2.6,
            },
        ]

        result = []
        for family in fare_families:
            if cabin and family["cabina"] != cabin:
                continue
            unit_price = round((self.base_price * family["multiplier"]) + baggage_fee, 2)
            taxes = round(unit_price * 0.19, 2)
            result.append({
                "codigo_tarifa": family["codigo_tarifa"],
                "nombre_tarifa": family["nombre_tarifa"],
                "cabina": family["cabina"],
                "equipaje_incluido": family["equipaje_incluido"],
                "permite_cambios": family["permite_cambios"],
                "precio_unitario": unit_price,
                "impuestos": taxes,
                "precio_total_pasajero": round(unit_price + taxes, 2),
                "moneda": self.currency,
            })
        return result
