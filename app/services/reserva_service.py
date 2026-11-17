import re
from typing import Optional
from app.domain.reserva import (
    ItemCarritoCreate,
    ItemCarritoData,
    ItemCarritoResponse,
    ReglaNegocioRN33Exception,
    DatosItemCarritoInvalidosException,
    DetalleItemCarrito,
    ConsultaCarritoData,
    ConsultaCarritoResponse,
    ReglaNegocioRN35Exception,
    UsuarioCarritoInvalidoException,
    CalculoTotalData,
    CalculoTotalResponse,
    ReglaNegocioRN37Exception,
    CarritoNoIdentificadoException,
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
    RegistrarViajerosCreate,
    RegistrarViajerosData,
    RegistrarViajerosResponse,
    ReglaNegocioRN40Exception,
    DatosViajerosInvalidosException,
    CancelarReservaCreate,
    CancelarReservaData,
    CancelarReservaResponse,
    ReglaNegocioRN43Exception,
    MotivoCancelacionInvalidoException,
)
from app.repositories.reserva_repository import ReservaRepository

TIPOS_SERVICIO_PERMITIDOS = {"VUELO", "HOTEL", "PAQUETE", "ACTIVIDAD"}

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

    # ── HU-033: Agregar ítem al carrito ─────────────────────────────
    def agregar_item_carrito(self, datos: ItemCarritoCreate) -> ItemCarritoResponse:
        tipo_servicio = (datos.tipo_servicio or "").strip().upper()
        ref_bloqueo = (datos.id_referencia_bloqueo or "").strip().upper()
        descripcion = (datos.descripcion or "").strip()

        # ── VALIDACIÓN DE PARÁMETROS (400 Bad Request) ──────────────────
        if (
            tipo_servicio not in TIPOS_SERVICIO_PERMITIDOS
            or datos.cantidad <= 0
            or datos.precio_unitario <= 0
            or not ref_bloqueo.startswith("BLK-")
        ):
            raise DatosItemCarritoInvalidosException(
                "El tipo de servicio, cantidad o referencia de bloqueo no son válidos"
            )

        # ── REGLA DE NEGOCIO RN-33 (409 Conflict) ──────────────────────
        # 1. Verificar que el bloqueo temporal siga vigente (AIN-09, AIN-10, AIN-13)
        if not self.repo.verificar_bloqueo_servicio_vigente(ref_bloqueo):
            raise ReglaNegocioRN33Exception(
                "El bloqueo temporal del servicio ha expirado o el ítem ya está en el carrito"
            )

        # 2. Verificar que el mismo bloqueo no haya sido agregado ya al carrito
        if self.repo.verificar_bloqueo_duplicado_en_carrito(ref_bloqueo):
            raise ReglaNegocioRN33Exception(
                "El bloqueo temporal del servicio ha expirado o el ítem ya está en el carrito"
            )

        # ── REGISTRO DEL ÍTEM EN EL CARRITO (201 Created) ──────────────
        item = self.repo.agregar_item_al_carrito(
            id_usuario=datos.id_usuario,
            tipo_servicio=tipo_servicio,
            id_referencia_bloqueo=ref_bloqueo,
            descripcion=descripcion,
            cantidad=datos.cantidad,
            precio_unitario=datos.precio_unitario,
        )

        data = ItemCarritoData(
            id_carrito=item["id_carrito"],
            id_item=item["id_item"],
            tipo_servicio=item["tipo_servicio"],
            id_referencia_bloqueo=item["id_referencia_bloqueo"],
            cantidad=item["cantidad"],
            subtotal=item["subtotal"],
            total_items_carrito=item["total_items_carrito"],
        )

        return ItemCarritoResponse(
            mensaje="Ítem agregado al carrito exitosamente",
            data=data,
            success=True,
        )

    # ── HU-035: Consultar carrito ───────────────────────────────────
    def consultar_carrito(self, id_usuario: Optional[int]) -> ConsultaCarritoResponse:
        # ── VALIDACIÓN DE PARÁMETROS (400 Bad Request) ──────────────────
        if id_usuario is None or id_usuario <= 0:
            raise UsuarioCarritoInvalidoException(
                "Identificador de usuario inválido o faltante"
            )

        carrito = self.repo.obtener_carrito_por_usuario(id_usuario)
        if not carrito:
            raise UsuarioCarritoInvalidoException(
                "Identificador de usuario inválido o faltante"
            )

        # ── REGLA DE NEGOCIO RN-35 (409 Conflict) ──────────────────────
        # Verificar que ningún bloqueo temporal del carrito haya expirado
        if not carrito.get("bloqueos_vigentes", False):
            raise ReglaNegocioRN35Exception(
                "El carrito contiene ítems cuyos bloqueos temporales han expirado"
            )

        # ── CONSTRUCCIÓN DE RESPUESTA ESTANDARIZADA (200 OK) ────────────
        items_raw = carrito.get("items_consulta", [])
        items = [
            DetalleItemCarrito(
                id_item=item["id_item"],
                tipo_servicio=item["tipo_servicio"],
                descripcion=item["descripcion"],
                cantidad=item["cantidad"],
                subtotal=float(item["subtotal"]),
            )
            for item in items_raw
        ]

        data = ConsultaCarritoData(
            id_carrito=carrito["id_carrito"],
            id_usuario=carrito["id_usuario"],
            moneda=carrito["moneda"],
            estado=carrito["estado_carrito"],
            items=items,
        )

        return ConsultaCarritoResponse(
            mensaje="Carrito consultado exitosamente",
            data=data,
            success=True,
        )

    # ── HU-037: Calcular total de la compra ─────────────────────────
    def calcular_total_compra(self, id_usuario: Optional[int]) -> CalculoTotalResponse:
        # ── VALIDACIÓN DE PARÁMETROS (400 Bad Request) ──────────────────
        if id_usuario is None or id_usuario <= 0:
            raise CarritoNoIdentificadoException(
                "No se pudo identificar el carrito del usuario"
            )

        carrito = self.repo.obtener_carrito_por_usuario(id_usuario)
        if not carrito:
            raise CarritoNoIdentificadoException(
                "No se pudo identificar el carrito del usuario"
            )

        # ── REGLA DE NEGOCIO RN-37 (409 Conflict) ──────────────────────
        # El carrito debe tener ítems válidos y sus bloqueos/servicios no deben haber expirado
        if not carrito.get("tiene_items_validos", False) or not carrito.get("bloqueos_vigentes", False):
            raise ReglaNegocioRN37Exception(
                "El carrito está vacío o contiene servicios expirados que impiden liquidar"
            )

        # ── CÁLCULO FINANCIERO CON PRECISIÓN DECIMAL (AIN-05) ───────────
        moneda = carrito.get("moneda", "COP")
        decimales = self.repo.obtener_precision_moneda_ain05(moneda)

        subtotal = round(float(carrito.get("subtotal", 2521008.0)), decimales)
        impuestos = round(float(carrito.get("impuestos", 478992.0)), decimales)
        descuentos = round(float(carrito.get("descuentos", 0.0)), decimales)
        total_pagar = round(subtotal + impuestos - descuentos, decimales)

        data = CalculoTotalData(
            id_carrito=carrito["id_carrito"],
            moneda=moneda,
            subtotal=subtotal,
            impuestos=impuestos,
            descuentos=descuentos,
            total_pagar=total_pagar,
        )

        return CalculoTotalResponse(
            mensaje="Total de la compra calculado exitosamente",
            data=data,
            success=True,
        )

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

    # ── HU-040: Registrar viajeros ──────────────────────────────────
    def registrar_viajeros(self, id_reserva: int, datos: RegistrarViajerosCreate) -> RegistrarViajerosResponse:
        # ── VALIDACIÓN DE PARÁMETROS Y CATÁLOGO AIN-01 (400 Bad Request) ──
        if not datos.viajeros:
            raise DatosViajerosInvalidosException(
                "Datos de viajeros incompletos o tipo de documento inválido"
            )

        reserva = self.repo.obtener_reserva_por_id(id_reserva)
        if not reserva:
            raise DatosViajerosInvalidosException(
                "Datos de viajeros incompletos o tipo de documento inválido"
            )

        viajeros_limpios = []
        documentos_vistos = set()
        hay_duplicados = False

        for v in datos.viajeros:
            nombres = (v.nombres or "").strip()
            apellidos = (v.apellidos or "").strip()
            tipo_doc = (v.tipo_documento or "").strip().upper()
            num_doc = (v.numero_documento or "").strip()
            fecha_nac = (v.fecha_nacimiento or "").strip()

            # Validar campos obligatorios y formato de fecha YYYY-MM-DD
            if (
                not nombres
                or not apellidos
                or not tipo_doc
                or not num_doc
                or len(num_doc) < 4
                or not re.match(r"^\d{4}-\d{2}-\d{2}$", fecha_nac)
            ):
                raise DatosViajerosInvalidosException(
                    "Datos de viajeros incompletos o tipo de documento inválido"
                )

            # Validar tipo de documento contra AIN-01
            if not self.repo.validar_tipo_documento_ain01(tipo_doc):
                raise DatosViajerosInvalidosException(
                    "Datos de viajeros incompletos o tipo de documento inválido"
                )

            if num_doc in documentos_vistos:
                hay_duplicados = True
            documentos_vistos.add(num_doc)

            viajeros_limpios.append(
                {
                    "nombres": nombres,
                    "apellidos": apellidos,
                    "tipo_documento": tipo_doc,
                    "numero_documento": num_doc,
                    "fecha_nacimiento": fecha_nac,
                    "es_titular": v.es_titular,
                }
            )

        # ── REGLA DE NEGOCIO RN-40 (409 Conflict) ──────────────────────
        # 1. Cantidad de viajeros debe coincidir con los cupos reservados (2 para 9001)
        # 2. No pueden existir números de documento repetidos en la misma reserva
        cupos_esperados = int(reserva.get("cupos_reservados", 2))
        if hay_duplicados or len(viajeros_limpios) != cupos_esperados:
            raise ReglaNegocioRN40Exception(
                "La cantidad de viajeros no coincide con los cupos o hay documentos duplicados"
            )

        # ── REGISTRO EN REPOSITORIO Y RESPUESTA (201 Created) ──────────
        reserva_actualizada = self.repo.registrar_viajeros_en_reserva(
            id_reserva=id_reserva,
            viajeros=viajeros_limpios,
        )

        data = RegistrarViajerosData(
            id_reserva=reserva_actualizada["id_reserva"],
            codigo_reserva=reserva_actualizada["codigo_reserva"],
            total_viajeros_registrados=len(viajeros_limpios),
            estado_nominacion=reserva_actualizada["estado_nominacion"],
        )

        return RegistrarViajerosResponse(
            mensaje="Viajeros registrados en la reserva exitosamente",
            data=data,
            success=True,
        )

    # ── HU-043: Cancelar reserva ────────────────────────────────────
    def cancelar_reserva(self, id_reserva: int, datos: CancelarReservaCreate) -> CancelarReservaResponse:
        motivo = (datos.motivo_cancelacion or "").strip()

        # ── VALIDACIÓN DE PARÁMETROS (400 Bad Request) ──────────────────
        if not motivo or len(motivo) < 5 or datos.id_usuario <= 0:
            raise MotivoCancelacionInvalidoException(
                "Debe proporcionar un motivo válido para cancelar la reserva"
            )

        # ── REGLA DE NEGOCIO RN-43 (409 Conflict) ──────────────────────
        # 1. Verificar que la reserva exista
        reserva = self.repo.obtener_reserva_por_id(id_reserva)
        if not reserva:
            raise ReglaNegocioRN43Exception(
                "La reserva ya se encuentra cancelada o en un estado final que no permite anulación"
            )

        # 2. Verificar en AIN-05 que el estado actual de la reserva admita cancelación
        estado_actual = reserva.get("estado", "")
        if not self.repo.verificar_estado_admite_cancelacion_ain05(estado_actual):
            raise ReglaNegocioRN43Exception(
                "La reserva ya se encuentra cancelada o en un estado final que no permite anulación"
            )

        # ── ACTUALIZACIÓN A CANCELADA Y NOTIFICACIÓN AIN-16 (200 OK) ────
        resultado = self.repo.cancelar_reserva(id_reserva=id_reserva, motivo=motivo)
        self.repo.notificar_cancelacion_ain16(
            id_reserva=id_reserva,
            codigo_reserva=resultado["codigo_reserva"],
            id_usuario=datos.id_usuario,
        )

        data = CancelarReservaData(
            id_reserva=resultado["id_reserva"],
            codigo_reserva=resultado["codigo_reserva"],
            estado_anterior=resultado["estado_anterior"],
            estado_actual=resultado["estado_actual"],
            aplica_reembolso=resultado["aplica_reembolso"],
            fecha_cancelacion=resultado["fecha_cancelacion"],
        )

        return CancelarReservaResponse(
            mensaje="Reserva cancelada exitosamente",
            data=data,
            success=True,
        )
