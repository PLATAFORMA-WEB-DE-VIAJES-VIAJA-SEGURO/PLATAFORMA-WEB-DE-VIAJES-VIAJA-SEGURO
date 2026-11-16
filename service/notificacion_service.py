import re
from domain.notificacion import (
    NotificacionCreate,
    NotificacionResponse,
    NotificacionData,
    ReglaNegocioRN55Exception,
    ValidacionParametrosException
)
from repository.notificacion_repository import NotificacionRepository

class NotificacionService:
    def __init__(self, repo: NotificacionRepository):
        self.repo = repo

    def enviar_notificacion(self, datos: NotificacionCreate) -> NotificacionResponse:
        canal = datos.canal.upper()
        destinatario = datos.destinatario.strip()
        plantilla = datos.plantilla.strip().upper()

        # ── REGLA DE NEGOCIO RN-55 ──────────────────────────────────────
        # 1. Validación de Canal Soportado (EMAIL o SMS)
        if canal not in ("EMAIL", "SMS"):
            raise ReglaNegocioRN55Exception("Canal no soportado. Los canales permitidos por RN-55 son EMAIL o SMS.")

        # 2. Validación de Formato de Destinatario Compatible con el Canal
        if canal == "EMAIL":
            patron_email = r"^[\w\.-]+@[\w\.-]+\.\w+$"
            if not re.match(patron_email, destinatario):
                raise ReglaNegocioRN55Exception(
                    "Formato de destinatario incompatible con el canal EMAIL (RN-55)."
                )
        elif canal == "SMS":
            patron_sms = r"^\+?[0-9]{7,15}$"
            if not re.match(patron_sms, destinatario):
                raise ReglaNegocioRN55Exception(
                    "Formato de número telefónico incompatible con el canal SMS (RN-55)."
                )

        # 3. Validación de Plantilla Activa en Catálogo AIN-07
        if not self.repo.es_plantilla_activa(plantilla):
            raise ReglaNegocioRN55Exception(
                f"La plantilla '{datos.plantilla}' no se encuentra activa en el catálogo (RN-55)."
            )

        # 4. Validación de Bloqueo de Destinatario o Límite de Reintentos
        if self.repo.esta_bloqueado(destinatario):
            raise ReglaNegocioRN55Exception(
                "El destinatario ha bloqueado notificaciones o se superó el límite de reintentos"
            )

        # ── DESPACHO A PROVEEDOR EXTERNO AEX-06 ─────────────────────────
        registro = self.repo.despachar_aex06(
            id_usuario=datos.id_usuario,
            canal=canal,
            destinatario=destinatario,
            plantilla=plantilla,
            variables=datos.variables
        )

        # ── ESTRUCTURACIÓN DE RESPUESTA ESTANDARIZADA (201 Created) ────
        data_response = NotificacionData(
            id_notificacion=registro["id_notificacion"],
            canal=registro["canal"],
            destinatario=registro["destinatario"],
            plantilla=registro["plantilla"],
            estado_envio=registro["estado_envio"],
            fecha_envio=registro["fecha_envio"]
        )

        return NotificacionResponse(
            mensaje="Notificación enviada exitosamente",
            data=data_response,
            success=True
        )
