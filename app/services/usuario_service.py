from typing import List
from app.domain.usuario import (
    Usuario,
    UsuarioCreate,
    UsuarioDataOut,
    RegistroUsuarioOut,
    UsuarioLogin,
    LoginDataOut,
    LoginUsuarioOut,
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


class ErrorCredencialesInvalidas(Exception):
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

    def iniciar_sesion(self, datos: UsuarioLogin) -> LoginUsuarioOut:
        usuario = self.repo.obtener_por_correo(datos.correo)

        # RN-02: Verifica existencia, estado ACTIVO y coincidencia de hash
        if not usuario or not usuario.esta_activo() or not usuario.verificar_password(datos.password):
            raise ErrorCredencialesInvalidas(
                "Credenciales inválidas o cuenta inactiva"
            )

        token = Usuario.generar_token_sesion()

        return LoginUsuarioOut(
            mensaje="Inicio de sesión exitoso",
            data=LoginDataOut(
                token=token,
                tipo_token="Bearer",
                id_usuario=usuario.id_usuario,
                nombres=usuario.nombres,
                apellidos=usuario.apellidos,
                correo=usuario.correo,
                rol=usuario.rol,
            ),
            success=True,
        )

    def listar_usuarios(self) -> List[UsuarioDataOut]:
        return [
            UsuarioDataOut(**u.to_response())
            for u in self.repo.obtener_todos()
        ]