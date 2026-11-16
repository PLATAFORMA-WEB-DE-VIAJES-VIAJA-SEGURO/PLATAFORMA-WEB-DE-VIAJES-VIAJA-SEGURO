from datetime import date
from typing import Optional
from app.domain.hotel import (
    MUNICIPIOS_HOTEL_VALIDOS,
    CATEGORIAS_HOTEL_VALIDAS,
    TIPOS_HABITACION_VALIDOS,
    MONEDAS_HOTEL_AIN03,
    HotelItemOut,
    BusquedaHotelesOut,
    HabitacionTarifaItemOut,
    ConsultaHabitacionesOut,
    BloqueoHabitacionIn,
    BloqueoHabitacionDataOut,
    BloqueoHabitacionOut,
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

        if not resultados:
            raise ErrorReglaNegocioHotel(
                "No se encontraron hoteles disponibles para el destino, fechas y huéspedes solicitados"
            )

        return BusquedaHotelesOut(
            mensaje="Hoteles disponibles consultados exitosamente",
            data=[HotelItemOut(**h.to_response()) for h in resultados],
            success=True,
        )

    # HU-019: Consultar habitaciones y tarifas (RN-19)
    def consultar_habitaciones_tarifas(
        self,
        id_hotel: str,
        fecha_entrada: date,
        fecha_salida: date,
        huespedes: int = 2,
        tipo_habitacion: Optional[str] = None,
    ) -> ConsultaHabitacionesOut:
        tipo_norm = tipo_habitacion.strip().upper() if tipo_habitacion else None

        if tipo_norm and tipo_norm not in TIPOS_HABITACION_VALIDOS:
            raise ErrorParametrosHotel(
                "El tipo de habitación no es válido en el catálogo PAR-09 (ESTANDAR, DOBLE, SUITE, FAMILIAR)"
            )
        if fecha_entrada < date.today():
            raise ErrorParametrosHotel(
                "La fecha de entrada no puede ser anterior a la fecha actual"
            )
        if fecha_salida <= fecha_entrada:
            raise ErrorParametrosHotel(
                "La fecha de salida debe ser posterior a la fecha de entrada"
            )

        hotel = self.repo.obtener_por_id(id_hotel)
        if not hotel:
            raise ErrorReglaNegocioHotel(
                "El hotel solicitado no existe o no cuenta con habitaciones activas"
            )

        if hotel.moneda not in MONEDAS_HOTEL_AIN03:
            raise ErrorReglaNegocioHotel(
                "La moneda configurada para el hotel no está habilitada en AIN-03"
            )

        if hotel.habitaciones_disponibles <= 0:
            raise ErrorReglaNegocioHotel(
                "El hotel no dispone de habitaciones libres para el rango de fechas solicitado"
            )

        noches = (fecha_salida - fecha_entrada).days
        habitaciones = hotel.generar_habitaciones_tarifas(
            noches=noches,
            huespedes=huespedes,
            tipo_habitacion=tipo_norm,
        )

        if not habitaciones:
            raise ErrorReglaNegocioHotel(
                "Ninguna habitación disponible cumple con la capacidad máxima de huéspedes solicitada"
            )

        return ConsultaHabitacionesOut(
            mensaje="Habitaciones y tarifas consultadas exitosamente",
            data=[HabitacionTarifaItemOut(**hab) for hab in habitaciones],
            success=True,
        )

    # HU-021: Bloquear habitación temporalmente (RN-21)
    def bloquear_habitacion(self, payload: BloqueoHabitacionIn) -> BloqueoHabitacionOut:
        tipo_norm = payload.tipo_habitacion.strip().upper()
        capacidades_maximas = {
            "ESTANDAR": 2,
            "DOBLE": 3,
            "SUITE": 4,
            "FAMILIAR": 6,
        }

        if tipo_norm not in TIPOS_HABITACION_VALIDOS:
            raise ErrorParametrosHotel(
                "El tipo de habitación no es válido en el catálogo PAR-09 (ESTANDAR, DOBLE, SUITE, FAMILIAR)"
            )
        if payload.fecha_entrada < date.today():
            raise ErrorParametrosHotel(
                "La fecha de entrada no puede ser anterior a la fecha actual"
            )
        if payload.fecha_salida <= payload.fecha_entrada:
            raise ErrorParametrosHotel(
                "La fecha de salida debe ser al menos un día posterior a la fecha de entrada"
            )

        capacidad_total = capacidades_maximas[tipo_norm] * payload.cantidad_habitaciones
        if payload.huespedes > capacidad_total:
            raise ErrorParametrosHotel(
                "La cantidad de huéspedes supera la capacidad máxima permitida para las habitaciones solicitadas"
            )

        hotel = self.repo.obtener_por_id(payload.id_hotel)
        if not hotel:
            raise ErrorReglaNegocioHotel(
                "El hotel seleccionado no existe o no se encuentra activo"
            )

        if hotel.moneda not in MONEDAS_HOTEL_AIN03:
            raise ErrorReglaNegocioHotel(
                "La moneda configurada para el hotel no está habilitada en AIN-03"
            )

        # RN-21: Validar disponibilidad real antes de ejecutar bloqueo temporal
        if hotel.habitaciones_disponibles < payload.cantidad_habitaciones:
            raise ErrorReglaNegocioHotel(
                "No hay suficientes habitaciones disponibles en el hotel para realizar el bloqueo temporal"
            )

        noches = (payload.fecha_salida - payload.fecha_entrada).days
        total_retenido = hotel.calcular_total_bloqueo(
            tipo_habitacion=tipo_norm,
            noches=noches,
            cantidad_habitaciones=payload.cantidad_habitaciones,
        )

        bloqueo = self.repo.registrar_bloqueo(
            hotel=hotel,
            tipo_habitacion=tipo_norm,
            fecha_entrada=payload.fecha_entrada,
            fecha_salida=payload.fecha_salida,
            noches=noches,
            cantidad_habitaciones=payload.cantidad_habitaciones,
            huespedes=payload.huespedes,
            id_usuario=payload.id_usuario,
            total_retenido=total_retenido,
            minutos_bloqueo=payload.minutos_bloqueo,
        )

        return BloqueoHabitacionOut(
            mensaje="Habitación bloqueada temporalmente de forma exitosa",
            data=BloqueoHabitacionDataOut(**bloqueo.to_response()),
            success=True,
        )
