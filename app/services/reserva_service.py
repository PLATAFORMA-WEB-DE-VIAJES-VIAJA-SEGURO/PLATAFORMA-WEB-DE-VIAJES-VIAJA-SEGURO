from app.domain.reserva import (
    CierreCarritoCreate,
    CierreCarritoData,
    CierreCarritoResponse,
    ReglaNegocioRN38Exception,
    DatosCierreCompraInvalidosException,
    ReservaCreate,
    ReservaData,
    ReservaResponse,
    ReglaNegocioRN39Exception,
    DatosReservaInvalidosException,
)
from app.repositories.reserva_repository import ReservaRepository

MEDIOS_PAGO_PERMITIDOS = {
    "TARJETA_CREDITO",
    "TARJETA_DEBITO",
    "PSE",
    "TC_VISA",
    "TC_MASTERCARD",
    "PAYPAL",
}

MONEDAS_PERMITIDAS = {"COP", "USD", "EUR"}


class ReservaService:
    def __init__(self, repo: ReservaRepository):
        self.repo = repo

    # ── HU-038: Cerrar compra ───────────────────────────────────────
    def cerrar_compra(self, datos: CierreCarritoCreate) -> CierreCarritoResponse:
        medio_pago = (datos.medio_pago or "").strip().upper()
        direccion = (datos.direccion_facturacion or "").strip()

        # ── VALIDACIÓN DE PARÁMETROS (400 Bad Request) ──────────────────
        if not medio_pago or not direccion or len(direccion) < 5 or medio_pago not in MEDIOS_PAGO_PERMITIDOS:
            raise DatosCierreCompraInvalidosException(
                "Datos de facturación o medio de pago incompletos"
            )

        # ── REGLA DE NEGOCIO RN-38 (409 Conflict) ──────────────────────
        # 1. Revalidar identidad del viajero en AIN-08
        if not self.repo.verificar_identidad_ain08(datos.id_usuario):
            raise ReglaNegocioRN38Exception(
                "El carrito ya fue cerrado previamente o algún bloqueo de servicio caducó"
            )

        # 2. Verificar que el carrito exista y esté en estado ABIERTO
        carrito = self.repo.obtener_carrito(datos.id_carrito)
        if not carrito or carrito.get("estado_carrito") != "ABIERTO":
            raise ReglaNegocioRN38Exception(
                "El carrito ya fue cerrado previamente o algún bloqueo de servicio caducó"
            )

        # 3. Verificar que todos los bloqueos de vuelos (AIN-09) y hoteles (AIN-10) estén vigentes
        if not self.repo.verificar_bloqueos_ain09_ain10(carrito):
            raise ReglaNegocioRN38Exception(
                "El carrito ya fue cerrado previamente o algún bloqueo de servicio caducó"
            )

        # ── CIERRE DEL CARRITO Y SOLICITUD DE COBRO (AIN-14) ────────────
        carrito_cerrado = self.repo.cerrar_carrito_y_solicitar_cobro_ain14(
            id_carrito=datos.id_carrito,
            medio_pago=medio_pago,
            direccion_facturacion=direccion,
        )

        # ── RESPUESTA ESTANDARIZADA (201 Created) ──────────────────────
        data = CierreCarritoData(
            id_carrito=carrito_cerrado["id_carrito"],
            estado_carrito=carrito_cerrado["estado_carrito"],
            codigo_reserva_preliminar=carrito_cerrado["codigo_reserva_preliminar"],
            total_liquidado=float(carrito_cerrado["total_liquidado"]),
            moneda=carrito_cerrado["moneda"],
        )

        return CierreCarritoResponse(
            mensaje="Compra cerrada exitosamente, pendiente de confirmación de pago",
            data=data,
            success=True,
        )

    # ── HU-039: Crear reserva ───────────────────────────────────────
    def crear_reserva(self, datos: ReservaCreate) -> ReservaResponse:
        moneda = (datos.moneda or "").strip().upper()

        # ── VALIDACIÓN DE PARÁMETROS Y EXISTENCIA DEL CARRITO (400 Bad Request) ──
        if moneda not in MONEDAS_PERMITIDAS or datos.total_reserva <= 0:
            raise DatosReservaInvalidosException(
                "Datos inválidos o carrito no encontrado para generar la reserva"
            )

        if not self.repo.verificar_identidad_ain08(datos.id_usuario):
            raise DatosReservaInvalidosException(
                "Datos inválidos o carrito no encontrado para generar la reserva"
            )

        carrito = self.repo.obtener_carrito(datos.id_carrito)
        if not carrito:
            raise DatosReservaInvalidosException(
                "Datos inválidos o carrito no encontrado para generar la reserva"
            )

        # ── REGLA DE NEGOCIO RN-39 (409 Conflict) ──────────────────────
        # Evitar duplicidad de reserva sobre un mismo carrito de compras
        if self.repo.verificar_reserva_existente_por_carrito(datos.id_carrito):
            raise ReglaNegocioRN39Exception(
                "Ya existe una reserva generada para este carrito de compras"
            )

        # ── PERSISTENCIA DE LA RESERVA OFICIAL (MOD-05) ────────────────
        registro = self.repo.crear_reserva(
            id_usuario=datos.id_usuario,
            id_carrito=datos.id_carrito,
            moneda=moneda,
            total_reserva=datos.total_reserva,
        )

        # ── RESPUESTA ESTANDARIZADA (201 Created) ──────────────────────
        data = ReservaData(
            id_reserva=registro["id_reserva"],
            codigo_reserva=registro["codigo_reserva"],
            id_usuario=registro["id_usuario"],
            estado=registro["estado"],
            total=registro["total"],
            moneda=registro["moneda"],
            fecha_creacion=registro["fecha_creacion"],
        )

        return ReservaResponse(
            mensaje="Reserva creada exitosamente",
            data=data,
            success=True,
        )
