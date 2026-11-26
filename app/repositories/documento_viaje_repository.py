import os
from datetime import date
from typing import List, Optional
from dotenv import load_dotenv
from app.domain.documento_viaje import TravelDocument


def _check_availability(document_number: str = "") -> None:
    load_dotenv(override=True)
    simulate_failure = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() == "true"
    if simulate_failure or document_number.strip().upper() == "DOC503":
        raise RuntimeError("Fallo de disponibilidad en el almacenamiento de documentos (MOD-01)")


class TravelDocumentRepository:
    def __init__(self):
        self._documents: List[TravelDocument] = []
        self._next_id: int = 8001
        self._seed()

    def _seed(self):
        initial_document = TravelDocument(
            document_id=8001,
            user_id=1,
            document_type="CC",
            document_number="1098765432",
            issuing_country="CO",
            expiration_date=date(2030, 12, 31),
            is_primary_document=True,
            status="ACTIVO",
        )
        self._documents.append(initial_document)
        self._next_id = 8002

    def get_by_user(self, user_id: int) -> List[TravelDocument]:
        _check_availability()
        return [
            doc for doc in self._documents
            if doc.user_id == user_id and doc.is_active()
        ]

    def get_active_duplicate(
        self, user_id: int, document_type: str, document_number: str
    ) -> Optional[TravelDocument]:
        _check_availability(document_number)
        return next(
            (
                doc for doc in self._documents
                if doc.user_id == user_id
                and doc.document_type == document_type
                and doc.document_number == document_number
                and doc.is_active()
            ),
            None,
        )

    def unmark_primary_documents(self, user_id: int) -> None:
        for doc in self._documents:
            if doc.user_id == user_id and doc.is_active():
                doc.is_primary_document = False

    def create(
        self,
        user_id: int,
        document_type: str,
        document_number: str,
        issuing_country: str,
        expiration_date: date,
        is_primary_document: bool,
    ) -> TravelDocument:
        _check_availability(document_number)
        if is_primary_document:
            self.unmark_primary_documents(user_id)

        new_document = TravelDocument(
            document_id=self._next_id,
            user_id=user_id,
            document_type=document_type,
            document_number=document_number,
            issuing_country=issuing_country,
            expiration_date=expiration_date,
            is_primary_document=is_primary_document,
            status="ACTIVO",
        )
        self._documents.append(new_document)
        self._next_id += 1
        return new_document


travel_document_repository = TravelDocumentRepository()
