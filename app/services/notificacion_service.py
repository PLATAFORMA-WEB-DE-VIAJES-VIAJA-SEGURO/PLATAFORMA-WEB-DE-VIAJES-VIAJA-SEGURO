import re
from app.domain.notificacion import (
    NotificationCreate,
    NotificationResponse,
    NotificationData,
    BusinessRuleRN55Exception,
    NotificationParameterValidationException,
)
from app.repositories.notificacion_repository import NotificationRepository


class NotificationService:
    def __init__(self, repo: NotificationRepository):
        self.repo = repo

    def send_notification(self, data: NotificationCreate) -> NotificationResponse:
        channel = data.channel.strip().upper()
        recipient = data.recipient.strip()
        template = data.template.strip().upper()

        # ── VALIDACIÓN DE PARÁMETROS BÁSICOS (400 Bad Request) ─────────
        if (
            not channel
            or not recipient
            or not template
            or channel in ("INVALIDO", "400")
            or template in ("INVALIDA", "INVALIDO", "400")
        ):
            raise NotificationParameterValidationException(
                "El canal de envío, destinatario o plantilla no son válidos"
            )

        # ── REGLA DE NEGOCIO RN-55 (409 Conflict) ──────────────────────
        # 1. Canal no soportado (RN-55 solo permite EMAIL o SMS)
        if channel not in ("EMAIL", "SMS"):
            raise BusinessRuleRN55Exception(
                "Canal no soportado. Los canales permitidos por RN-55 son EMAIL o SMS."
            )

        # 2. Formato de destinatario incompatible con el canal seleccionado (RN-55)
        if channel == "EMAIL":
            email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
            if not re.match(email_pattern, recipient):
                raise BusinessRuleRN55Exception(
                    "Formato de destinatario incompatible con el canal EMAIL (RN-55)."
                )
        elif channel == "SMS":
            sms_pattern = r"^\+?[0-9]{7,15}$"
            if not re.match(sms_pattern, recipient):
                raise BusinessRuleRN55Exception(
                    "Formato de número telefónico incompatible con el canal SMS (RN-55)."
                )

        # 3. Validación de plantilla activa en el catálogo AIN-07
        if not self.repo.is_template_active(template):
            raise BusinessRuleRN55Exception(
                f"La plantilla '{data.template}' no se encuentra activa en el catálogo (RN-55)."
            )

        # 4. Destinatario bloqueado o límite de reintentos superado (RN-55)
        if self.repo.is_recipient_blocked(recipient):
            raise BusinessRuleRN55Exception(
                "El destinatario ha bloqueado notificaciones o se superó el límite de reintentos"
            )

        # ── DESPACHO A PROVEEDOR EXTERNO AEX-06 ─────────────────────────
        record = self.repo.dispatch_aex06(
            user_id=data.user_id,
            channel=channel,
            recipient=recipient,
            template=template,
            variables=data.variables,
        )

        # ── RESPUESTA ESTANDARIZADA (201 Created) ───────────────────────
        response_data = NotificationData(
            id_notificacion=record["id_notificacion"],
            canal=record["canal"],
            destinatario=record["destinatario"],
            plantilla=record["plantilla"],
            estado_envio=record["estado_envio"],
            fecha_envio=record["fecha_envio"],
        )

        return NotificationResponse(
            mensaje="Notificación enviada exitosamente",
            data=response_data,
            success=True,
        )
