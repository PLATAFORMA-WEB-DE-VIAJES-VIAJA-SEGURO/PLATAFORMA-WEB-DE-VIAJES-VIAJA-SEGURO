from datetime import date
from typing import Optional
from app.domain.paquete import (
    VALID_PACKAGE_COUNTRIES,
    VALID_PACKAGE_MUNICIPALITIES,
    VALID_PACKAGE_TYPES,
    VALID_ACTIVITY_CATEGORIES,
    VALID_PACKAGE_CURRENCIES_AIN04,
    DestinationItemOut,
    DestinationsQueryOut,
    ActivityItemOut,
    ActivitiesQueryOut,
    ActivityAvailabilityDataOut,
    ActivityAvailabilityOut,
)
from app.repositories.paquete_repository import PackageRepository


class PackageParametersError(Exception):
    pass


class PackageBusinessRuleError(Exception):
    pass


class PackageService:
    def __init__(self, repo: PackageRepository):
        self.repo = repo

    # HU-023: Consultar destinos (RN-23)
    def get_destinations(
        self,
        country: Optional[str] = None,
        municipality: Optional[str] = None,
        package_type: Optional[str] = None,
    ) -> DestinationsQueryOut:
        normalized_country = country.strip().upper() if country else None
        normalized_municipality = municipality.strip().upper() if municipality else None
        normalized_type = package_type.strip().upper() if package_type else None

        if normalized_country and normalized_country != "503" and normalized_country not in VALID_PACKAGE_COUNTRIES:
            raise PackageParametersError(
                "El código de país no es válido en el catálogo PAR-02"
            )
        if normalized_municipality and normalized_municipality != "503" and normalized_municipality not in VALID_PACKAGE_MUNICIPALITIES:
            raise PackageParametersError(
                "El código de municipio no es válido en el catálogo PAR-03"
            )
        if normalized_type and normalized_type not in VALID_PACKAGE_TYPES:
            raise PackageParametersError(
                "El tipo de paquete no es válido en el catálogo PAR-10"
            )

        destinations = self.repo.get_destinations(
            country=normalized_country,
            municipality=normalized_municipality,
            package_type=normalized_type,
        )

        if not destinations:
            raise PackageBusinessRuleError(
                "No se encontraron destinos turísticos activos para los criterios consultados"
            )

        return DestinationsQueryOut(
            mensaje="Destinos turísticos consultados exitosamente",
            data=[DestinationItemOut(**dest.to_response()) for dest in destinations],
            success=True,
        )

    # HU-026: Consultar actividades del destino (RN-26)
    def get_destination_activities(
        self,
        destination_id: str,
        start_date: date,
        end_date: Optional[date] = None,
        category: Optional[str] = None,
    ) -> ActivitiesQueryOut:
        normalized_destination = destination_id.strip().upper()
        normalized_category = category.strip().upper() if category else None

        if start_date < date.today():
            raise PackageParametersError(
                "La fecha de inicio de las actividades no puede ser anterior a la fecha actual"
            )
        if end_date and end_date < start_date:
            raise PackageParametersError(
                "La fecha de fin no puede ser anterior a la fecha de inicio"
            )
        if normalized_category and normalized_category not in VALID_ACTIVITY_CATEGORIES:
            raise PackageParametersError(
                "La categoría de actividad no es válida (TOUR_GUIADO, AVENTURA, GASTRONOMIA, ACUATICA, CULTURAL)"
            )

        destination = self.repo.get_destination_by_id(normalized_destination)
        if not destination:
            raise PackageBusinessRuleError(
                "El destino seleccionado no existe o no se encuentra activo"
            )

        activities = self.repo.get_destination_activities(
            destination_id=normalized_destination,
            category=normalized_category,
        )

        if not activities:
            raise PackageBusinessRuleError(
                "No se encontraron actividades disponibles en AEX-03 para el destino y criterios indicados"
            )

        return ActivitiesQueryOut(
            mensaje="Actividades del destino consultadas exitosamente",
            data=[ActivityItemOut(**act.to_response()) for act in activities],
            success=True,
        )

    # HU-027: Verificar cupo y tarifa de actividad (RN-27)
    def check_activity_availability_and_fare(
        self,
        activity_id: str,
        activity_date: date,
        people_count: int = 2,
    ) -> ActivityAvailabilityOut:
        if activity_date < date.today():
            raise PackageParametersError(
                "La fecha solicitada para la actividad no puede ser anterior a la fecha actual"
            )

        activity = self.repo.get_activity_by_id(activity_id)
        if not activity:
            raise PackageBusinessRuleError(
                "La actividad solicitada no existe o fue desactivada por el operador local"
            )

        if activity.currency not in VALID_PACKAGE_CURRENCIES_AIN04:
            raise PackageBusinessRuleError(
                "La moneda de la tarifa no está habilitada en el catálogo PAR-07 (AIN-04)"
            )

        # RN-27: Validar aforo suficiente en el operador local (AEX-03)
        if activity.daily_quota < people_count:
            raise PackageBusinessRuleError(
                "No hay cupos suficientes disponibles para la cantidad de personas solicitada en esta actividad"
            )

        detail = activity.calculate_availability_and_fare(
            activity_date=activity_date,
            people_count=people_count,
        )

        return ActivityAvailabilityOut(
            mensaje="Cupo y tarifa de actividad verificados exitosamente",
            data=ActivityAvailabilityDataOut(**detail),
            success=True,
        )
