from app.domain.reserva import (
    CierreCarritoCreate,
    CierreCarritoData,
    CierreCarritoResponse,
    ReglaNegocioRN38Exception,
    DatosCierreCompraInvalidosException,
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


class ReservaService:
    def __init__(self, repo: ReservaRepository):
        self.repo = repo

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
