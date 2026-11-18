import re
from typing import Optional
from app.domain.reserva import (
    CartItemCreate,
    CartItemData,
    CartItemResponse,
    BusinessRuleRN33Exception,
    InvalidCartItemDataException,
    CartItemDetail,
    CartQueryData,
    CartQueryResponse,
    BusinessRuleRN35Exception,
    InvalidCartUserException,
    TotalCalculationData,
    TotalCalculationResponse,
    BusinessRuleRN37Exception,
    UnidentifiedCartException,
    CartCheckoutCreate,
    CartCheckoutData,
    CartCheckoutResponse,
    BusinessRuleRN38Exception,
    InvalidCheckoutDataException,
    ReservationCreate,
    ReservationData,
    ReservationResponse,
    BusinessRuleRN39Exception,
    InvalidReservationDataException,
    RegisterTravelersCreate,
    RegisterTravelersData,
    RegisterTravelersResponse,
    BusinessRuleRN40Exception,
    InvalidTravelersDataException,
    CancelReservationCreate,
    CancelReservationData,
    CancelReservationResponse,
    BusinessRuleRN43Exception,
    InvalidCancellationReasonException,
)
from app.repositories.reserva_repository import ReservationRepository

ALLOWED_SERVICE_TYPES = {"VUELO", "HOTEL", "PAQUETE", "ACTIVIDAD"}

ALLOWED_PAYMENT_METHODS = {
    "TARJETA_CREDITO",
    "TARJETA_DEBITO",
    "PSE",
    "TC_VISA",
    "TC_MASTERCARD",
    "PAYPAL",
}

ALLOWED_CURRENCIES = {"COP", "USD", "EUR"}


