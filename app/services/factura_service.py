import re
from app.domain.factura import (
    InvoiceResponse,
    InvoiceData,
    BusinessRuleRN48Exception,
    InvalidTaxDataException,
)
from app.repositories.factura_repository import InvoiceRepository
from app.repositories.transaccion_repository import TransactionRepository


class InvoiceService:
    def __init__(self, invoice_repo: InvoiceRepository, transaction_repo: TransactionRepository):
        self.invoice_repo = invoice_repo
        self.transaction_repo = transaction_repo

    def issue_invoice(
        self,
        transaction_id: int,
        tax_document_type: str,
        tax_document_number: str,
        company_name: str,
        billing_email: str,
    ) -> InvoiceResponse:

        # ── VALIDACIÓN DE PARÁMETROS (400 Bad Request) ──────────────────
        doc_type = (tax_document_type or "").strip().upper()
        doc_number = (tax_document_number or "").strip()
        company = (company_name or "").strip()
        email = (billing_email or "").strip().lower()

        if not doc_type or not doc_number or not company or not email:
            raise InvalidTaxDataException("Datos fiscales del adquirente incompletos")

        # Validar formato básico del correo
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            raise InvalidTaxDataException("Datos fiscales del adquirente incompletos")

        # ── REGLA DE NEGOCIO RN-48 (409 Conflict) ──────────────────────
        # 1. Verificar que la transacción exista y esté en estado APROBADO
        transaction = self.invoice_repo.get_transaction(
            transaction_id=transaction_id,
            memory_transactions=self.transaction_repo._transactions,
        )

        if transaction is None or transaction.get("estado_transaccion") != "APROBADO":
            raise BusinessRuleRN48Exception(
                "La transacción no está aprobada o ya cuenta con una factura emitida"
            )

        # 2. Verificar que no exista una factura previa para esta transacción
        if self.invoice_repo.is_transaction_invoiced(transaction_id):
            raise BusinessRuleRN48Exception(
                "La transacción no está aprobada o ya cuenta con una factura emitida"
            )

        # ── EMISIÓN VÍA AEX-05 ─────────────────────────────────────────
        total = transaction["monto_cobrado"]

        record = self.invoice_repo.issue_invoice_aex05(
            transaction_id=transaction_id,
            total=total,
            tax_document_type=doc_type,
            tax_document_number=doc_number,
            company_name=company,
            billing_email=email,
        )

        # ── NOTIFICACIÓN VÍA AIN-17 ────────────────────────────────────
        self.invoice_repo.notify_invoice_ain17(
            email=email,
            invoice_number=record["numero_factura"],
            transaction_id=transaction_id,
        )

        # ── RESPUESTA ESTANDARIZADA (201 Created) ──────────────────────
        response_data = InvoiceData(
            id_factura=record["id_factura"],
            numero_factura=record["numero_factura"],
            id_transaccion=record["id_transaccion"],
            cufe=record["cufe"],
            total_facturado=record["total_facturado"],
            estado_dian=record["estado_dian"],
        )

        return InvoiceResponse(
            mensaje="Factura electrónica emitida exitosamente",
            data=response_data,
            success=True,
        )
