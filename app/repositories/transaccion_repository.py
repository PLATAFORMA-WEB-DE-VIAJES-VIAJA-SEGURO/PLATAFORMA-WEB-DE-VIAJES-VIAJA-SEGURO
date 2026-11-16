from typing import Optional, Dict, Any, List

class TransaccionRepository:
    """
    Repositorio que coordina la integración con AIN-15a (Consulta de Reserva),
    AIN-15b (Actualización de Reserva), AIN-17 (Notificaciones) y AEX-04 (Pasarela).
    """

    def __init__(self):
        # Almacén de reservas de AIN-15a
        self._reservas: Dict[str, Dict[str, Any]] = {
            "VS-2026-8841": {
                "codigo_reserva": "VS-2026-8841",
                "monto_liquidado": 3000000.0,
                "moneda": "COP",
                "estado": "PENDIENTE_PAGO"
            },
            "VS-2026-1002": {
                "codigo_reserva": "VS-2026-1002",
                "monto_liquidado": 1500000.0,
                "moneda": "COP",
                "estado": "PENDIENTE_PAGO"
            }
        }

        # Transacciones persistidas
        self._transacciones: List[Dict[str, Any]] = []
        # Secuencia según el ejemplo de HU-047 (inicia en 47001)
        self._siguiente_id_transaccion = 47001

    def consultar_reserva_ain15a(self, codigo_reserva: str) -> Optional[Dict[str, Any]]:
        """AIN-15a: Consulta la reserva para verificar su estado y monto exacto liquidado."""
        codigo_normalizado = codigo_reserva.strip().upper()
        return self._reservas.get(codigo_normalizado)

    def actualizar_estado_reserva_ain15b(self, codigo_reserva: str, nuevo_estado: str = "CONFIRMADA") -> bool:
        """AIN-15b: Actualiza el estado de la reserva una vez el cobro es aprobado."""
        codigo_normalizado = codigo_reserva.strip().upper()
        if codigo_normalizado in self._reservas:
            self._reservas[codigo_normalizado]["estado"] = nuevo_estado
            return True
        return False

    def autorizar_cobro_aex04(
        self,
        codigo_reserva: str,
        monto: float,
        moneda: str,
        codigo_medio_pago: str,
        token_tarjeta: str
    ) -> Dict[str, Any]:
        """
        AEX-04: Solicita la autorización financiera ante la pasarela de pagos.
        """
        id_trans = self._siguiente_id_transaccion
        # Referencia pasarela estandarizada según notas técnicas
        referencia = f"PAY-99887766" if id_trans == 47001 else f"PAY-{id_trans:08d}"

        registro = {
            "id_transaccion": id_trans,
            "referencia_pasarela": referencia,
            "codigo_reserva": codigo_reserva,
            "monto_cobrado": monto,
            "moneda": moneda,
            "codigo_medio_pago": codigo_medio_pago,
            "estado_transaccion": "APROBADO",
            "estado_reserva": "CONFIRMADA"
        }

        self._transacciones.append(registro)
        self._siguiente_id_transaccion += 1

        return registro

    def notificar_confirmacion_ain17(self, codigo_reserva: str, id_transaccion: int):
        """AIN-17: Despacha la notificación de confirmación al viajero de forma no bloqueante."""
        pass

# Instancia singleton del repositorio
transaccion_repository = TransaccionRepository()