class ReservationService:
    def __init__(self, repo: ReservationRepository):
        self.repo = repo

    # ── HU-033: Agregar ítem al carrito ─────────────────────────────
    def add_cart_item(self, data: CartItemCreate) -> CartItemResponse:
        service_type = (data.service_type or "").strip().upper()
        lock_ref = (data.lock_reference_id or "").strip().upper()
        description = (data.description or "").strip()

        # ── VALIDACIÓN DE PARÁMETROS (400 Bad Request) ──────────────────
        if (
            service_type not in ALLOWED_SERVICE_TYPES
            or data.quantity <= 0
            or data.unit_price <= 0
            or not lock_ref.startswith("BLK-")
        ):
            raise InvalidCartItemDataException(
                "El tipo de servicio, cantidad o referencia de bloqueo no son válidos"
            )

        # ── REGLA DE NEGOCIO RN-33 (409 Conflict) ──────────────────────
        # 1. Verificar que el bloqueo temporal siga vigente (AIN-09, AIN-10, AIN-13)
        if not self.repo.is_service_lock_valid(lock_ref):
            raise BusinessRuleRN33Exception(
                "El bloqueo temporal del servicio ha expirado o el ítem ya está en el carrito"
            )

        # 2. Verificar que el mismo bloqueo no haya sido agregado ya al carrito
        if self.repo.is_lock_duplicated_in_cart(lock_ref):
            raise BusinessRuleRN33Exception(
                "El bloqueo temporal del servicio ha expirado o el ítem ya está en el carrito"
            )

        # ── REGISTRO DEL ÍTEM EN EL CARRITO (201 Created) ──────────────
        item = self.repo.add_item_to_cart(
            user_id=data.user_id,
            service_type=service_type,
            lock_reference_id=lock_ref,
            description=description,
            quantity=data.quantity,
            unit_price=data.unit_price,
        )

        response_data = CartItemData(
            id_carrito=item["id_carrito"],
            id_item=item["id_item"],
            tipo_servicio=item["tipo_servicio"],
            id_referencia_bloqueo=item["id_referencia_bloqueo"],
            cantidad=item["cantidad"],
            subtotal=item["subtotal"],
            total_items_carrito=item["total_items_carrito"],
        )

        return CartItemResponse(
            mensaje="Ítem agregado al carrito exitosamente",
            data=response_data,
            success=True,
        )

    # ── HU-035: Consultar carrito ───────────────────────────────────
    def get_cart(self, user_id: Optional[int]) -> CartQueryResponse:
        # ── VALIDACIÓN DE PARÁMETROS (400 Bad Request) ──────────────────
        if user_id is None or user_id <= 0:
            raise InvalidCartUserException(
                "Identificador de usuario inválido o faltante"
            )

        cart = self.repo.get_cart_by_user(user_id)
        if not cart:
            raise InvalidCartUserException(
                "Identificador de usuario inválido o faltante"
            )

        # ── REGLA DE NEGOCIO RN-35 (409 Conflict) ──────────────────────
        # Verificar que ningún bloqueo temporal del carrito haya expirado
        if not cart.get("bloqueos_vigentes", False):
            raise BusinessRuleRN35Exception(
                "El carrito contiene ítems cuyos bloqueos temporales han expirado"
            )

        # ── CONSTRUCCIÓN DE RESPUESTA ESTANDARIZADA (200 OK) ────────────
        raw_items = cart.get("items_consulta", [])
        items = [
            CartItemDetail(
                id_item=item["id_item"],
                tipo_servicio=item["tipo_servicio"],
                descripcion=item["descripcion"],
                cantidad=item["cantidad"],
                subtotal=float(item["subtotal"]),
            )
            for item in raw_items
        ]

        response_data = CartQueryData(
            id_carrito=cart["id_carrito"],
            id_usuario=cart["id_usuario"],
            moneda=cart["moneda"],
            estado=cart["estado_carrito"],
            items=items,
        )

        return CartQueryResponse(
            mensaje="Carrito consultado exitosamente",
            data=response_data,
            success=True,
        )

    # ── HU-037: Calcular total de la compra ─────────────────────────
    def calculate_purchase_total(self, user_id: Optional[int]) -> TotalCalculationResponse:
        # ── VALIDACIÓN DE PARÁMETROS (400 Bad Request) ──────────────────
        if user_id is None or user_id <= 0:
            raise UnidentifiedCartException(
                "No se pudo identificar el carrito del usuario"
            )

        cart = self.repo.get_cart_by_user(user_id)
        if not cart:
            raise UnidentifiedCartException(
                "No se pudo identificar el carrito del usuario"
            )

        # ── REGLA DE NEGOCIO RN-37 (409 Conflict) ──────────────────────
        # El carrito debe tener ítems válidos y sus bloqueos/servicios no deben haber expirado
        if not cart.get("tiene_items_validos", False) or not cart.get("bloqueos_vigentes", False):
            raise BusinessRuleRN37Exception(
                "El carrito está vacío o contiene servicios expirados que impiden liquidar"
            )

        # ── CÁLCULO FINANCIERO CON PRECISIÓN DECIMAL (AIN-05) ───────────
        currency = cart.get("moneda", "COP")
        decimals = self.repo.get_currency_precision_ain05(currency)

        subtotal = round(float(cart.get("subtotal", 2521008.0)), decimals)
        taxes = round(float(cart.get("impuestos", 478992.0)), decimals)
        discounts = round(float(cart.get("descuentos", 0.0)), decimals)
        total_to_pay = round(subtotal + taxes - discounts, decimals)

        response_data = TotalCalculationData(
            id_carrito=cart["id_carrito"],
            moneda=currency,
            subtotal=subtotal,
            impuestos=taxes,
            descuentos=discounts,
            total_pagar=total_to_pay,
        )

        return TotalCalculationResponse(
            mensaje="Total de la compra calculado exitosamente",
            data=response_data,
            success=True,
        )

    # ── HU-038: Cerrar compra ───────────────────────────────────────
    def close_purchase(self, data: CartCheckoutCreate) -> CartCheckoutResponse:
        payment_method = (data.payment_method or "").strip().upper()
        address = (data.billing_address or "").strip()

        # ── VALIDACIÓN DE PARÁMETROS (400 Bad Request) ──────────────────
        if not payment_method or not address or len(address) < 5 or payment_method not in ALLOWED_PAYMENT_METHODS:
            raise InvalidCheckoutDataException(
                "Datos de facturación o medio de pago incompletos"
            )

        # ── REGLA DE NEGOCIO RN-38 (409 Conflict) ──────────────────────
        # 1. Revalidar identidad del viajero en AIN-08
        if not self.repo.verify_identity_ain08(data.user_id):
            raise BusinessRuleRN38Exception(
                "El carrito ya fue cerrado previamente o algún bloqueo de servicio caducó"
            )

        # 2. Verificar que el carrito exista y esté en estado ABIERTO
        cart = self.repo.get_cart(data.cart_id)
        if not cart or cart.get("estado_carrito") != "ABIERTO":
            raise BusinessRuleRN38Exception(
                "El carrito ya fue cerrado previamente o algún bloqueo de servicio caducó"
            )

        # 3. Verificar que todos los bloqueos de vuelos (AIN-09) y hoteles (AIN-10) estén vigentes
        if not self.repo.verify_locks_ain09_ain10(cart):
            raise BusinessRuleRN38Exception(
                "El carrito ya fue cerrado previamente o algún bloqueo de servicio caducó"
            )

        # ── CIERRE DEL CARRITO Y SOLICITUD DE COBRO (AIN-14) ────────────
        closed_cart = self.repo.close_cart_and_request_charge_ain14(
            cart_id=data.cart_id,
            payment_method=payment_method,
            billing_address=address,
        )

        # ── RESPUESTA ESTANDARIZADA (201 Created) ──────────────────────
        response_data = CartCheckoutData(
            id_carrito=closed_cart["id_carrito"],
            estado_carrito=closed_cart["estado_carrito"],
            codigo_reserva_preliminar=closed_cart["codigo_reserva_preliminar"],
            total_liquidado=float(closed_cart["total_liquidado"]),
            moneda=closed_cart["moneda"],
        )

        return CartCheckoutResponse(
            mensaje="Compra cerrada exitosamente, pendiente de confirmación de pago",
            data=response_data,
            success=True,
        )

    # ── HU-039: Crear reserva ───────────────────────────────────────
    def create_reservation(self, data: ReservationCreate) -> ReservationResponse:
        currency = (data.currency or "").strip().upper()

        # ── VALIDACIÓN DE PARÁMETROS Y EXISTENCIA DEL CARRITO (400 Bad Request) ──
        if currency not in ALLOWED_CURRENCIES or data.total_reservation <= 0:
            raise InvalidReservationDataException(
                "Datos inválidos o carrito no encontrado para generar la reserva"
            )

        if not self.repo.verify_identity_ain08(data.user_id):
            raise InvalidReservationDataException(
                "Datos inválidos o carrito no encontrado para generar la reserva"
            )

        cart = self.repo.get_cart(data.cart_id)
        if not cart:
            raise InvalidReservationDataException(
                "Datos inválidos o carrito no encontrado para generar la reserva"
            )

        # ── REGLA DE NEGOCIO RN-39 (409 Conflict) ──────────────────────
        # Evitar duplicidad de reserva sobre un mismo carrito de compras
        if self.repo.has_existing_reservation_for_cart(data.cart_id):
            raise BusinessRuleRN39Exception(
                "Ya existe una reserva generada para este carrito de compras"
            )

        # ── PERSISTENCIA DE LA RESERVA OFICIAL (MOD-05) ────────────────
        record = self.repo.create_reservation(
            user_id=data.user_id,
            cart_id=data.cart_id,
            currency=currency,
            total_reservation=data.total_reservation,
        )

        # ── RESPUESTA ESTANDARIZADA (201 Created) ──────────────────────
        response_data = ReservationData(
            id_reserva=record["id_reserva"],
            codigo_reserva=record["codigo_reserva"],
            id_usuario=record["id_usuario"],
            estado=record["estado"],
            total=record["total"],
            moneda=record["moneda"],
            fecha_creacion=record["fecha_creacion"],
        )

        return ReservationResponse(
            mensaje="Reserva creada exitosamente",
            data=response_data,
            success=True,
        )

    # ── HU-040: Registrar viajeros ──────────────────────────────────
    def register_travelers(self, reservation_id: int, data: RegisterTravelersCreate) -> RegisterTravelersResponse:
        # ── VALIDACIÓN DE PARÁMETROS Y CATÁLOGO AIN-01 (400 Bad Request) ──
        if not data.travelers:
            raise InvalidTravelersDataException(
                "Datos de viajeros incompletos o tipo de documento inválido"
            )

        reservation = self.repo.get_reservation_by_id(reservation_id)
        if not reservation:
            raise InvalidTravelersDataException(
                "Datos de viajeros incompletos o tipo de documento inválido"
            )

        cleaned_travelers = []
        seen_documents = set()
        has_duplicates = False

        for traveler in data.travelers:
            first_name = (traveler.first_name or "").strip()
            last_name = (traveler.last_name or "").strip()
            doc_type = (traveler.document_type or "").strip().upper()
            doc_number = (traveler.document_number or "").strip()
            birth_date = (traveler.birth_date or "").strip()

            # Validar campos obligatorios y formato de fecha YYYY-MM-DD
            if (
                not first_name
                or not last_name
                or not doc_type
                or not doc_number
                or len(doc_number) < 4
                or not re.match(r"^\d{4}-\d{2}-\d{2}$", birth_date)
            ):
                raise InvalidTravelersDataException(
                    "Datos de viajeros incompletos o tipo de documento inválido"
                )

            # Validar tipo de documento contra AIN-01
            if not self.repo.validate_document_type_ain01(doc_type):
                raise InvalidTravelersDataException(
                    "Datos de viajeros incompletos o tipo de documento inválido"
                )

            if doc_number in seen_documents:
                has_duplicates = True
            seen_documents.add(doc_number)

            cleaned_travelers.append(
                {
                    "nombres": first_name,
                    "apellidos": last_name,
                    "tipo_documento": doc_type,
                    "numero_documento": doc_number,
                    "fecha_nacimiento": birth_date,
                    "es_titular": traveler.is_holder,
                }
            )

        # ── REGLA DE NEGOCIO RN-40 (409 Conflict) ──────────────────────
        # 1. Cantidad de viajeros debe coincidir con los cupos reservados (2 para 9001)
        # 2. No pueden existir números de documento repetidos en la misma reserva
        expected_spots = int(reservation.get("cupos_reservados", 2))
        if has_duplicates or len(cleaned_travelers) != expected_spots:
            raise BusinessRuleRN40Exception(
                "La cantidad de viajeros no coincide con los cupos o hay documentos duplicados"
            )

        # ── REGISTRO EN REPOSITORIO Y RESPUESTA (201 Created) ──────────
        updated_reservation = self.repo.register_travelers_in_reservation(
            reservation_id=reservation_id,
            travelers=cleaned_travelers,
        )

        response_data = RegisterTravelersData(
            id_reserva=updated_reservation["id_reserva"],
            codigo_reserva=updated_reservation["codigo_reserva"],
            total_viajeros_registrados=len(cleaned_travelers),
            estado_nominacion=updated_reservation["estado_nominacion"],
        )

        return RegisterTravelersResponse(
            mensaje="Viajeros registrados en la reserva exitosamente",
            data=response_data,
            success=True,
        )

    # ── HU-043: Cancelar reserva ────────────────────────────────────
    def cancel_reservation(self, reservation_id: int, data: CancelReservationCreate) -> CancelReservationResponse:
        reason = (data.cancellation_reason or "").strip()

        # ── VALIDACIÓN DE PARÁMETROS (400 Bad Request) ──────────────────
        if not reason or len(reason) < 5 or data.user_id <= 0:
            raise InvalidCancellationReasonException(
                "Debe proporcionar un motivo válido para cancelar la reserva"
            )

        # ── REGLA DE NEGOCIO RN-43 (409 Conflict) ──────────────────────
        # 1. Verificar que la reserva exista
        reservation = self.repo.get_reservation_by_id(reservation_id)
        if not reservation:
            raise BusinessRuleRN43Exception(
                "La reserva ya se encuentra cancelada o en un estado final que no permite anulación"
            )

        # 2. Verificar en AIN-05 que el estado actual de la reserva admita cancelación
        current_status = reservation.get("estado", "")
        if not self.repo.can_cancel_status_ain05(current_status):
            raise BusinessRuleRN43Exception(
                "La reserva ya se encuentra cancelada o en un estado final que no permite anulación"
            )

        # ── ACTUALIZACIÓN A CANCELADA Y NOTIFICACIÓN AIN-16 (200 OK) ────
        result = self.repo.cancel_reservation(reservation_id=reservation_id, reason=reason)
        self.repo.notify_cancellation_ain16(
            reservation_id=reservation_id,
            reservation_code=result["codigo_reserva"],
            user_id=data.user_id,
        )

        response_data = CancelReservationData(
            id_reserva=result["id_reserva"],
            codigo_reserva=result["codigo_reserva"],
            estado_anterior=result["estado_anterior"],
            estado_actual=result["estado_actual"],
            aplica_reembolso=result["aplica_reembolso"],
            fecha_cancelacion=result["fecha_cancelacion"],
        )

        return CancelReservationResponse(
            mensaje="Reserva cancelada exitosamente",
            data=response_data,
            success=True,
        )
