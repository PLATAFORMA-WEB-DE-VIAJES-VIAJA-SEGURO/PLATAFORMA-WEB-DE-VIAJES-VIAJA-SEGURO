from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field

AEROPUERTOS_VALIDOS = {"BOG", "MDE", "CLO", "BGA", "CTG", "MIA", "MAD", "MEX", "PTY"}


class VueloItemOut(BaseModel):
    id_vuelo: str
    aerolinea: str
    numero_vuelo: str
    origen: str
    destino: str
    fecha_salida: date
    hora_salida: str
    hora_llegada: str
    duracion: str
    puestos_disponibles: int
    precio_base: float
    moneda: str


class BusquedaVuelosOut(BaseModel):
    mensaje: str
    data: Optional[List[VueloItemOut]] = None
    success: bool


class Vuelo:
    def __init__(
        self,
        id_vuelo: str,
        aerolinea: str,
        numero_vuelo: str,
        origen: str,
        destino: str,
        fecha_salida: date,
        hora_salida: str,
        hora_llegada: str,
        duracion: str,
        puestos_disponibles: int,
        precio_base: float,
        moneda: str = "COP",
        activo: bool = True,
    ):
        self.id_vuelo = id_vuelo
        self.aerolinea = aerolinea
        self.numero_vuelo = numero_vuelo
        self.origen = origen
        self.destino = destino
        self.fecha_salida = fecha_salida
        self.hora_salida = hora_salida
        self.hora_llegada = hora_llegada
        self.duracion = duracion
        self.puestos_disponibles = puestos_disponibles
        self.precio_base = precio_base
        self.moneda = moneda
        self.activo = activo

    def to_response(self) -> dict:
        return {
            "id_vuelo": self.id_vuelo,
            "aerolinea": self.aerolinea,
            "numero_vuelo": self.numero_vuelo,
            "origen": self.origen,
            "destino": self.destino,
            "fecha_salida": self.fecha_salida,
            "hora_salida": self.hora_salida,
            "hora_llegada": self.hora_llegada,
            "duracion": self.duracion,
            "puestos_disponibles": self.puestos_disponibles,
            "precio_base": self.precio_base,
            "moneda": self.moneda,
        }