from typing import Optional
from app.domain.paquete import (
    PAISES_PAQUETE_VALIDOS,
    MUNICIPIOS_PAQUETE_VALIDOS,
    TIPOS_PAQUETE_VALIDOS,
    DestinoItemOut,
    ConsultaDestinosOut,
)
from app.repositories.paquete_repository import PaqueteRepository


class ErrorParametrosPaquete(Exception):
    pass


class ErrorReglaNegocioPaquete(Exception):
    pass


class PaqueteService:
    def __init__(self, repo: PaqueteRepository):
        self.repo = repo

    # HU-023: Consultar destinos (RN-23)
    def consultar_destinos(
        self,
        pais: Optional[str] = None,
        municipio: Optional[str] = None,
        tipo_paquete: Optional[str] = None,
    ) -> ConsultaDestinosOut:
        pais_norm = pais.strip().upper() if pais else None
        municipio_norm = municipio.strip().upper() if municipio else None
        tipo_norm = tipo_paquete.strip().upper() if tipo_paquete else None

        if pais_norm and pais_norm != "503" and pais_norm not in PAISES_PAQUETE_VALIDOS:
            raise ErrorParametrosPaquete(
                "El código de país no es válido en el catálogo PAR-02"
            )
        if municipio_norm and municipio_norm != "503" and municipio_norm not in MUNICIPIOS_PAQUETE_VALIDOS:
            raise ErrorParametrosPaquete(
                "El código de municipio no es válido en el catálogo PAR-03"
            )
        if tipo_norm and tipo_norm not in TIPOS_PAQUETE_VALIDOS:
            raise ErrorParametrosPaquete(
                "El tipo de paquete no es válido en el catálogo PAR-10"
            )

        destinos = self.repo.consultar_destinos(
            pais=pais_norm,
            municipio=municipio_norm,
            tipo_paquete=tipo_norm,
        )

        # RN-23: Validar que existan destinos activos para los filtros indicados
        if not destinos:
            raise ErrorReglaNegocioPaquete(
                "No se encontraron destinos turísticos activos para los criterios consultados"
            )

        return ConsultaDestinosOut(
            mensaje="Destinos turísticos consultados exitosamente",
            data=[DestinoItemOut(**d.to_response()) for d in destinos],
            success=True,
        )