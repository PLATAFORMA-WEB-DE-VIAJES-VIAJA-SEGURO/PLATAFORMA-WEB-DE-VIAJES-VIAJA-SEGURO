from app.domain.transaccion import (
    TransaccionCreate,
    TransaccionResponse,
    TransaccionData,
    ReglaNegocioRN47Exception,
    DatosPagoInvalidosException
)
from app.repositories.transaccion_repository import TransaccionRepository

class TransaccionService:
    def __init__(self, repo: TransaccionRepository):
        self.repo = repo

    def procesar_cobro(self, datos: TransaccionCreate) -> TransaccionResponse:
        codigo_reserva = datos.codigo_reserva.strip().upper()
        token = datos.token_tarjeta.strip()

        # ── VALIDACIÓN DE PARÁMETROS BÁSICOS Y TOKEN (400 Bad Request) ─
        if not codigo_reserva or not token or not token.startswith("tok_"):
            raise DatosPagoInvalidosException(
                "Datos de pago incompletos o token de tarjeta inválido"
            )

        # ── REGLA DE NEGOCIO RN-47 (409 Conflict) ──────────────────────
        # 1. Consulta AIN-15a para verificar el monto exacto vigente de la reserva
        reserva = self.repo.consultar_reserva_ain15a(codigo_reserva)
        if not reserva:
            raise ReglaNegocioRN47Exception(
                "El monto enviado no coincide con el saldo de la reserva o la transacción fue rechazada"
            )

        # 2. Validación de discrepancia de monto o moneda frente a AIN-15a
        monto_esperado = float(reserva.get("monto_liquidado", 0.0))
        monto_enviado = float(datos.monto)
        moneda_esperada = reserva.get("moneda", "COP").upper()
        moneda_enviada = datos.moneda.strip().upper()

        # Margen mínimo de tolerancia para flotantes
        if abs(monto_esperado - monto_enviado) > 0.01 or moneda_esperada != moneda_enviada:
            raise ReglaNegocioRN47Exception(
                "El monto enviado no coincide con el saldo de la reserva o la transacción fue rechazada"
            )

        # 3. Validación de rechazo bancario simulado por token (RN-47)
        if token.lower() in ("tok_rechazado", "tok_fondos_insuficientes", "tok_decline"):
            raise ReglaNegocioRN47Exception(
                "El monto enviado no coincide con el saldo de la reserva o la transacción fue rechazada"
            )

        # ── AUTORIZACIÓN ANTE PASARELA AEX-04 ───────────────────────────
        transaccion = self.repo.autorizar_cobro_aex04(
            codigo_reserva=codigo_reserva,
            monto=datos.monto,
            moneda=moneda_enviada,
            codigo_medio_pago=datos.codigo_medio_pago,
            token_tarjeta=token
        )

        # ── ACTUALIZACIÓN DE ESTADO EN AIN-15b Y NOTIFICACIÓN AIN-17 ────
        self.repo.actualizar_estado_reserva_ain15b(codigo_reserva, "CONFIRMADA")
        self.repo.notificar_confirmacion_ain17(codigo_reserva, transaccion["id_transaccion"])

        # ── CONSTRUCCIÓN DE RESPUESTA ESTANDARIZADA (201 Created) ───────
        data_resp = TransaccionData(
            id_transaccion=transaccion["id_transaccion"],
            referencia_pasarela=transaccion["referencia_pasarela"],
            codigo_reserva=transaccion["codigo_reserva"],
            monto_cobrado=float(transaccion["monto_cobrado"]),
            moneda=transaccion["moneda"],
            estado_transaccion=transaccion["estado_transaccion"],
            estado_reserva=transaccion["estado_reserva"]
        )

        return TransaccionResponse(
            mensaje="Cobro aprobado y reserva confirmada exitosamente",
            data=data_resp,
            success=True
        )
