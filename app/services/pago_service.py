import re
from app.domain.pago import (
    PaymentMethodsResponse,
    PaymentMethodsData,
    PaymentMethodItem,
    UnsupportedCurrencyException,
    BusinessRuleRN45Exception,
)
from app.repositories.pago_repository import PaymentRepository


class PaymentService:
    def __init__(self, repo: PaymentRepository):
        self.repo = repo

    def get_payment_methods(self, currency: str = "COP") -> PaymentMethodsResponse:
        cleaned_currency = (currency or "").strip().upper()

        # ── VALIDACIÓN DE FORMATO DE PARÁMETROS (400 Bad Request) ──────
        # El código de moneda debe ser un código alfabético de 3 letras (formato ISO 4217)
        if not cleaned_currency or not re.match(r"^[A-Z]{3}$", cleaned_currency):
            raise UnsupportedCurrencyException("Código de moneda no soportado")

        # ── REGLA DE NEGOCIO RN-45 (409 Conflict) ──────────────────────
        # Solo se exponen medios activos en el catálogo PAR-06 / AIN-06 y pasarela AEX-04.
        # Si la moneda no tiene medios habilitados (como XXX, EUR, etc.), se rechaza por RN-45.
        raw_methods = self.repo.get_active_methods(cleaned_currency)

        if not raw_methods:
            raise BusinessRuleRN45Exception(
                "No hay medios de pago habilitados temporalmente para esta moneda"
            )

        # ── CONSTRUCCIÓN DE RESPUESTA ESTANDARIZADA (200 OK) ────────────
        items = [
            PaymentMethodItem(
                codigo=method["codigo"],
                nombre=method["nombre"],
                tipo=method["tipo"],
                activo=method["activo"],
            )
            for method in raw_methods
        ]

        response_data = PaymentMethodsData(
            moneda=cleaned_currency,
            medios_pago=items,
        )

        return PaymentMethodsResponse(
            mensaje="Medios de pago consultados exitosamente",
            data=response_data,
            success=True,
        )
