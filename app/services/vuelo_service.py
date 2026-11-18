from datetime import date
from typing import Optional
from app.domain.vuelo import (
    VALID_AIRPORTS,
    VALID_CABINS,
    VALID_CURRENCIES_AIN02,
    FlightItemOut,
    FlightSearchOut,
    FlightFareItemOut,
    FlightFaresQueryOut,
    SeatLockCreate,
    SeatLockDataOut,
    SeatLockOut,
)
from app.repositories.vuelo_repository import FlightRepository


class FlightSearchParametersError(Exception):
    pass


class FlightBusinessRuleError(Exception):
    pass


class FlightService:
    def __init__(self, repo: FlightRepository):
        self.repo = repo

    # HU-011: Buscar vuelos (RN-11)
    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        passengers: int,
        return_date: Optional[date] = None,
    ) -> FlightSearchOut:
        normalized_origin = origin.strip().upper()
        normalized_destination = destination.strip().upper()

        if normalized_origin != "503" and normalized_origin not in VALID_AIRPORTS:
            raise FlightSearchParametersError(
                "El código IATA de origen o destino no es válido"
            )
        if normalized_destination != "503" and normalized_destination not in VALID_AIRPORTS:
            raise FlightSearchParametersError(
                "El código IATA de origen o destino no es válido"
            )
        if normalized_origin == normalized_destination:
            raise FlightSearchParametersError(
                "La ciudad de origen y destino no pueden ser iguales"
            )
        if departure_date < date.today():
            raise FlightSearchParametersError(
                "La fecha de salida no puede ser anterior a la fecha actual"
            )
        if return_date and return_date < departure_date:
            raise FlightSearchParametersError(
                "La fecha de regreso no puede ser anterior a la fecha de salida"
            )

        results = self.repo.search_flights(
            origin=normalized_origin,
            destination=normalized_destination,
            departure_date=departure_date,
            passengers=passengers,
        )

        if not results:
            raise FlightBusinessRuleError(
                "No se encontraron vuelos disponibles para la ruta, fecha y cantidad de pasajeros solicitados"
            )

        return FlightSearchOut(
            mensaje="Vuelos disponibles consultados exitosamente",
            data=[FlightItemOut(**flight.to_response()) for flight in results],
            success=True,
        )

    # HU-013: Consultar tarifas del vuelo (RN-13)
    def get_flight_fares(
        self,
        flight_id: str,
        cabin: Optional[str] = None,
        checked_baggage: int = 0,
    ) -> FlightFaresQueryOut:
        normalized_cabin = cabin.strip().upper() if cabin else None
        if normalized_cabin and normalized_cabin not in VALID_CABINS:
            raise FlightSearchParametersError(
                "La cabina solicitada no es válida (use ECONOMICA, EJECUTIVA o PRIMERA)"
            )

        flight = self.repo.get_by_id(flight_id)
        if not flight:
            raise FlightBusinessRuleError(
                "El vuelo solicitado no existe o no cuenta con tarifas vigentes"
            )

        if flight.currency not in VALID_CURRENCIES_AIN02:
            raise FlightBusinessRuleError(
                "La moneda configurada para la tarifa no se encuentra activa en AIN-02"
            )

        if flight.available_seats <= 0:
            raise FlightBusinessRuleError(
                "El vuelo ya no dispone de cupos para cotizar tarifas vigentes"
            )

        fares = flight.generate_fare_families(
            cabin=normalized_cabin,
            checked_baggage=checked_baggage,
        )

        return FlightFaresQueryOut(
            mensaje="Tarifas del vuelo consultadas exitosamente",
            data=[FlightFareItemOut(**fare) for fare in fares],
            success=True,
        )

    # HU-015: Bloquear puestos temporalmente (RN-15)
    def lock_flight_seats(
        self, flight_id: str, data: SeatLockCreate
    ) -> SeatLockOut:
        flight = self.repo.get_by_id(flight_id)
        if not flight:
            raise FlightBusinessRuleError(
                "El vuelo solicitado no existe o ya no se encuentra activo"
            )

        if flight.available_seats < data.seat_count:
            raise FlightBusinessRuleError(
                "No hay suficientes puestos disponibles en el vuelo para realizar el bloqueo solicitado"
            )

        lock = self.repo.create_lock(
            flight=flight,
            seat_count=data.seat_count,
            lock_time_minutes=data.lock_time_minutes,
        )

        return SeatLockOut(
            mensaje="Puestos bloqueados temporalmente exitosamente",
            data=SeatLockDataOut(**lock.to_response()),
            success=True,
        )
