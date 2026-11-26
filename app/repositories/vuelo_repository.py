import os
from datetime import date
from typing import List, Optional
from dotenv import load_dotenv
from app.domain.vuelo import Flight, FlightLock


def _check_gds_availability(control_value: str = "", destination: str = "") -> None:
    load_dotenv(override=True)
    simulate_failure = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() == "true"
    if (
        simulate_failure
        or control_value.upper() in {"503", "VL-503"}
        or destination.upper() == "503"
    ):
        raise RuntimeError("Fallo de conexión con el proveedor externo AEX-01 (GDS Aerolíneas)")


class FlightRepository:
    def __init__(self):
        self._flights: List[Flight] = []
        self._locks: List[FlightLock] = []
        self._lock_sequence: int = 15001
        self._seed()

    def _seed(self):
        self._flights = [
            Flight(
                flight_id="VL-101",
                airline="Avianca",
                flight_number="AV8520",
                origin="BOG",
                destination="CTG",
                departure_date=date(2026, 12, 15),
                departure_time="07:30",
                arrival_time="09:00",
                duration="1h 30m",
                available_seats=12,
                base_price=320000.0,
                currency="COP",
            ),
            Flight(
                flight_id="VL-102",
                airline="LATAM Airlines",
                flight_number="LA4110",
                origin="BOG",
                destination="CTG",
                departure_date=date(2026, 12, 15),
                departure_time="14:15",
                arrival_time="15:45",
                duration="1h 30m",
                available_seats=6,
                base_price=295000.0,
                currency="COP",
            ),
            Flight(
                flight_id="VL-103",
                airline="Copa Airlines",
                flight_number="CM302",
                origin="BOG",
                destination="MIA",
                departure_date=date(2026, 12, 20),
                departure_time="10:00",
                arrival_time="14:40",
                duration="4h 40m",
                available_seats=8,
                base_price=1450000.0,
                currency="COP",
            ),
            Flight(
                flight_id="VL-104",
                airline="Iberia",
                flight_number="IB6588",
                origin="BOG",
                destination="MAD",
                departure_date=date(2026, 12, 22),
                departure_time="18:10",
                arrival_time="10:30",
                duration="10h 20m",
                available_seats=0,
                base_price=3100000.0,
                currency="COP",
            ),
        ]

    # HU-011: Buscar vuelos disponibles en AEX-01
    def search_flights(
        self, origin: str, destination: str, departure_date: date, passengers: int
    ) -> List[Flight]:
        _check_gds_availability(origin, destination)
        return [
            flight for flight in self._flights
            if flight.active
            and flight.origin == origin
            and flight.destination == destination
            and flight.departure_date == departure_date
            and flight.available_seats >= passengers
        ]

    # HU-013 y HU-015: Obtener vuelo por ID
    def get_by_id(self, flight_id: str) -> Optional[Flight]:
        _check_gds_availability(flight_id)
        return next(
            (flight for flight in self._flights if flight.flight_id == flight_id.strip().upper() and flight.active),
            None,
        )

    # HU-015: Registrar bloqueo temporal y descontar cupos disponibles en AEX-01
    def create_lock(
        self,
        flight: Flight,
        seat_count: int,
        lock_time_minutes: int = 20,
    ) -> FlightLock:
        _check_gds_availability(flight.flight_id)
        flight.available_seats -= seat_count
        new_lock = FlightLock(
            lock_id=f"BLK-{self._lock_sequence}",
            flight_id=flight.flight_id,
            flight_number=flight.flight_number,
            seat_count=seat_count,
            remaining_seats=flight.available_seats,
            lock_time_minutes=lock_time_minutes,
        )
        self._locks.append(new_lock)
        self._lock_sequence += 1
        return new_lock


flight_repository = FlightRepository()
