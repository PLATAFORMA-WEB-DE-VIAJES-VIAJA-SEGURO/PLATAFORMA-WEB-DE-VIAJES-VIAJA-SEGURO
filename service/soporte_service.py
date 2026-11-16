from domain.soporte import (
    CasoSoporteCreate,
    CasoSoporteResponse,
    CasoSoporteData,
    ReglaNegocioRN51Exception,
    ValidacionParametrosException
)
from repository.soporte_repository import SoporteRepository

class SoporteService:
    def __init__(self, repo: SoporteRepository):
        self.repo = repo

    def radicar_caso(self, datos: CasoSoporteCreate) -> CasoSoporteResponse:
        # ── VALIDACIONES DE CAMPOS OBLIGATORIOS (400 Bad Request) ───────
        if not datos.tipo_caso or not datos.asunto or not datos.descripcion:
            raise ValidacionParametrosException("El tipo de caso, asunto o descripción son obligatorios")

        # ── APLICACIÓN DE LA REGLA DE NEGOCIO RN-51 (409 Conflict) ──────
        # Duplicidad de caso abierto para la misma reserva y tipo de caso
        if datos.codigo_reserva:
            if self.repo.existe_caso_abierto_identico(datos.codigo_reserva, datos.tipo_caso):
                raise ReglaNegocioRN51Exception(
                    "Ya existe un caso abierto idéntico para la misma reserva"
                )

        # ── GENERACIÓN Y RADICACIÓN DEL CASO (ESTADO ABIERTO) ───────────
        registro = self.repo.radicar_caso(
            id_usuario=datos.id_usuario,
            codigo_reserva=datos.codigo_reserva,
            tipo_caso=datos.tipo_caso,
            asunto=datos.asunto,
            descripcion=datos.descripcion
        )

        # ── INTEGRACIÓN SIMULADA CON AIN-16 / AEX-06 (NOTIFICACIÓN) ─────
        # Se envía confirmación al usuario con su número de radicado

        # ── CONSTRUCCIÓN DE RESPUESTA ESTANDARIZADA (201 Created) ───────
        data_response = CasoSoporteData(
            id_caso=registro["id_caso"],
            numero_radicado=registro["numero_radicado"],
            id_usuario=registro["id_usuario"],
            tipo_caso=registro["tipo_caso"],
            estado=registro["estado"],
            fecha_radicacion=registro["fecha_radicacion"]
        )

        return CasoSoporteResponse(
            mensaje="Caso de soporte radicado exitosamente",
            data=data_response,
            success=True
        )
