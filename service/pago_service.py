import re
from domain.pago import (
    MediosPagoResponse,
    MediosPagoData,
    MedioPagoItem,
    MonedaNoSoportadaException,
    ReglaNegocioRN45Exception
)
from repository.pago_repository import PagoRepository

class PagoService:
    def __init__(self, repo: PagoRepository):
        self.repo = repo

    def consultar_medios_pago(self, moneda: str = "COP") -> MediosPagoResponse:
        moneda_limpia = (moneda or "").strip().upper()

        # ── VALIDACIÓN DE FORMATO DE PARÁMETROS (400 Bad Request) ──────
        # El código de moneda debe ser un código alfabético de 3 letras (formato ISO 4217)
        if not moneda_limpia or not re.match(r"^[A-Z]{3}$", moneda_limpia):
            raise MonedaNoSoportadaException("Código de moneda no soportado")

        # ── REGLA DE NEGOCIO RN-45 (409 Conflict) ──────────────────────
        # Solo se exponen medios activos en el catálogo PAR-06 / AIN-06 y pasarela AEX-04.
        # Si la moneda no tiene medios habilitados (como XXX, EUR, etc.), se rechaza por RN-45.
        medios_raw = self.repo.consultar_medios_activos(moneda_limpia)

        if not medios_raw:
            raise ReglaNegocioRN45Exception(
                "No hay medios de pago habilitados temporalmente para esta moneda"
            )

        # ── CONSTRUCCIÓN DE RESPUESTA ESTANDARIZADA (200 OK) ────────────
        items = [
            MedioPagoItem(
                codigo=m["codigo"],
                nombre=m["nombre"],
                tipo=m["tipo"],
                activo=m["activo"]
            )
            for m in medios_raw
        ]

        data = MediosPagoData(
            moneda=moneda_limpia,
            medios_pago=items
        )

        return MediosPagoResponse(
            mensaje="Medios de pago consultados exitosamente",
            data=data,
            success=True
        )
