from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from domain.notificacion import ProveedorNoDisponibleException

class NotificacionRepository:
    """
    Repositorio que gestiona la persistencia de notificaciones y la
    interacción simulada con el catálogo AIN-07 y el proveedor externo AEX-06.
    """

    def __init__(self):
        # Almacén de notificaciones despachadas
        self._notificaciones: List[Dict[str, Any]] = []
        # Secuencia de ID según criterio de HU-055 (ej: 55001)
        self._siguiente_id = 55001

        # Catálogo AIN-07: Plantillas autorizadas y activas
        self._plantillas_activas = {
            "CONFIRMACION_RESERVA",
            "ACTUALIZACION_CASO",
            "CANCELACION_RESERVA",
            "RECORDATORIO_PAGO",
            "BIENVENIDA"
        }

        # Catálogo AIN-07: Destinatarios con bloqueos o superación de reintentos (RN-55)
        self._destinatarios_bloqueados = {
            "bloqueado@email.com",
            "+570000000000",
            "spam@email.com"
        }

        # Interruptor de simulación de fallo del proveedor AEX-06 (para pruebas de 503)
        self.simular_falla_proveedor = False

    def es_plantilla_activa(self, plantilla: str) -> bool:
        """Valida contra el catálogo AIN-07 si la plantilla está activa."""
        return plantilla.strip().upper() in self._plantillas_activas

    def esta_bloqueado(self, destinatario: str) -> bool:
        """Verifica si el destinatario ha bloqueado notificaciones o superó reintentos."""
        return destinatario.strip().lower() in {d.lower() for d in self._destinatarios_bloqueados}

    def despachar_aex06(
        self,
        id_usuario: int,
        canal: str,
        destinatario: str,
        plantilla: str,
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transmite la notificación al proveedor externo AEX-06 y registra la entrega.
        """
        if self.simular_falla_proveedor or destinatario.lower() == "fallo_proveedor@email.com":
            raise ProveedorNoDisponibleException("El proveedor externo de mensajería no responde en este momento")

        fecha_actual_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        registro = {
            "id_notificacion": self._siguiente_id,
            "id_usuario": id_usuario,
            "canal": canal,
            "destinatario": destinatario,
            "plantilla": plantilla,
            "variables": variables,
            "estado_envio": "ENVIADO",
            "fecha_envio": fecha_actual_iso
        }

        self._notificaciones.append(registro)
        self._siguiente_id += 1

        return registro

# Instancia singleton para inyección en el servicio
notificacion_repository = NotificacionRepository()
