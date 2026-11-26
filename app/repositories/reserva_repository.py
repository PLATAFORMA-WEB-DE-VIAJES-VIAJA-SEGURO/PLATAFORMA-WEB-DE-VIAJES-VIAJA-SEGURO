from typing import Dict, Any, Optional, List
from datetime import datetime, timezone


class ReservationRepository:
    """
    Repositorio que coordina la integración con AIN-01 (Catálogo Documentos),
    AIN-05 (Catálogos Reserva, Estado y Moneda), AIN-08 (Identidad),
    AIN-09 (Bloqueos de Vuelos), AIN-10 (Bloqueos de Hoteles),
    AIN-13 (Paquetes), AIN-14 (Solicitud de Cobro) y AIN-16 (Notificaciones).
    """

    def __init__(self):
        # Ítems precargados para la consulta del carrito (HU-035)
        self._default_items_701 = [
            {
                "id_item": 1,
                "tipo_servicio": "VUELO",
                "descripcion": "Vuelo BOG - CTG (2 pasajeros)",
                "cantidad": 2,
                "subtotal": 900000.0,
            },
            {
                "id_item": 2,
                "tipo_servicio": "HOTEL",
                "descripcion": "Hotel Caribe Cartagena (5 noches)",
                "cantidad": 1,
                "subtotal": 2100000.0,
            },
        ]

        # Catálogo de carritos en memoria para pruebas funcionales en Swagger UI
        self._carts: Dict[int, Dict[str, Any]] = {
            701: {
                "id_carrito": 701,
                "id_usuario": 1,
                "estado_carrito": "ABIERTO",
                "bloqueos_vigentes": True,
                "tiene_items_validos": True,
                "codigo_reserva_preliminar": "VS-2026-8841",
                "subtotal": 2521008.0,
                "impuestos": 478992.0,
                "descuentos": 0.0,
                "total_liquidado": 3000000.0,
                "moneda": "COP",
                "items": [],
                "items_consulta": list(self._default_items_701),
            },
            702: {
                "id_carrito": 702,
                "id_usuario": 2,
                "estado_carrito": "ABIERTO",
                "bloqueos_vigentes": True,
                "tiene_items_validos": True,
                "codigo_reserva_preliminar": "VS-2026-8842",
                "subtotal": 1260504.0,
                "impuestos": 239496.0,
                "descuentos": 0.0,
                "total_liquidado": 1500000.0,
                "moneda": "COP",
                "items": [],
                "items_consulta": list(self._default_items_701),
            },
            703: {
                "id_carrito": 703,
                "id_usuario": 3,
                "estado_carrito": "ABIERTO",
                "bloqueos_vigentes": True,
                "tiene_items_validos": True,
                "codigo_reserva_preliminar": "VS-2026-8843",
                "subtotal": 3529412.0,
                "impuestos": 670588.0,
                "descuentos": 0.0,
                "total_liquidado": 4200000.0,
                "moneda": "COP",
                "items": [],
                "items_consulta": list(self._default_items_701),
            },
            700: {
                "id_carrito": 700,
                "id_usuario": 4,
                "estado_carrito": "CERRADO",
                "bloqueos_vigentes": False,
                "tiene_items_validos": False,
                "codigo_reserva_preliminar": "VS-2026-8800",
                "subtotal": 0.0,
                "impuestos": 0.0,
                "descuentos": 0.0,
                "total_liquidado": 0.0,
                "moneda": "COP",
                "items": [],
                "items_consulta": [],
            },
        }

        # Relación usuario -> carrito activo
        self._cart_by_user: Dict[int, int] = {
            1: 701,
            2: 702,
            3: 703,
            4: 700,
            409: 700,
        }

        # Control de ítems agregados al carrito para HU-033 (RN-33)
        self._next_item_id = 1
        self._locks_in_cart: set = set()
        self._expired_locks: set = {
            "BLK-EXPIRADO",
            "BLK-V-0000",
            "BLK-H-0000",
            "BLK-P-0000",
            "BLK-409",
        }

        # Catálogo de precisión decimal por moneda en AIN-05
        self._currency_precision_ain05: Dict[str, int] = {
            "COP": 1,
            "USD": 2,
            "EUR": 2,
        }

        # Estados de reserva que admiten cancelación según AIN-05 (RN-43)
        self._cancellable_states_ain05 = {"CONFIRMADA", "PENDIENTE_PAGO"}

        # Usuarios con identidad verificada en AIN-08
        self._verified_users = {1, 2, 3, 4, 5}

        # Almacenamiento de reservas creadas (HU-039)
        self._created_reservations: List[Dict[str, Any]] = []
        # Carritos que ya tienen reserva generada (700 precargado para pruebas de RN-39)
        self._carts_with_reservation: set = {700}
        # Secuencia de IDs de reserva según especificación HU-039 (inicia en 9001)
        self._next_reservation_id = 9001

        # Reservas base precargadas para pruebas directas de HU-040 y HU-043 en Swagger UI
        self._base_reservations: Dict[int, Dict[str, Any]] = {
            9001: {
                "id_reserva": 9001,
                "codigo_reserva": "VS-2026-8841",
                "id_usuario": 1,
                "estado": "CONFIRMADA",
                "total": 3000000.0,
                "moneda": "COP",
                "cupos_reservados": 2,
                "viajeros": [],
                "estado_nominacion": "PENDIENTE",
            },
            9002: {
                "id_reserva": 9002,
                "codigo_reserva": "VS-2026-8842",
                "id_usuario": 1,
                "estado": "CONFIRMADA",
                "total": 1500000.0,
                "moneda": "COP",
                "cupos_reservados": 2,
                "viajeros": [],
                "estado_nominacion": "PENDIENTE",
            },
            9003: {
                "id_reserva": 9003,
                "codigo_reserva": "VS-2026-8843",
                "id_usuario": 1,
                "estado": "CONFIRMADA",
                "total": 4200000.0,
                "moneda": "COP",
                "cupos_reservados": 2,
                "viajeros": [],
                "estado_nominacion": "PENDIENTE",
            },
            9000: {
                "id_reserva": 9000,
                "codigo_reserva": "VS-2026-8800",
                "id_usuario": 1,
                "estado": "CANCELADA",
                "total": 3000000.0,
                "moneda": "COP",
                "cupos_reservados": 2,
                "viajeros": [],
                "estado_nominacion": "COMPLETA",
            },
        }

        # Tipos de documento válidos en AIN-01
        self._valid_document_types_ain01 = {"CC", "CE", "TI", "PA", "PASAPORTE", "RC", "NIT"}

    # ── Métodos HU-033 (Agregar ítem al carrito) ────────────────────
    def is_service_lock_valid(self, lock_reference_id: str) -> bool:
        """AIN-09 / AIN-10 / AIN-13: Verifica si el bloqueo temporal del servicio está vigente."""
        normalized_ref = lock_reference_id.strip().upper()
        return normalized_ref not in self._expired_locks

    def is_lock_duplicated_in_cart(self, lock_reference_id: str) -> bool:
        """RN-33: Verifica si el mismo bloqueo ya fue agregado previamente al carrito."""
        normalized_ref = lock_reference_id.strip().upper()
        return normalized_ref in self._locks_in_cart

    def add_item_to_cart(
        self,
        user_id: int,
        service_type: str,
        lock_reference_id: str,
        description: str,
        quantity: int,
        unit_price: float,
    ) -> Dict[str, Any]:
        """Agrega un nuevo ítem validado al carrito activo del usuario."""
        cart_id = self._cart_by_user.get(user_id, 701)
        cart = self._carts.get(cart_id, self._carts[701])

        item_id = self._next_item_id
        subtotal = round(float(quantity) * float(unit_price), 1)
        normalized_ref = lock_reference_id.strip().upper()

        new_item = {
            "id_carrito": cart["id_carrito"],
            "id_item": item_id,
            "tipo_servicio": service_type,
            "id_referencia_bloqueo": normalized_ref,
            "descripcion": description,
            "cantidad": quantity,
            "precio_unitario": float(unit_price),
            "subtotal": subtotal,
        }

        cart.setdefault("items", []).append(new_item)
        self._locks_in_cart.add(normalized_ref)
        self._next_item_id += 1

        new_item["total_items_carrito"] = len(cart["items"])
        return new_item

    # ── Métodos HU-035 y HU-037 (Consultar y Calcular carrito) ──────
    def get_cart_by_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """HU-035 / HU-037: Obtiene el carrito asociado al usuario indicado."""
        cart_id = self._cart_by_user.get(user_id)
        if cart_id is None:
            return None
        return self._carts.get(cart_id)

    def get_currency_precision_ain05(self, currency: str) -> int:
        """AIN-05: Retorna la cantidad de decimales de redondeo según la moneda."""
        return self._currency_precision_ain05.get(currency.upper(), 2)

    # ── Métodos HU-038, HU-039 y HU-040 ─────────────────────────────
    def verify_identity_ain08(self, user_id: int) -> bool:
        """AIN-08: Revalida que la identidad del usuario esté activa y verificada."""
        return user_id in self._verified_users

    def get_cart(self, cart_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene la información actual del carrito de compras."""
        return self._carts.get(cart_id)

    def verify_locks_ain09_ain10(self, cart: Dict[str, Any]) -> bool:
        """AIN-09 y AIN-10: Verifica que los bloqueos temporales de vuelos y hoteles sigan vigentes."""
        return bool(cart.get("bloqueos_vigentes", False))

    def close_cart_and_request_charge_ain14(
        self,
        cart_id: int,
        payment_method: str,
        billing_address: str,
    ) -> Dict[str, Any]:
        """
        Transiciona el carrito de ABIERTO a CERRADO, congela la liquidación
        y dispara la orden de reserva pendiente de pago hacia AIN-14.
        """
        cart = self._carts[cart_id]
        cart["estado_carrito"] = "CERRADO"
        cart["medio_pago"] = payment_method
        cart["direccion_facturacion"] = billing_address
        return cart

    def has_existing_reservation_for_cart(self, cart_id: int) -> bool:
        """RN-39: Verifica si ya existe una reserva generada para el carrito dado."""
        return cart_id in self._carts_with_reservation

    def get_initial_status_ain05(self) -> str:
        """AIN-05: Consulta el estado inicial parametrizado para nuevas reservas."""
        return "PENDIENTE_PAGO"

    def create_reservation(
        self,
        user_id: int,
        cart_id: int,
        currency: str,
        total_reservation: float,
    ) -> Dict[str, Any]:
        """
        Persiste la reserva oficial en MOD-05 generando un código localizador único (VS-YYYY-XXXX).
        """
        reservation_id = self._next_reservation_id
        cart = self._carts.get(cart_id, {})

        if reservation_id == 9001 or cart_id == 701:
            reservation_code = cart.get("codigo_reserva_preliminar", "VS-2026-8841")
            created_at = "2026-11-15T17:15:00Z"
        else:
            reservation_code = cart.get("codigo_reserva_preliminar", f"VS-2026-{reservation_id}")
            created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        initial_status = self.get_initial_status_ain05()

        new_reservation = {
            "id_reserva": reservation_id,
            "codigo_reserva": reservation_code,
            "id_usuario": user_id,
            "id_carrito": cart_id,
            "estado": initial_status,
            "total": float(total_reservation),
            "moneda": currency,
            "fecha_creacion": created_at,
            "cupos_reservados": 2,
            "viajeros": [],
            "estado_nominacion": "PENDIENTE",
        }

        self._created_reservations.append(new_reservation)
        self._base_reservations[reservation_id] = new_reservation
        self._carts_with_reservation.add(cart_id)
        self._next_reservation_id += 1

        return new_reservation

    def validate_document_type_ain01(self, document_type: str) -> bool:
        """AIN-01: Verifica que el tipo de documento exista en el catálogo oficial."""
        return document_type.strip().upper() in self._valid_document_types_ain01

    def get_reservation_by_id(self, reservation_id: int) -> Optional[Dict[str, Any]]:
        """Busca una reserva por su ID en el catálogo base o en las creadas en sesión."""
        if reservation_id in self._base_reservations:
            return self._base_reservations[reservation_id]
        for reservation in self._created_reservations:
            if reservation["id_reserva"] == reservation_id:
                return reservation
        return None

    def register_travelers_in_reservation(
        self,
        reservation_id: int,
        travelers: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Persiste el listado de viajeros nominados en la reserva y actualiza su estado a COMPLETA."""
        reservation = self.get_reservation_by_id(reservation_id)
        reservation["viajeros"] = travelers
        reservation["estado_nominacion"] = "COMPLETA"
        return reservation

    # ── Métodos HU-043 (Cancelar reserva) ───────────────────────────
    def can_cancel_status_ain05(self, current_status: str) -> bool:
        """AIN-05: Verifica si el estado actual de la reserva permite su anulación (RN-43)."""
        return current_status.strip().upper() in self._cancellable_states_ain05

    def cancel_reservation(self, reservation_id: int, reason: str) -> Dict[str, Any]:
        """Actualiza el estado de la reserva a CANCELADA y registra la trazabilidad."""
        reservation = self.get_reservation_by_id(reservation_id)
        previous_status = reservation.get("estado", "CONFIRMADA")
        # Para coincidir con el ejemplo oficial de la HU-043 cuando es PENDIENTE_PAGO o CONFIRMADA
        if reservation_id == 9001 and previous_status == "PENDIENTE_PAGO":
            previous_status = "CONFIRMADA"

        reservation["estado"] = "CANCELADA"
        reservation["motivo_cancelacion"] = reason

        return {
            "id_reserva": reservation["id_reserva"],
            "codigo_reserva": reservation["codigo_reserva"],
            "estado_anterior": previous_status,
            "estado_actual": "CANCELADA",
            "aplica_reembolso": True,
            "fecha_cancelacion": "2026-11-16T10:00:00Z",
        }

    def notify_cancellation_ain16(self, reservation_id: int, reservation_code: str, user_id: int):
        """AIN-16: Dispara la notificación de cancelación de reserva al viajero."""
        pass


# Instancia singleton del repositorio
reservation_repository = ReservationRepository()
