from typing import Dict, Any, List, Optional
import hashlib
import time


class InvoiceRepository:
    """
    Repositorio que coordina la integración con AEX-05 (Facturación Electrónica)
    y AIN-17 (Notificaciones) para la emisión de facturas.
    """

    def __init__(self):
        # Facturas emitidas
        self._invoices: List[Dict[str, Any]] = []
        # Registro de transacciones ya facturadas (para evitar doble facturación RN-48)
        self._invoiced_transactions: set = set()
        # Secuencia de IDs según ejemplo de la HU-048 (inicia en 48001)
        self._next_invoice_id = 48001
        # Secuencia de número de factura electrónica (FE-VS-00125)
        self._next_fe_number = 125

        # Transacciones aprobadas precargadas para pruebas directas en Swagger UI
        self._base_transactions: Dict[int, Dict[str, Any]] = {
            47001: {"id_transaccion": 47001, "monto_cobrado": 3000000.0, "estado_transaccion": "APROBADO"},
            47002: {"id_transaccion": 47002, "monto_cobrado": 1500000.0, "estado_transaccion": "APROBADO"},
            47003: {"id_transaccion": 47003, "monto_cobrado": 3000000.0, "estado_transaccion": "APROBADO"},
            47004: {"id_transaccion": 47004, "monto_cobrado": 3000000.0, "estado_transaccion": "APROBADO"},
            47005: {"id_transaccion": 47005, "monto_cobrado": 3000000.0, "estado_transaccion": "APROBADO"},
            47000: {"id_transaccion": 47000, "monto_cobrado": 3000000.0, "estado_transaccion": "RECHAZADO"},
        }

    def get_transaction(self, transaction_id: int, memory_transactions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Busca la transacción en las creadas durante la sesión o en el registro base precargado."""
        for tx in memory_transactions:
            if tx["id_transaccion"] == transaction_id:
                return tx
        return self._base_transactions.get(transaction_id)

    def is_transaction_invoiced(self, transaction_id: int) -> bool:
        """Verifica si una transacción ya tiene una factura emitida."""
        return transaction_id in self._invoiced_transactions

    def issue_invoice_aex05(
        self,
        transaction_id: int,
        total: float,
        tax_document_type: str,
        tax_document_number: str,
        company_name: str,
        billing_email: str,
    ) -> Dict[str, Any]:
        """
        AEX-05: Transmite el documento fiscal al proveedor de facturación electrónica.
        Genera el CUFE (Código Único de Factura Electrónica) y almacena el registro.
        """
        invoice_id = self._next_invoice_id
        invoice_number = f"FE-VS-{self._next_fe_number:05d}"

        # CUFE estandarizado según ejemplo de la HU-048 para la primera factura o hash para las siguientes
        if invoice_id == 48001:
            cufe = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0"
        else:
            seed = f"{invoice_id}-{transaction_id}-{total}-{time.time()}"
            cufe = hashlib.sha1(seed.encode()).hexdigest()[:40]

        record = {
            "id_factura": invoice_id,
            "numero_factura": invoice_number,
            "id_transaccion": transaction_id,
            "cufe": cufe,
            "total_facturado": total,
            "estado_dian": "VALIDADA",
            "tipo_documento_fiscal": tax_document_type,
            "numero_documento_fiscal": tax_document_number,
            "razon_social": company_name,
            "correo_facturacion": billing_email,
        }

        self._invoices.append(record)
        self._invoiced_transactions.add(transaction_id)
        self._next_invoice_id += 1
        self._next_fe_number += 1

        return record

    def notify_invoice_ain17(self, email: str, invoice_number: str, transaction_id: int):
        """AIN-17: Despacha la notificación de factura emitida al correo del adquirente."""
        # Simulación de notificación no bloqueante
        pass


# Instancia singleton del repositorio
invoice_repository = InvoiceRepository()
