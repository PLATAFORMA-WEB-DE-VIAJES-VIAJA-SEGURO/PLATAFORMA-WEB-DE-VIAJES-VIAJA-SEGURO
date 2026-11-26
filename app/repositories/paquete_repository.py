import os
from typing import List, Optional
from dotenv import load_dotenv
from app.domain.paquete import Destination, Activity


def _check_package_availability(control_value: str = "") -> None:
    load_dotenv(override=True)
    simulate_failure = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() == "true"
    if simulate_failure or control_value.strip().upper() in {"503", "DST-503", "ACT-503"}:
        raise RuntimeError("Fallo de conexión con el servicio externo AEX-03 / catálogo de paquetes")


class PackageRepository:
    def __init__(self):
        self._destinations: List[Destination] = []
        self._activities: List[Activity] = []
        self._seed()

    def _seed(self):
        self._destinations = [
            Destination(
                destination_id="DST-301",
                name="Cartagena Colonial y Playas",
                country="CO",
                municipality="CTG",
                package_type="PLAYA",
                description="Recorrido por la ciudad amurallada, Islas del Rosario y gastronomía caribeña",
                recommended_season="Diciembre a Abril",
                price_from=1250000.0,
                currency="COP",
            ),
            Destination(
                destination_id="DST-302",
                name="Medellín Innovación y Cultura",
                country="CO",
                municipality="MDE",
                package_type="CULTURAL",
                description="Tour Comuna 13, Guatapé y Piedra del Peñol",
                recommended_season="Todo el año",
                price_from=890000.0,
                currency="COP",
            ),
            Destination(
                destination_id="DST-303",
                name="Bogotá Histórica y Monserrate",
                country="CO",
                municipality="BOG",
                package_type="CULTURAL",
                description="Visita a La Candelaria, Museo del Oro y Cerro de Monserrate",
                recommended_season="Enero a Marzo",
                price_from=640000.0,
                currency="COP",
            ),
            Destination(
                destination_id="DST-304",
                name="Miami Beach y Parques",
                country="US",
                municipality="MIA",
                package_type="TODO_INCLUIDO",
                description="Estancia frente al mar con paseos por Everglades y compras",
                recommended_season="Noviembre a Mayo",
                price_from=3400000.0,
                currency="COP",
            ),
        ]

        self._activities = [
            Activity(
                activity_id="ACT-401",
                destination_id="DST-301",
                name="Pasadía Islas del Rosario y Playa Blanca",
                category="ACUATICA",
                duration_hours=8,
                meeting_point="Muelle de la Bodeguita - Puerta 4",
                includes_guide=True,
                daily_quota=20,
                price_per_person=260000.0,
                currency="COP",
            ),
            Activity(
                activity_id="ACT-402",
                destination_id="DST-301",
                name="Caminata Histórica Ciudad Amurallada y Castillo San Felipe",
                category="CULTURAL",
                duration_hours=4,
                meeting_point="Torre del Reloj",
                includes_guide=True,
                daily_quota=15,
                price_per_person=140000.0,
                currency="COP",
            ),
            Activity(
                activity_id="ACT-403",
                destination_id="DST-302",
                name="Excursión Piedra del Peñol y Guatapé",
                category="TOUR_GUIADO",
                duration_hours=10,
                meeting_point="Estación Poblado",
                includes_guide=True,
                daily_quota=12,
                price_per_person=195000.0,
                currency="COP",
            ),
            Activity(
                activity_id="ACT-404",
                destination_id="DST-303",
                name="Recorrido Museo del Oro y Monserrate",
                category="CULTURAL",
                duration_hours=5,
                meeting_point="Parque Santander",
                includes_guide=True,
                daily_quota=2,
                price_per_person=130000.0,
                currency="COP",
            ),
        ]

    # HU-023: Consultar destinos disponibles con filtros opcionales
    def get_destinations(
        self,
        country: Optional[str] = None,
        municipality: Optional[str] = None,
        package_type: Optional[str] = None,
    ) -> List[Destination]:
        control_value = country or municipality or package_type or ""
        _check_package_availability(control_value)
        return [
            dest for dest in self._destinations
            if dest.active
            and (country is None or dest.country == country)
            and (municipality is None or dest.municipality == municipality)
            and (package_type is None or dest.package_type == package_type)
        ]

    # HU-026: Obtener destino por ID
    def get_destination_by_id(self, destination_id: str) -> Optional[Destination]:
        _check_package_availability(destination_id)
        return next(
            (dest for dest in self._destinations if dest.destination_id == destination_id.strip().upper() and dest.active),
            None,
        )

    # HU-026: Consultar actividades asociadas a un destino en AEX-03
    def get_destination_activities(
        self,
        destination_id: str,
        category: Optional[str] = None,
    ) -> List[Activity]:
        _check_package_availability(destination_id)
        return [
            act for act in self._activities
            if act.active
            and act.destination_id == destination_id.strip().upper()
            and act.daily_quota > 0
            and (category is None or act.category == category)
        ]

    # HU-027: Obtener actividad por ID en AEX-03
    def get_activity_by_id(self, activity_id: str) -> Optional[Activity]:
        _check_package_availability(activity_id)
        return next(
            (act for act in self._activities if act.activity_id == activity_id.strip().upper() and act.active),
            None,
        )


package_repository = PackageRepository()
