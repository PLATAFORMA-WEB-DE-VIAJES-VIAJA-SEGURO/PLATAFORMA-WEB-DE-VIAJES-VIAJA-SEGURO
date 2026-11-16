from datetime import date
from typing import List
from app.domain.documento_viaje import (
    DocumentoViajeCreate,
    DocumentoViajeDataOut,
    RegistroDocumentoViajeOut,
    TIPOS_DOCUMENTO_VIAJE_VALIDOS,
    PAISES_EMISION_VALIDOS,
)
from app.repositories.documento_viaje_repository import DocumentoViajeRepository
from app.repositories.usuario_repository import UsuarioRepository


class ErrorCatalogoDocumentoInvalido(Exception):
    pass


class ErrorReglaNegocioDocumento(Exception):
    pass


class DocumentoViajeService:
    def __init__(self, repo: DocumentoViajeRepository, usuario_repo: UsuarioRepository):
        self.repo = repo
        self.usuario_repo = usuario_repo

    def _validar_catalogos_ain01(self, datos: DocumentoViajeCreate) -> None:
        # Consumo transversal simulado de AIN-01 (PAR-01 y PAR-02)
        if (
            datos.tipo_documento not in TIPOS_DOCUMENTO_VIAJE_VALIDOS
            or datos.pais_emision not in PAISES_EMISION_VALIDOS
        ):
            raise ErrorCatalogoDocumentoInvalido(
                "El tipo de documento o país de emisión proporcionado no son válidos"
            )

    def registrar_documento(
        self, id_usuario: int, datos: DocumentoViajeCreate
    ) -> RegistroDocumentoViajeOut:
        self._validar_catalogos_ain01(datos)

        # Verifica que el usuario exista y esté activo en MOD-01
        usuarios_activos = self.usuario_repo.obtener_todos()
        usuario = next((u for u in usuarios_activos if u.id_usuario == id_usuario), None)
        if not usuario:
            raise ErrorReglaNegocioDocumento(
                "El usuario indicado no existe o no se encuentra activo"
            )

        # RN-08: Fecha de vencimiento debe ser posterior a la fecha actual
        if datos.fecha_vencimiento <= date.today():
            raise ErrorReglaNegocioDocumento(
                "El documento de viaje se encuentra vencido o expira hoy"
            )

        # RN-08: No permitir duplicar el mismo tipo y número de documento activo en el usuario
        if self.repo.obtener_duplicado_activo(
            id_usuario, datos.tipo_documento, datos.numero_documento
        ):
            raise ErrorReglaNegocioDocumento(
                "El documento de viaje ya se encuentra registrado en el perfil del usuario"
            )

        creado = self.repo.crear(
            id_usuario=id_usuario,
            tipo_documento=datos.tipo_documento,
            numero_documento=datos.numero_documento,
            pais_emision=datos.pais_emision,
            fecha_vencimiento=datos.fecha_vencimiento,
            es_documento_principal=datos.es_documento_principal,
        )

        return RegistroDocumentoViajeOut(
            mensaje="Documento de viaje registrado exitosamente",
            data=DocumentoViajeDataOut(**creado.to_response()),
            success=True,
        )

    def listar_documentos_usuario(self, id_usuario: int) -> List[DocumentoViajeDataOut]:
        return [
            DocumentoViajeDataOut(**d.to_response())
            for d in self.repo.obtener_por_usuario(id_usuario)
        ]
    