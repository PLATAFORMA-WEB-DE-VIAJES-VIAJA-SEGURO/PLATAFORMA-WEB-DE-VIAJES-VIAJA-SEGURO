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
        canal = datos.canal.strip().upper()
        destinatario = datos.destinatario.strip()
        plantilla = datos.plantilla.strip().upper()

        # ── VALIDACIÓN DE PARÁMETROS BÁSICOS (400 Bad Request) ─────────
        if not canal or not destinatario or not plantilla:
            raise ValidacionParametrosException(
                "El canal de envío, destinatario o plantilla no son válidos"
            )

        # ── REGLA DE NEGOCIO RN-55 (409 Conflict) ──────────────────────
        # 1. Canal no soportado (RN-55 solo permite EMAIL o SMS)
        if canal not in ("EMAIL", "SMS"):
            raise ReglaNegocioRN55Exception(
                "Canal no soportado. Los canales permitidos por RN-55 son EMAIL o SMS."
            )

        # 2. Formato de destinatario incompatible con el canal seleccionado (RN-55)
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

        # 3. Validación de plantilla activa en el catálogo AIN-07
        if not self.repo.es_plantilla_activa(plantilla):
            raise ReglaNegocioRN55Exception(
                f"La plantilla '{datos.plantilla}' no se encuentra activa en el catálogo (RN-55)."
            )

        # 4. Destinatario bloqueado o límite de reintentos superado (RN-55)
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

        # ── RESPUESTA ESTANDARIZADA (201 Created) ───────────────────────
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
