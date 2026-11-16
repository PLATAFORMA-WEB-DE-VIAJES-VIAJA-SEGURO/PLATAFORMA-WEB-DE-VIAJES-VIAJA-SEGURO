from typing import List, Optional
from pydantic import BaseModel

# Catálogos transversales (MOD-04 / AIN-04: PAR-02, PAR-03, PAR-10, PAR-07)
PAISES_PAQUETE_VALIDOS = {"CO", "US", "ES", "MX", "PA"}
MUNICIPIOS_PAQUETE_VALIDOS = {"BOG", "MDE", "CLO", "BGA", "CTG", "MIA", "MAD", "MEX", "PTY"}
TIPOS_PAQUETE_VALIDOS = {"TODO_INCLUIDO", "AVENTURA", "CULTURAL", "PLAYA", "FAMILIAR"}
MONEDAS_PAQUETE_AIN04 = {"COP", "USD"}


# HU-023: Esquemas de consulta de destinos
class DestinoItemOut(BaseModel):
    id_destino: str
    nombre: str
    pais: str
    municipio: str
    tipo_paquete: str
    descripcion: str
    temporada_recomendada: str
    precio_desde: float
    moneda: str


class ConsultaDestinosOut(BaseModel):
    mensaje: str
    data: Optional[List[DestinoItemOut]] = None
    success: bool


# Entidad de dominio: Destino
class Destino:
    def __init__(
        self,
        id_destino: str,
        nombre: str,
        pais: str,
        municipio: str,
        tipo_paquete: str,
        descripcion: str,
        temporada_recomendada: str,
        precio_desde: float,
        moneda: str = "COP",
        activo: bool = True,
    ):
        self.id_destino = id_destino
        self.nombre = nombre
        self.pais = pais
        self.municipio = municipio
        self.tipo_paquete = tipo_paquete
        self.descripcion = descripcion
        self.temporada_recomendada = temporada_recomendada
        self.precio_desde = precio_desde
        self.moneda = moneda
        self.activo = activo

    # HU-023: Serialización del destino
    def to_response(self) -> dict:
        return {
            "id_destino": self.id_destino,
            "nombre": self.nombre,
            "pais": self.pais,
            "municipio": self.municipio,
            "tipo_paquete": self.tipo_paquete,
            "descripcion": self.descripcion,
            "temporada_recomendada": self.temporada_recomendada,
            "precio_desde": self.precio_desde,
            "moneda": self.moneda,
        }