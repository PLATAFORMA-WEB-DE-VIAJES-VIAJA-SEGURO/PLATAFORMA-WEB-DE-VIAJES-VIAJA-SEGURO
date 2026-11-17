import os
from typing import List, Optional
from dotenv import load_dotenv
from app.domain.paquete import Destino


def _verificar_disponibilidad_paquetes(valor_control: str = "") -> None:
    load_dotenv(override=True)
    falla_env = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() == "true"
    if falla_env or valor_control.strip().upper() in {"503", "DST-503", "ACT-503"}:
        raise RuntimeError("Fallo de conexión con el servicio externo AEX-03 / catálogo de paquetes")


class PaqueteRepository:
    def __init__(self):
        self._destinos: List[Destino] = []
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

    # Base para HU-026 y HU-027
    def obtener_destino_por_id(self, id_destino: str) -> Optional[Destino]:
        _verificar_disponibilidad_paquetes(id_destino)
        return next(
            (d for d in self._destinos if d.id_destino == id_destino.strip().upper() and d.activo),
            None,
        )


paquete_repository = PaqueteRepository()