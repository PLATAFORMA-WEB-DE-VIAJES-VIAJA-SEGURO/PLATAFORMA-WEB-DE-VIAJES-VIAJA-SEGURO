from datetime import date
from typing import Optional
from app.domain.hotel import (
    VALID_HOTEL_MUNICIPALITIES,
    VALID_HOTEL_CATEGORIES,
    VALID_ROOM_TYPES,
    VALID_HOTEL_CURRENCIES_AIN03,
    HotelItemOut,
    HotelSearchOut,
    RoomRateItemOut,
    RoomRatesQueryOut,
    RoomLockIn,
    RoomLockDataOut,
    RoomLockOut,
)
from app.repositories.hotel_repository import HotelRepository


class HotelParametersError(Exception):
    pass


class HotelBusinessRuleError(Exception):
    pass


class HotelService:
    def __init__(self, repo: HotelRepository):
        self.repo = repo

    # HU-017: Buscar hoteles (RN-17)
    def search_hotels(
        self,
        city: str,
        check_in_date: date,
        check_out_date: date,
        guests: int,
        category: Optional[str] = None,
    ) -> HotelSearchOut:
        normalized_city = city.strip().upper()
        normalized_category = category.strip().upper() if category else None

        if normalized_city != "503" and normalized_city not in VALID_HOTEL_MUNICIPALITIES:
            raise HotelParametersError(
                "El código de ciudad/municipio no es válido en el catálogo PAR-03"
            )
        if normalized_category and normalized_category not in VALID_HOTEL_CATEGORIES:
            raise HotelParametersError(
                "La categoría hotelera no es válida en el catálogo PAR-08"
            )
        if check_in_date < date.today():
            raise HotelParametersError(
                "La fecha de entrada no puede ser anterior a la fecha actual"
            )
        if check_out_date <= check_in_date:
            raise HotelParametersError(
                "La fecha de salida debe ser al menos un día posterior a la fecha de entrada"
            )

        results = self.repo.search_hotels(
            municipality=normalized_city,
            guests=guests,
            category=normalized_category,
        )

        if not results:
            raise HotelBusinessRuleError(
                "No se encontraron hoteles disponibles para el destino, fechas y huéspedes solicitados"
            )

        return HotelSearchOut(
            mensaje="Hoteles disponibles consultados exitosamente",
            data=[HotelItemOut(**hotel.to_response()) for hotel in results],
            success=True,
        )

    # HU-019: Consultar habitaciones y tarifas (RN-19)
    def get_rooms_and_rates(
        self,
        hotel_id: str,
        check_in_date: date,
        check_out_date: date,
        guests: int = 2,
        room_type: Optional[str] = None,
    ) -> RoomRatesQueryOut:
        normalized_room_type = room_type.strip().upper() if room_type else None

        if normalized_room_type and normalized_room_type not in VALID_ROOM_TYPES:
            raise HotelParametersError(
                "El tipo de habitación no es válido en el catálogo PAR-09 (ESTANDAR, DOBLE, SUITE, FAMILIAR)"
            )
        if check_in_date < date.today():
            raise HotelParametersError(
                "La fecha de entrada no puede ser anterior a la fecha actual"
            )
        if check_out_date <= check_in_date:
            raise HotelParametersError(
                "La fecha de salida debe ser posterior a la fecha de entrada"
            )

        hotel = self.repo.get_by_id(hotel_id)
        if not hotel:
            raise HotelBusinessRuleError(
                "El hotel solicitado no existe o no cuenta con habitaciones activas"
            )

        if hotel.currency not in VALID_HOTEL_CURRENCIES_AIN03:
            raise HotelBusinessRuleError(
                "La moneda configurada para el hotel no está habilitada en AIN-03"
            )

        if hotel.available_rooms <= 0:
            raise HotelBusinessRuleError(
                "El hotel no dispone de habitaciones libres para el rango de fechas solicitado"
            )

        nights = (check_out_date - check_in_date).days
        rooms = hotel.generate_rooms_and_rates(
            nights=nights,
            guests=guests,
            room_type=normalized_room_type,
        )

        if not rooms:
            raise HotelBusinessRuleError(
                "Ninguna habitación disponible cumple con la capacidad máxima de huéspedes solicitada"
            )

        return RoomRatesQueryOut(
            mensaje="Habitaciones y tarifas consultadas exitosamente",
            data=[RoomRateItemOut(**room) for room in rooms],
            success=True,
        )

    # HU-021: Bloquear habitación temporalmente (RN-21)
    def lock_room(self, payload: RoomLockIn) -> RoomLockOut:
        normalized_room_type = payload.room_type.strip().upper()
        max_capacities = {
            "ESTANDAR": 2,
            "DOBLE": 3,
            "SUITE": 4,
            "FAMILIAR": 6,
        }

        if normalized_room_type not in VALID_ROOM_TYPES:
            raise HotelParametersError(
                "El tipo de habitación no es válido en el catálogo PAR-09 (ESTANDAR, DOBLE, SUITE, FAMILIAR)"
            )
        if payload.check_in_date < date.today():
            raise HotelParametersError(
                "La fecha de entrada no puede ser anterior a la fecha actual"
            )
        if payload.check_out_date <= payload.check_in_date:
            raise HotelParametersError(
                "La fecha de salida debe ser al menos un día posterior a la fecha de entrada"
            )

        total_capacity = max_capacities[normalized_room_type] * payload.room_count
        if payload.guests > total_capacity:
            raise HotelParametersError(
                "La cantidad de huéspedes supera la capacidad máxima permitida para las habitaciones solicitadas"
            )

        hotel = self.repo.get_by_id(payload.hotel_id)
        if not hotel:
            raise HotelBusinessRuleError(
                "El hotel seleccionado no existe o no se encuentra activo"
            )

        if hotel.currency not in VALID_HOTEL_CURRENCIES_AIN03:
            raise HotelBusinessRuleError(
                "La moneda configurada para el hotel no está habilitada en AIN-03"
            )

        # RN-21: Validar disponibilidad real antes de ejecutar bloqueo temporal
        if hotel.available_rooms < payload.room_count:
            raise HotelBusinessRuleError(
                "No hay suficientes habitaciones disponibles en el hotel para realizar el bloqueo temporal"
            )

        nights = (payload.check_out_date - payload.check_in_date).days
        retained_total = hotel.calculate_lock_total(
            room_type=normalized_room_type,
            nights=nights,
            room_count=payload.room_count,
        )

        lock = self.repo.register_lock(
            hotel=hotel,
            room_type=normalized_room_type,
            check_in_date=payload.check_in_date,
            check_out_date=payload.check_out_date,
            nights=nights,
            room_count=payload.room_count,
            guests=payload.guests,
            user_id=payload.user_id,
            retained_total=retained_total,
            lock_minutes=payload.lock_minutes,
        )

        return RoomLockOut(
            mensaje="Habitación bloqueada temporalmente de forma exitosa",
            data=RoomLockDataOut(**lock.to_response()),
            success=True,
        )
