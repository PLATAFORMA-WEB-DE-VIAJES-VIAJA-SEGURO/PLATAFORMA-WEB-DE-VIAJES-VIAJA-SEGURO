import os
from datetime import date
from typing import List, Optional
from dotenv import load_dotenv
from app.domain.hotel import Hotel, RoomLock


def _check_hotel_availability(control_value: str = "") -> None:
    load_dotenv(override=True)
    simulate_failure = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() == "true"
    if simulate_failure or control_value.strip().upper() in {"503", "HT-503"}:
        raise RuntimeError("Fallo de conexión con el proveedor externo AEX-02 (Servicio de oferta hotelera)")


class HotelRepository:
    def __init__(self):
        self._hotels: List[Hotel] = []
        self._locks: List[RoomLock] = []
        self._seed()

    def _seed(self):
        self._hotels = [
            Hotel(
                hotel_id="HT-201",
                name="Hotel Caribe Histórico",
                municipality="CTG",
                category="5_ESTRELLAS",
                address="Cra. 1 # 2-87, Bocagrande",
                rating=4.8,
                available_rooms=10,
                min_price_per_night=450000.0,
                currency="COP",
            ),
            Hotel(
                hotel_id="HT-202",
                name="Hotel Muralla Boutique",
                municipality="CTG",
                category="BOUTIQUE",
                address="Calle de la Factoría # 36-57",
                rating=4.7,
                available_rooms=4,
                min_price_per_night=380000.0,
                currency="COP",
            ),
            Hotel(
                hotel_id="HT-203",
                name="Hotel Capital Ejecutivo",
                municipality="BOG",
                category="4_ESTRELLAS",
                address="Av. Calle 26 # 69-76",
                rating=4.5,
                available_rooms=15,
                min_price_per_night=290000.0,
                currency="COP",
            ),
            Hotel(
                hotel_id="HT-204",
                name="Hotel Costa Sol",
                municipality="MIA",
                category="4_ESTRELLAS",
                address="1200 Ocean Drive, Miami Beach",
                rating=4.6,
                available_rooms=0,
                min_price_per_night=680000.0,
                currency="COP",
            ),
        ]

    # HU-017: Buscar hoteles disponibles en AEX-02
    def search_hotels(
        self,
        municipality: str,
        guests: int,
        category: Optional[str] = None,
    ) -> List[Hotel]:
        _check_hotel_availability(municipality)
        required_rooms = (guests + 1) // 2
        return [
            hotel for hotel in self._hotels
            if hotel.active
            and hotel.municipality == municipality
            and hotel.available_rooms >= required_rooms
            and (category is None or hotel.category == category)
        ]

    # HU-019 y HU-021: Obtener hotel por ID
    def get_by_id(self, hotel_id: str) -> Optional[Hotel]:
        _check_hotel_availability(hotel_id)
        return next(
            (hotel for hotel in self._hotels if hotel.hotel_id == hotel_id.strip().upper() and hotel.active),
            None,
        )

    # HU-021: Registrar bloqueo temporal de habitación en AEX-02
    def register_lock(
        self,
        hotel: Hotel,
        room_type: str,
        check_in_date: date,
        check_out_date: date,
        nights: int,
        room_count: int,
        guests: int,
        user_id: int,
        retained_total: float,
        lock_minutes: int,
    ) -> RoomLock:
        _check_hotel_availability(hotel.hotel_id)
        hotel.available_rooms -= room_count
        sequence = 500 + len(self._locks) + 1
        lock = RoomLock(
            lock_code=f"BLQ-HT-{sequence}",
            hotel=hotel,
            room_type=room_type,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            nights=nights,
            room_count=room_count,
            guests=guests,
            user_id=user_id,
            retained_total=retained_total,
            lock_minutes=lock_minutes,
        )
        self._locks.append(lock)
        return lock


hotel_repository = HotelRepository()
