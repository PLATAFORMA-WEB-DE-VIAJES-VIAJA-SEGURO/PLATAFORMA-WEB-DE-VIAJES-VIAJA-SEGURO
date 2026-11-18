from app.domain.transaccion import (
    TransactionCreate,
    TransactionResponse,
    TransactionData,
    BusinessRuleRN47Exception,
    InvalidPaymentDataException,
)
from app.repositories.transaccion_repository import TransactionRepository


class TransactionService:
    def __init__(self, repo: TransactionRepository):
        self.repo = repo

    def process_charge(self, data: TransactionCreate) -> TransactionResponse:
        reservation_code = data.reservation_code.strip().upper()
        token = data.card_token.strip()

        # ── VALIDACIÓN DE PARÁMETROS BÁSICOS Y TOKEN (400 Bad Request) ─
        if not reservation_code or not token or not token.startswith("tok_"):
            raise InvalidPaymentDataException(
                "Datos de pago incompletos o token de tarjeta inválido"
            )

        # ── REGLA DE NEGOCIO RN-47 (409 Conflict) ──────────────────────
        # 1. Consulta AIN-15a para verificar el monto exacto vigente de la reserva
        reservation = self.repo.get_reservation_ain15a(reservation_code)
        if not reservation:
            raise BusinessRuleRN47Exception(
                "El monto enviado no coincide con el saldo de la reserva o la transacción fue rechazada"
            )

        # 2. Validación de discrepancia de monto o moneda frente a AIN-15a
        expected_amount = float(reservation.get("monto_liquidado", 0.0))
        sent_amount = float(data.amount)
        expected_currency = reservation.get("moneda", "COP").upper()
        sent_currency = data.currency.strip().upper()

        # Margen mínimo de tolerancia para flotantes
        if abs(expected_amount - sent_amount) > 0.01 or expected_currency != sent_currency:
            raise BusinessRuleRN47Exception(
                "El monto enviado no coincide con el saldo de la reserva o la transacción fue rechazada"
            )

        # 3. Validación de rechazo bancario simulado por token (RN-47)
        if token.lower() in ("tok_rechazado", "tok_fondos_insuficientes", "tok_decline"):
            raise BusinessRuleRN47Exception(
                "El monto enviado no coincide con el saldo de la reserva o la transacción fue rechazada"
            )

        # ── AUTORIZACIÓN ANTE PASARELA AEX-04 ───────────────────────────
        transaction = self.repo.authorize_charge_aex04(
            reservation_code=reservation_code,
            amount=data.amount,
            currency=sent_currency,
            payment_method_code=data.payment_method_code,
            card_token=token,
        )

        # ── ACTUALIZACIÓN DE ESTADO EN AIN-15b Y NOTIFICACIÓN AIN-17 ────
        self.repo.update_reservation_status_ain15b(reservation_code, "CONFIRMADA")
        self.repo.notify_confirmation_ain17(reservation_code, transaction["id_transaccion"])

        # ── CONSTRUCCIÓN DE RESPUESTA ESTANDARIZADA (201 Created) ───────
        response_data = TransactionData(
            id_transaccion=transaction["id_transaccion"],
            referencia_pasarela=transaction["referencia_pasarela"],
            codigo_reserva=transaction["codigo_reserva"],
            monto_cobrado=float(transaction["monto_cobrado"]),
            moneda=transaction["moneda"],
            estado_transaccion=transaction["estado_transaccion"],
            estado_reserva=transaction["estado_reserva"],
        )

        return TransactionResponse(
            mensaje="Cobro aprobado y reserva confirmada exitosamente",
            data=response_data,
            success=True,
        )
