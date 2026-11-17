import os
from datetime import date
from typing import List, Optional
from dotenv import load_dotenv
from app.domain.documento_viaje import DocumentoViaje


def _verificar_disponibilidad(numero_documento: str = "") -> None:
    load_dotenv(override=True)
    falla_env = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() == "true"
    if falla_env or numero_documento.strip().upper() == "DOC503":
        raise RuntimeError("Fallo de disponibilidad en el almacenamiento de documentos (MOD-01)")


class DocumentoViajeRepository:
    def __init__(self):
        self._datos: List[DocumentoViaje] = []
        self._siguiente_id: int = 8001
        self._seed()

    def _seed(self):
        doc_inicial = DocumentoViaje(
            id_documento=8001,
            id_usuario=1,
            tipo_documento="CC",
            numero_documento="1098765432",
            pais_emision="CO",
            fecha_vencimiento=date(2030, 12, 31),
            es_documento_principal=True,
            estado="ACTIVO",
        )
        self._datos.append(doc_inicial)
        self._siguiente_id = 8002

    def obtener_por_usuario(self, id_usuario: int) -> List[DocumentoViaje]:
        _verificar_disponibilidad()
        return [
            d for d in self._datos
            if d.id_usuario == id_usuario and d.esta_activo()
        ]

    def obtener_duplicado_activo(
        self, id_usuario: int, tipo_documento: str, numero_documento: str
    ) -> Optional[DocumentoViaje]:
        _verificar_disponibilidad(numero_documento)
        return next(
            (
                d for d in self._datos
                if d.id_usuario == id_usuario
                and d.tipo_documento == tipo_documento
                and d.numero_documento == numero_documento
                and d.esta_activo()
            ),
            None,
        )

    def desmarcar_principales_usuario(self, id_usuario: int) -> None:
        for d in self._datos:
            if d.id_usuario == id_usuario and d.esta_activo():
                d.es_documento_principal = False

    def crear(
        self,
        id_usuario: int,
        tipo_documento: str,
        numero_documento: str,
        pais_emision: str,
        fecha_vencimiento: date,
        es_documento_principal: bool,
    ) -> DocumentoViaje:
        _verificar_disponibilidad(numero_documento)
        if es_documento_principal:
            self.desmarcar_principales_usuario(id_usuario)

        nuevo = DocumentoViaje(
            id_documento=self._siguiente_id,
            id_usuario=id_usuario,
            tipo_documento=tipo_documento,
            numero_documento=numero_documento,
            pais_emision=pais_emision,
            fecha_vencimiento=fecha_vencimiento,
            es_documento_principal=es_documento_principal,
            estado="ACTIVO",
        )
        self._datos.append(nuevo)
        self._siguiente_id += 1
        return nuevo


documento_viaje_repository = DocumentoViajeRepository()
