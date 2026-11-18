import os
from typing import Optional, List
from dotenv import load_dotenv
from app.domain.usuario import User


def _check_availability(email: str = "") -> None:
    load_dotenv(override=True)
    simulate_failure = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() == "true"
    if simulate_failure or email.lower().strip() == "fallo_proveedor@email.com":
        raise RuntimeError("Fallo de disponibilidad en el almacenamiento de MOD-01")


class UserRepository:
    def __init__(self):
        self._users: List[User] = []
        self._next_id: int = 1
        self._seed()

    def _seed(self):
        active_user = User(
            user_id=1,
            first_name="Carlos",
            last_name="Mendoza",
            email="carlos.mendoza@viajaseguro.com",
            password_hash=User.hash_password("Viaja2026*"),
            document_type="CC",
            document_number="1098765432",
            country="CO",
            municipality="BGA",
            role="VIAJERO",
            status="ACTIVO",
        )
        inactive_user = User(
            user_id=2,
            first_name="Andrea",
            last_name="Rojas",
            email="inactivo@viajaseguro.com",
            password_hash=User.hash_password("Viaja2026*"),
            document_type="CC",
            document_number="1098111999",
            country="CO",
            municipality="BGA",
            role="VIAJERO",
            status="INACTIVO",
        )
        self._users.extend([active_user, inactive_user])
        self._next_id = 3

    def get_all(self) -> List[User]:
        _check_availability()
        return [user for user in self._users if user.is_active()]

    def get_by_email(self, email: str) -> Optional[User]:
        _check_availability(email)
        normalized_email = email.lower().strip()
        return next(
            (user for user in self._users if user.email == normalized_email),
            None,
        )

    def get_active_by_email(self, email: str) -> Optional[User]:
        _check_availability(email)
        normalized_email = email.lower().strip()
        return next(
            (user for user in self._users if user.email == normalized_email and user.is_active()),
            None,
        )

    def create(
        self,
        first_name: str,
        last_name: str,
        email: str,
        password_hash: str,
        document_type: str,
        document_number: str,
        country: str,
        municipality: str,
        role: str,
    ) -> User:
        _check_availability(email)
        new_user = User(
            user_id=self._next_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=password_hash,
            document_type=document_type,
            document_number=document_number,
            country=country,
            municipality=municipality,
            role=role,
            status="ACTIVO",
        )
        self._users.append(new_user)
        self._next_id += 1
        return new_user


user_repository = UserRepository()
