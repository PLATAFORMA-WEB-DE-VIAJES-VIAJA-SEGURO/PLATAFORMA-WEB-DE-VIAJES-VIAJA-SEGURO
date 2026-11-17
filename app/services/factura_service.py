import re
from app.domain.factura import (
    FacturaResponse,
    FacturaData,
    ReglaNegocioRN48Exception,
    DatosFiscalesInvalidosException
)
from app.repositories.factura_repository import FacturaRepository
from app.repositories.transaccion_repository import TransaccionRepository


class FacturaService:
    def __init__(self, repo_factura: FacturaRepository, repo_transaccion: TransaccionRepository):
        self.repo_factura = repo_factura
        self.repo_transaccion = repo_transaccion

    def emitir_factura(
        self,
        id_transaccion: int,
        tipo_documento_fiscal: str,
        numero_documento_fiscal: str,
        razon_social: str,
        correo_facturacion: str
    ) -> FacturaResponse:

        # ── VALIDACIÓN DE PARÁMETROS (400 Bad Request) ──────────────────
        tipo_doc = (tipo_documento_fiscal or "").strip().upper()
        numero_doc = (numero_documento_fiscal or "").strip()
        razon = (razon_social or "").strip()
        correo = (correo_facturacion or "").strip().lower()

        if not tipo_doc or not numero_doc or not razon or not correo:
            raise DatosFiscalesInvalidosException("Datos fiscales del adquirente incompletos")

        # Validar formato básico del correo
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", correo):
            raise DatosFiscalesInvalidosException("Datos fiscales del adquirente incompletos")

        # ── REGLA DE NEGOCIO RN-48 (409 Conflict) ──────────────────────
        # 1. Verificar que la transacción exista y esté en estado APROBADO
        transaccion = self.repo_factura.obtener_transaccion(
            id_transaccion=id_transaccion,
            transacciones_en_memoria=self.repo_transaccion._transacciones
        )

        if transaccion is None or transaccion.get("estado_transaccion") != "APROBADO":
            raise ReglaNegocioRN48Exception(
                "La transacción no está aprobada o ya cuenta con una factura emitida"
            )

        # 2. Verificar que no exista una factura previa para esta transacción
        if self.repo_factura.verificar_transaccion_facturada(id_transaccion):
            raise ReglaNegocioRN48Exception(
                "La transacción no está aprobada o ya cuenta con una factura emitida"
            )

        # ── EMISIÓN VÍA AEX-05 ─────────────────────────────────────────
        total = transaccion["monto_cobrado"]

        registro = self.repo_factura.emitir_factura_aex05(
            id_transaccion=id_transaccion,
            total=total,
            tipo_documento_fiscal=tipo_doc,
            numero_documento_fiscal=numero_doc,
            razon_social=razon,
            correo_facturacion=correo
        )

        # ── NOTIFICACIÓN VÍA AIN-17 ────────────────────────────────────
        self.repo_factura.notificar_factura_ain17(
            correo=correo,
            numero_factura=registro["numero_factura"],
            id_transaccion=id_transaccion
        )

        # ── RESPUESTA ESTANDARIZADA (201 Created) ──────────────────────
        data = FacturaData(
            id_factura=registro["id_factura"],
            numero_factura=registro["numero_factura"],
            id_transaccion=registro["id_transaccion"],
            cufe=registro["cufe"],
            total_facturado=registro["total_facturado"],
            estado_dian=registro["estado_dian"]
        )

        return FacturaResponse(
            mensaje="Factura electrónica emitida exitosamente",
            data=data,
            success=True
        )
