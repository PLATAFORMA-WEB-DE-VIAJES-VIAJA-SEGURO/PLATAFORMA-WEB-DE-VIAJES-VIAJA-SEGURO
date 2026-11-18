from app.domain.soporte import (
    SupportCaseCreate,
    SupportCaseResponse,
    SupportCaseData,
    BusinessRuleRN51Exception,
    SupportParameterValidationException,
)
from app.repositories.soporte_repository import SupportRepository


class SupportService:
    def __init__(self, repo: SupportRepository):
        self.repo = repo

    def file_case(self, data: SupportCaseCreate) -> SupportCaseResponse:
        # ── VALIDACIONES DE CAMPOS OBLIGATORIOS (400 Bad Request) ───────
        if not data.case_type or not data.subject or not data.description:
            raise SupportParameterValidationException("El tipo de caso, asunto o descripción son obligatorios")

        # ── APLICACIÓN DE LA REGLA DE NEGOCIO RN-51 (409 Conflict) ──────
        # Duplicidad de caso abierto para la misma reserva y tipo de caso
        if data.reservation_code:
            if self.repo.has_identical_open_case(data.reservation_code, data.case_type):
                raise BusinessRuleRN51Exception(
                    "Ya existe un caso abierto idéntico para la misma reserva"
                )

        # ── GENERACIÓN Y RADICACIÓN DEL CASO (ESTADO ABIERTO) ───────────
        record = self.repo.create_case(
            user_id=data.user_id,
            reservation_code=data.reservation_code,
            case_type=data.case_type,
            subject=data.subject,
            description=data.description,
        )

        # ── CONSTRUCCIÓN DE RESPUESTA ESTANDARIZADA (201 Created) ───────
        response_data = SupportCaseData(
            id_caso=record["id_caso"],
            numero_radicado=record["numero_radicado"],
            id_usuario=record["id_usuario"],
            tipo_caso=record["tipo_caso"],
            estado=record["estado"],
            fecha_radicacion=record["fecha_radicacion"],
        )

        return SupportCaseResponse(
            mensaje="Caso de soporte radicado exitosamente",
            data=response_data,
            success=True,
        )
