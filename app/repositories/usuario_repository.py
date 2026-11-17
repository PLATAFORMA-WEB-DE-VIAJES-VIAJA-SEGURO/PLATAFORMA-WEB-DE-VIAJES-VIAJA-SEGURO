import os
from typing import Optional, List
from dotenv import load_dotenv
from app.domain.usuario import Usuario


def _verificar_disponibilidad(correo: str = "") -> None:
    load_dotenv(override=True)
    falla_env = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() == "true"
    if falla_env or correo.lower().strip() == "fallo_proveedor@email.com":
        raise RuntimeError("Fallo de disponibilidad en el almacenamiento de MOD-01")


class UsuarioRepository:
    def __init__(self):
        self._datos: List[Usuario] = []
        self._siguiente_id: int = 1
        self._seed()

    def _seed(self):
        usuario_activo = Usuario(
            id_usuario=1,
            nombres="Carlos",
            apellidos="Mendoza",
            correo="carlos.mendoza@viajaseguro.com",
            password_hash=Usuario.encriptar_password("Viaja2026*"),
            tipo_documento="CC",
            numero_documento="1098765432",
            pais="CO",
            municipio="BGA",
            rol="VIAJERO",
            estado="ACTIVO",
        )
        usuario_inactivo = Usuario(
            id_usuario=2,
            nombres="Andrea",
            apellidos="Rojas",
            correo="inactivo@viajaseguro.com",
            password_hash=Usuario.encriptar_password("Viaja2026*"),
            tipo_documento="CC",
            numero_documento="1098111999",
            pais="CO",
            municipio="BGA",
            rol="VIAJERO",
            estado="INACTIVO",
        )
        self._datos.extend([usuario_activo, usuario_inactivo])
        self._siguiente_id = 3

    def obtener_todos(self) -> List[Usuario]:
        _verificar_disponibilidad()
        return [u for u in self._datos if u.esta_activo()]

    def obtener_por_correo(self, correo: str) -> Optional[Usuario]:
        _verificar_disponibilidad(correo)
        correo_norm = correo.lower().strip()
        return next(
            (u for u in self._datos if u.correo == correo_norm),
            None,
        )

    def obtener_activo_por_correo(self, correo: str) -> Optional[Usuario]:
        _verificar_disponibilidad(correo)
        correo_norm = correo.lower().strip()
        return next(
            (u for u in self._datos if u.correo == correo_norm and u.esta_activo()),
            None,
        )

    def crear(
        self,
        nombres: str,
        apellidos: str,
        correo: str,
        password_hash: str,
        tipo_documento: str,
        numero_documento: str,
        pais: str,
        municipio: str,
        rol: str,
    ) -> Usuario:
        _verificar_disponibilidad(correo)
        nuevo = Usuario(
            id_usuario=self._siguiente_id,
            nombres=nombres,
            apellidos=apellidos,
            correo=correo,
            password_hash=password_hash,
            tipo_documento=tipo_documento,
            numero_documento=numero_documento,
            pais=pais,
            municipio=municipio,
            rol=rol,
            estado="ACTIVO",
        )
        self._datos.append(nuevo)
        self._siguiente_id += 1
        return nuevo


usuario_repository = UsuarioRepository()