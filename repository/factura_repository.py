from typing import Dict, Any, List, Optional
import hashlib
import time


class FacturaRepository:
    """
    Repositorio que coordina la integración con AEX-05 (Facturación Electrónica)
    y AIN-17 (Notificaciones) para la emisión de facturas.
    """

    def __init__(self):
        # Facturas emitidas
        self._facturas: List[Dict[str, Any]] = []
        # Registro de transacciones ya facturadas (para evitar doble facturación RN-48)
        self._transacciones_facturadas: set = set()
        # Secuencia de IDs según ejemplo de la HU-048 (inicia en 48001)
        self._siguiente_id_factura = 48001
        # Secuencia de número de factura electrónica (FE-VS-00125)
        self._siguiente_numero_fe = 125

        # Transacciones aprobadas precargadas para pruebas directas en Swagger UI
        self._transacciones_base: Dict[int, Dict[str, Any]] = {
            47001: {"id_transaccion": 47001, "monto_cobrado": 3000000.0, "estado_transaccion": "APROBADO"},
            47002: {"id_transaccion": 47002, "monto_cobrado": 1500000.0, "estado_transaccion": "APROBADO"},
            47003: {"id_transaccion": 47003, "monto_cobrado": 3000000.0, "estado_transaccion": "APROBADO"},
            47004: {"id_transaccion": 47004, "monto_cobrado": 3000000.0, "estado_transaccion": "APROBADO"},
            47005: {"id_transaccion": 47005, "monto_cobrado": 3000000.0, "estado_transaccion": "APROBADO"},
            47000: {"id_transaccion": 47000, "monto_cobrado": 3000000.0, "estado_transaccion": "RECHAZADO"},
        }

    def obtener_transaccion(self, id_transaccion: int, transacciones_en_memoria: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Busca la transacción en las creadas durante la sesión o en el registro base precargado."""
        for t in transacciones_en_memoria:
            if t["id_transaccion"] == id_transaccion:
                return t
        return self._transacciones_base.get(id_transaccion)

    def verificar_transaccion_facturada(self, id_transaccion: int) -> bool:
        """Verifica si una transacción ya tiene una factura emitida."""
        return id_transaccion in self._transacciones_facturadas

    def emitir_factura_aex05(
        self,
        id_transaccion: int,
        total: float,
        tipo_documento_fiscal: str,
        numero_documento_fiscal: str,
        razon_social: str,
        correo_facturacion: str
    ) -> Dict[str, Any]:
        """
        AEX-05: Transmite el documento fiscal al proveedor de facturación electrónica.
        Genera el CUFE (Código Único de Factura Electrónica) y almacena el registro.
        """
        id_factura = self._siguiente_id_factura
        numero_factura = f"FE-VS-{self._siguiente_numero_fe:05d}"

        # CUFE estandarizado según ejemplo de la HU-048 para la primera factura o hash para las siguientes
        if id_factura == 48001:
            cufe = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0"
        else:
            semilla = f"{id_factura}-{id_transaccion}-{total}-{time.time()}"
            cufe = hashlib.sha1(semilla.encode()).hexdigest()[:40]

        registro = {
            "id_factura": id_factura,
            "numero_factura": numero_factura,
            "id_transaccion": id_transaccion,
            "cufe": cufe,
            "total_facturado": total,
            "estado_dian": "VALIDADA",
            "tipo_documento_fiscal": tipo_documento_fiscal,
            "numero_documento_fiscal": numero_documento_fiscal,
            "razon_social": razon_social,
            "correo_facturacion": correo_facturacion
        }

        self._facturas.append(registro)
        self._transacciones_facturadas.add(id_transaccion)
        self._siguiente_id_factura += 1
        self._siguiente_numero_fe += 1

        return registro

    def notificar_factura_ain17(self, correo: str, numero_factura: str, id_transaccion: int):
        """AIN-17: Despacha la notificación de factura emitida al correo del adquirente."""
        # Simulación de notificación no bloqueante
        pass


# Instancia singleton del repositorio
factura_repository = FacturaRepository()
