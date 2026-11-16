from typing import List
from app.domain.usuario import (
    Usuario,
    UsuarioCreate,
    UsuarioDataOut,
    RegistroUsuarioOut,
    TIPOS_DOCUMENTO_VALIDOS,
    PAISES_VALIDOS,
    MUNICIPIOS_VALIDOS,
    ROLES_VALIDOS,
)
from app.repositories.usuario_repository import UsuarioRepository


class ErrorCatalogoInvalido(Exception):
    pass


class ErrorCorreoDuplicado(Exception):
    pass


class UsuarioService:
    def __init__(self, repo: UsuarioRepository):
        self.repo = repo

    def _validar_referencias(self, datos: UsuarioCreate) -> None:
        if (
            datos.tipo_documento not in TIPOS_DOCUMENTO_VALIDOS
            or datos.pais not in PAISES_VALIDOS
            or datos.municipio not in MUNICIPIOS_VALIDOS
            or (datos.rol and datos.rol not in ROLES_VALIDOS)
        ):
            raise ErrorCatalogoInvalido(
                "El tipo de documento, rol o ubicación proporcionada no son válidos"
            )

    def registrar_usuario(self, datos: UsuarioCreate) -> RegistroUsuarioOut:
        self._validar_referencias(datos)

        if self.repo.obtener_activo_por_correo(datos.correo):
            raise ErrorCorreoDuplicado(
                "El correo electrónico ya se encuentra registrado en una cuenta activa"
            )

        password_hash = Usuario.encriptar_password(datos.password)
        usuario_creado = self.repo.crear(
            nombres=datos.nombres,
            apellidos=datos.apellidos,
            correo=datos.correo,
            password_hash=password_hash,
            tipo_documento=datos.tipo_documento,
            numero_documento=datos.numero_documento,
            pais=datos.pais,
            municipio=datos.municipio,
            rol=datos.rol or "VIAJERO",
        )

        return RegistroUsuarioOut(
            mensaje="Usuario registrado exitosamente",
            data=UsuarioDataOut(**usuario_creado.to_response()),
            success=True,
        )

    def listar_usuarios(self) -> List[UsuarioDataOut]:
        return [
            UsuarioDataOut(**u.to_response())
            for u in self.repo.obtener_todos()
        ]