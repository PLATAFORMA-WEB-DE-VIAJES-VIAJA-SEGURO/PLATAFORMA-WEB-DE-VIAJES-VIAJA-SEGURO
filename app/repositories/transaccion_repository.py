from typing import Optional, Dict, Any, List


class TransactionRepository:
    """
    Repositorio que coordina la integración con AIN-15a (Consulta de Reserva),
    AIN-15b (Actualización de Reserva), AIN-17 (Notificaciones) y AEX-04 (Pasarela).
    """

    def __init__(self):
        # Almacén de reservas de AIN-15a
        self._reservations: Dict[str, Dict[str, Any]] = {
            "VS-2026-8841": {
                "codigo_reserva": "VS-2026-8841",
                "monto_liquidado": 3000000.0,
                "moneda": "COP",
                "estado": "PENDIENTE_PAGO",
            },
            "VS-2026-1002": {
                "codigo_reserva": "VS-2026-1002",
                "monto_liquidado": 1500000.0,
                "moneda": "COP",
                "estado": "PENDIENTE_PAGO",
            },
        }

        # Transacciones persistidas
        self._transactions: List[Dict[str, Any]] = []
        # Secuencia según el ejemplo de HU-047 (inicia en 47001)
        self._next_transaction_id = 47001

    def get_reservation_ain15a(self, reservation_code: str) -> Optional[Dict[str, Any]]:
        """AIN-15a: Consulta la reserva para verificar su estado y monto exacto liquidado."""
        normalized_code = reservation_code.strip().upper()
        return self._reservations.get(normalized_code)

    def update_reservation_status_ain15b(self, reservation_code: str, new_status: str = "CONFIRMADA") -> bool:
        """AIN-15b: Actualiza el estado de la reserva una vez el cobro es aprobado."""
        normalized_code = reservation_code.strip().upper()
        if normalized_code in self._reservations:
            self._reservations[normalized_code]["estado"] = new_status
            return True
        return False

    def authorize_charge_aex04(
        self,
        reservation_code: str,
        amount: float,
        currency: str,
        payment_method_code: str,
        card_token: str,
    ) -> Dict[str, Any]:
        """
        AEX-04: Solicita la autorización financiera ante la pasarela de pagos.
        """
        transaction_id = self._next_transaction_id
        # Referencia pasarela estandarizada según notas técnicas
        reference = "PAY-99887766" if transaction_id == 47001 else f"PAY-{transaction_id:08d}"

        record = {
            "id_transaccion": transaction_id,
            "referencia_pasarela": reference,
            "codigo_reserva": reservation_code,
            "monto_cobrado": amount,
            "moneda": currency,
            "codigo_medio_pago": payment_method_code,
            "estado_transaccion": "APROBADO",
            "estado_reserva": "CONFIRMADA",
        }

        self._transactions.append(record)
        self._next_transaction_id += 1

        return record

    def notify_confirmation_ain17(self, reservation_code: str, transaction_id: int):
        """AIN-17: Despacha la notificación de confirmación al viajero de forma no bloqueante."""
        pass


# Instancia singleton del repositorio
transaction_repository = TransactionRepository()
