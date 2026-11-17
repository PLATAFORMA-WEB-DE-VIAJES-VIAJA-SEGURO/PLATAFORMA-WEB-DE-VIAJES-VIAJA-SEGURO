import os
from typing import List, Optional
from dotenv import load_dotenv
from app.domain.paquete import Destino, Actividad


def _verificar_disponibilidad_paquetes(valor_control: str = "") -> None:
    load_dotenv(override=True)
    falla_env = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() == "true"
    if falla_env or valor_control.strip().upper() in {"503", "DST-503"}:
        raise RuntimeError("Fallo de conexión con el servicio externo AEX-03 / catálogo de paquetes")


class PaqueteRepository:
    def __init__(self):
        self._destinos: List[Destino] = []
        self._actividades: List[Actividad] = []
        self._seed()

    def _seed(self):
        self._destinos = [
            Destino(
                id_destino="DST-301",
                nombre="Cartagena Colonial y Playas",
                pais="CO",
                municipio="CTG",
                tipo_paquete="PLAYA",
                descripcion="Recorrido por la ciudad amurallada, Islas del Rosario y gastronomía caribeña",
                temporada_recomendada="Diciembre a Abril",
                precio_desde=1250000.0,
                moneda="COP",
            ),
            Destino(
                id_destino="DST-302",
                nombre="Medellín Innovación y Cultura",
                pais="CO",
                municipio="MDE",
                tipo_paquete="CULTURAL",
                descripcion="Tour Comuna 13, Guatapé y Piedra del Peñol",
                temporada_recomendada="Todo el año",
                precio_desde=890000.0,
                moneda="COP",
            ),
            Destino(
                id_destino="DST-303",
                nombre="Bogotá Histórica y Monserrate",
                pais="CO",
                municipio="BOG",
                tipo_paquete="CULTURAL",
                descripcion="Visita a La Candelaria, Museo del Oro y Cerro de Monserrate",
                temporada_recomendada="Enero a Marzo",
                precio_desde=640000.0,
                moneda="COP",
            ),
            Destino(
                id_destino="DST-304",
                nombre="Miami Beach y Parques",
                pais="US",
                municipio="MIA",
                tipo_paquete="TODO_INCLUIDO",
                descripcion="Estancia frente al mar con paseos por Everglades y compras",
                temporada_recomendada="Noviembre a Mayo",
                precio_desde=3400000.0,
                moneda="COP",
            ),
        ]

        self._actividades = [
            Actividad(
                id_actividad="ACT-401",
                id_destino="DST-301",
                nombre="Pasadía Islas del Rosario y Playa Blanca",
                categoria="ACUATICA",
                duracion_horas=8,
                punto_encuentro="Muelle de la Bodeguita - Puerta 4",
                incluye_guia=True,
                cupos_diarios=20,
                precio_persona=260000.0,
                moneda="COP",
            ),
            Actividad(
                id_actividad="ACT-402",
                id_destino="DST-301",
                nombre="Caminata Histórica Ciudad Amurallada y Castillo San Felipe",
                categoria="CULTURAL",
                duracion_horas=4,
                punto_encuentro="Torre del Reloj",
                incluye_guia=True,
                cupos_diarios=15,
                precio_persona=140000.0,
                moneda="COP",
            ),
            Actividad(
                id_actividad="ACT-403",
                id_destino="DST-302",
                nombre="Excursión Piedra del Peñol y Guatapé",
                categoria="TOUR_GUIADO",
                duracion_horas=10,
                punto_encuentro="Estación Poblado",
                incluye_guia=True,
                cupos_diarios=12,
                precio_persona=195000.0,
                moneda="COP",
            ),
            Actividad(
                id_actividad="ACT-404",
                id_destino="DST-303",
                nombre="Recorrido Museo del Oro y Monserrate",
                categoria="CULTURAL",
                duracion_horas=5,
                punto_encuentro="Parque Santander",
                incluye_guia=True,
                cupos_diarios=2,
                precio_persona=130000.0,
                moneda="COP",
            ),
        ]

    # HU-023: Consultar destinos disponibles con filtros opcionales
    def consultar_destinos(
        self,
        pais: Optional[str] = None,
        municipio: Optional[str] = None,
        tipo_paquete: Optional[str] = None,
    ) -> List[Destino]:
        valor_control = pais or municipio or tipo_paquete or ""
        _verificar_disponibilidad_paquetes(valor_control)
        return [
            d for d in self._destinos
            if d.activo
            and (pais is None or d.pais == pais)
            and (municipio is None or d.municipio == municipio)
            and (tipo_paquete is None or d.tipo_paquete == tipo_paquete)
        ]

    # HU-026: Obtener destino por ID
    def obtener_destino_por_id(self, id_destino: str) -> Optional[Destino]:
        _verificar_disponibilidad_paquetes(id_destino)
        return next(
            (d for d in self._destinos if d.id_destino == id_destino.strip().upper() and d.activo),
            None,
        )

    # HU-026: Consultar actividades asociadas a un destino en AEX-03
    def consultar_actividades_destino(
        self,
        id_destino: str,
        categoria: Optional[str] = None,
    ) -> List[Actividad]:
        _verificar_disponibilidad_paquetes(id_destino)
        return [
            a for a in self._actividades
            if a.activa
            and a.id_destino == id_destino.strip().upper()
            and a.cupos_diarios > 0
            and (categoria is None or a.categoria == categoria)
        ]


paquete_repository = PaqueteRepository()