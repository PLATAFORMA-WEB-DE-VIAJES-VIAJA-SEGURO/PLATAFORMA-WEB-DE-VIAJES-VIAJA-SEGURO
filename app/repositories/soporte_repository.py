from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from app.domain.soporte import SupportServiceUnavailableException


class SupportRepository:
    """
    Repositorio para persistencia de casos de soporte y trazabilidad de radicados.
    """

    def __init__(self):
        self._cases: List[Dict[str, Any]] = []
        # Secuencia según el ejemplo de HU-051 (inicia en 51001)
        self._next_id = 51001
        # Consecutivo de radicado para formato PQR-YYYY-XXXX (inicia en 45 como en el ejemplo)
        self._filing_sequence = 45

        # Flag para simular falla de disponibilidad (503)
        self.simulate_availability_failure = False

    def has_identical_open_case(self, reservation_code: Optional[str], case_type: str) -> bool:
        """
        Regla RN-51: Verifica si ya existe un caso abierto con el mismo tipo de caso
        para la misma reserva.
        """
        if not reservation_code:
            return False

        normalized_reservation = reservation_code.strip().upper()
        normalized_type = case_type.strip().upper()

        for case in self._cases:
            existing_reservation = (case.get("codigo_reserva") or "").strip().upper()
            existing_type = case.get("tipo_caso", "").strip().upper()
            existing_status = case.get("estado", "").strip().upper()

            if (
                existing_reservation == normalized_reservation
                and existing_type == normalized_type
                and existing_status == "ABIERTO"
            ):
                return True

        return False

    def create_case(
        self,
        user_id: int,
        reservation_code: Optional[str],
        case_type: str,
        subject: str,
        description: str,
    ) -> Dict[str, Any]:
        """
        Registra un nuevo caso de soporte en estado ABIERTO y genera número único de radicado.
        """
        if self.simulate_availability_failure or (reservation_code and reservation_code.upper() == "FALLO-503"):
            raise SupportServiceUnavailableException("No fue posible radicar el caso de soporte en este momento")

        current_year = datetime.now(timezone.utc).year
        filing_number = f"PQR-{current_year}-{self._filing_sequence:04d}"
        filed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        new_case = {
            "id_caso": self._next_id,
            "numero_radicado": filing_number,
            "id_usuario": user_id,
            "codigo_reserva": reservation_code,
            "tipo_caso": case_type,
            "asunto": subject,
            "descripcion": description,
            "estado": "ABIERTO",
            "fecha_radicacion": filed_at,
        }

        self._cases.append(new_case)
        self._next_id += 1
        self._filing_sequence += 1

        return new_case


# Instancia singleton del repositorio
support_repository = SupportRepository()
