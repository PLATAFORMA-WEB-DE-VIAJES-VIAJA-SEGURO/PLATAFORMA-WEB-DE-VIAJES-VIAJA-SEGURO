from datetime import date
from typing import Optional
from app.domain.paquete import (
    PAISES_PAQUETE_VALIDOS,
    MUNICIPIOS_PAQUETE_VALIDOS,
    TIPOS_PAQUETE_VALIDOS,
    CATEGORIAS_ACTIVIDAD_VALIDAS,
    DestinoItemOut,
    ConsultaDestinosOut,
    ActividadItemOut,
    ConsultaActividadesOut,
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

        if not destinos:
            raise ErrorReglaNegocioPaquete(
                "No se encontraron destinos turísticos activos para los criterios consultados"
            )

        return ConsultaDestinosOut(
            mensaje="Destinos turísticos consultados exitosamente",
            data=[DestinoItemOut(**d.to_response()) for d in destinos],
            success=True,
        )

    # HU-026: Consultar actividades del destino (RN-26)
    def consultar_actividades_destino(
        self,
        id_destino: str,
        fecha_inicio: date,
        fecha_fin: Optional[date] = None,
        categoria: Optional[str] = None,
    ) -> ConsultaActividadesOut:
        destino_norm = id_destino.strip().upper()
        categoria_norm = categoria.strip().upper() if categoria else None

        if fecha_inicio < date.today():
            raise ErrorParametrosPaquete(
                "La fecha de inicio de las actividades no puede ser anterior a la fecha actual"
            )
        if fecha_fin and fecha_fin < fecha_inicio:
            raise ErrorParametrosPaquete(
                "La fecha de fin no puede ser anterior a la fecha de inicio"
            )
        if categoria_norm and categoria_norm not in CATEGORIAS_ACTIVIDAD_VALIDAS:
            raise ErrorParametrosPaquete(
                "La categoría de actividad no es válida (TOUR_GUIADO, AVENTURA, GASTRONOMIA, ACUATICA, CULTURAL)"
            )

        destino = self.repo.obtener_destino_por_id(destino_norm)
        if not destino:
            raise ErrorReglaNegocioPaquete(
                "El destino seleccionado no existe o no se encuentra activo"
            )

        actividades = self.repo.consultar_actividades_destino(
            id_destino=destino_norm,
            categoria=categoria_norm,
        )

        # RN-26: El destino debe contar con actividades vigentes en operadores locales (AEX-03)
        if not actividades:
            raise ErrorReglaNegocioPaquete(
                "No se encontraron actividades disponibles en AEX-03 para el destino y criterios indicados"
            )

        return ConsultaActividadesOut(
            mensaje="Actividades del destino consultadas exitosamente",
            data=[ActividadItemOut(**a.to_response()) for a in actividades],
            success=True,
        )