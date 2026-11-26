from datetime import datetime, timezone
from typing import Dict, Any, List
from app.domain.notificacion import MessagingProviderUnavailableException


class NotificationRepository:
    """
    Repositorio que gestiona la persistencia de notificaciones y la
    interacción simulada con el catálogo AIN-07 y el proveedor externo AEX-06.
    """

    def __init__(self):
        # Almacén de notificaciones despachadas
        self._notifications: List[Dict[str, Any]] = []
        # Secuencia de ID según criterio de HU-055 (ej: 55001)
        self._next_id = 55001

        # Catálogo AIN-07: Plantillas autorizadas y activas
        self._active_templates = {
            "CONFIRMACION_RESERVA",
            "ACTUALIZACION_CASO",
            "CANCELACION_RESERVA",
            "RECORDATORIO_PAGO",
            "BIENVENIDA",
        }

        # Catálogo AIN-07: Destinatarios con bloqueos o superación de reintentos (RN-55)
        self._blocked_recipients = {
            "bloqueado@email.com",
            "+570000000000",
            "spam@email.com",
        }

        # Interruptor de simulación de fallo del proveedor AEX-06 (para pruebas de 503)
        self.simulate_provider_failure = False

    def is_template_active(self, template: str) -> bool:
        """Valida contra el catálogo AIN-07 si la plantilla está activa."""
        return template.strip().upper() in self._active_templates

    def is_recipient_blocked(self, recipient: str) -> bool:
        """Verifica si el destinatario ha bloqueado notificaciones o superó reintentos."""
        return recipient.strip().lower() in {item.lower() for item in self._blocked_recipients}

    def dispatch_aex06(
        self,
        user_id: int,
        channel: str,
        recipient: str,
        template: str,
        variables: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Transmite la notificación al proveedor externo AEX-06 y registra la entrega.
        """
        if self.simulate_provider_failure or recipient.lower() == "fallo_proveedor@email.com":
            raise MessagingProviderUnavailableException("El proveedor externo de mensajería no responde en este momento")

        current_iso_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        record = {
            "id_notificacion": self._next_id,
            "id_usuario": user_id,
            "canal": channel,
            "destinatario": recipient,
            "plantilla": template,
            "variables": variables,
            "estado_envio": "ENVIADO",
            "fecha_envio": current_iso_date,
        }

        self._notifications.append(record)
        self._next_id += 1

        return record


# Instancia singleton para inyección en el servicio
notification_repository = NotificationRepository()
