from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from app.domain.soporte import ServicioNoDisponibleException

class SoporteRepository:
    """
    Repositorio para persistencia de casos de soporte y trazabilidad de radicados.
    """

    def __init__(self):
        self._casos: List[Dict[str, Any]] = []
        # Secuencia según el ejemplo de HU-051 (inicia en 51001)
        self._siguiente_id = 51001
        # Consecutivo de radicado para formato PQR-YYYY-XXXX (inicia en 45 como en el ejemplo)
        self._consecutivo_radicado = 45

        # Flag para simular falla de disponibilidad (503)
        self.simular_falla_disponibilidad = False

    def existe_caso_abierto_identico(self, codigo_reserva: Optional[str], tipo_caso: str) -> bool:
        """
        Regla RN-51: Verifica si ya existe un caso abierto con el mismo tipo de caso
        para la misma reserva.
        """
        if not codigo_reserva:
            return False

        codigo_reserva_normalizado = codigo_reserva.strip().upper()
        tipo_caso_normalizado = tipo_caso.strip().upper()

        for caso in self._casos:
            reserva_existente = (caso.get("codigo_reserva") or "").strip().upper()
            tipo_existente = caso.get("tipo_caso", "").strip().upper()
            estado_existente = caso.get("estado", "").strip().upper()

            if (
                reserva_existente == codigo_reserva_normalizado
                and tipo_existente == tipo_caso_normalizado
                and estado_existente == "ABIERTO"
            ):
                return True

        return False

    def radicar_caso(
        self,
        id_usuario: int,
        codigo_reserva: Optional[str],
        tipo_caso: str,
        asunto: str,
        descripcion: str
    ) -> Dict[str, Any]:
        """
        Registra un nuevo caso de soporte en estado ABIERTO y genera número único de radicado.
        """
        if self.simular_falla_disponibilidad or (codigo_reserva and codigo_reserva.upper() == "FALLO-503"):
            raise ServicioNoDisponibleException("No fue posible radicar el caso de soporte en este momento")

        anio_actual = datetime.now(timezone.utc).year
        numero_radicado = f"PQR-{anio_actual}-{self._consecutivo_radicado:04d}"
        fecha_radicacion = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        nuevo_caso = {
            "id_caso": self._siguiente_id,
            "numero_radicado": numero_radicado,
            "id_usuario": id_usuario,
            "codigo_reserva": codigo_reserva,
            "tipo_caso": tipo_caso,
            "asunto": asunto,
            "descripcion": descripcion,
            "estado": "ABIERTO",
            "fecha_radicacion": fecha_radicacion
        }

        self._casos.append(nuevo_caso)
        self._siguiente_id += 1
        self._consecutivo_radicado += 1

        return nuevo_caso

# Instancia singleton del repositorio
soporte_repository = SoporteRepository()
