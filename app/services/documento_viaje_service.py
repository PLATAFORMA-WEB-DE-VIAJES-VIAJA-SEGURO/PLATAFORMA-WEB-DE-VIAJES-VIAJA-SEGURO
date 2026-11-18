from datetime import date
from typing import List
from app.domain.documento_viaje import (
    TravelDocumentCreate,
    TravelDocumentDataOut,
    TravelDocumentRegistrationOut,
    VALID_TRAVEL_DOCUMENT_TYPES,
    VALID_ISSUING_COUNTRIES,
)
from app.repositories.documento_viaje_repository import TravelDocumentRepository
from app.repositories.usuario_repository import UserRepository


class InvalidDocumentCatalogError(Exception):
    pass


class DocumentBusinessRuleError(Exception):
    pass


class TravelDocumentService:
    def __init__(self, repo: TravelDocumentRepository, user_repo: UserRepository):
        self.repo = repo
        self.user_repo = user_repo

    def _validate_catalogs_ain01(self, data: TravelDocumentCreate) -> None:
        # Consumo transversal simulado de AIN-01 (PAR-01 y PAR-02)
        if (
            data.document_type not in VALID_TRAVEL_DOCUMENT_TYPES
            or data.issuing_country not in VALID_ISSUING_COUNTRIES
        ):
            raise InvalidDocumentCatalogError(
                "El tipo de documento o país de emisión proporcionado no son válidos"
            )

    def register_document(
        self, user_id: int, data: TravelDocumentCreate
    ) -> TravelDocumentRegistrationOut:
        self._validate_catalogs_ain01(data)

        # Verifica que el usuario exista y esté activo en MOD-01
        active_users = self.user_repo.get_all()
        user = next((item for item in active_users if item.user_id == user_id), None)
        if not user:
            raise DocumentBusinessRuleError(
                "El usuario indicado no existe o no se encuentra activo"
            )

        # RN-08: Fecha de vencimiento debe ser posterior a la fecha actual
        if data.expiration_date <= date.today():
            raise DocumentBusinessRuleError(
                "El documento de viaje se encuentra vencido o expira hoy"
            )

        # RN-08: No permitir duplicar el mismo tipo y número de documento activo en el usuario
        if self.repo.get_active_duplicate(
            user_id, data.document_type, data.document_number
        ):
            raise DocumentBusinessRuleError(
                "El documento de viaje ya se encuentra registrado en el perfil del usuario"
            )

        created_doc = self.repo.create(
            user_id=user_id,
            document_type=data.document_type,
            document_number=data.document_number,
            issuing_country=data.issuing_country,
            expiration_date=data.expiration_date,
            is_primary_document=data.is_primary_document,
        )

        return TravelDocumentRegistrationOut(
            mensaje="Documento de viaje registrado exitosamente",
            data=TravelDocumentDataOut(**created_doc.to_response()),
            success=True,
        )

    def list_user_documents(self, user_id: int) -> List[TravelDocumentDataOut]:
        return [
            TravelDocumentDataOut(**doc.to_response())
            for doc in self.repo.get_by_user(user_id)
        ]
