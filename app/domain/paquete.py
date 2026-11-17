from datetime import date
from typing import List, Optional
from pydantic import BaseModel

# Catálogos transversales (MOD-04 / AIN-04: PAR-02, PAR-03, PAR-10, PAR-07)
PAISES_PAQUETE_VALIDOS = {"CO", "US", "ES", "MX", "PA"}
MUNICIPIOS_PAQUETE_VALIDOS = {"BOG", "MDE", "CLO", "BGA", "CTG", "MIA", "MAD", "MEX", "PTY"}
TIPOS_PAQUETE_VALIDOS = {"TODO_INCLUIDO", "AVENTURA", "CULTURAL", "PLAYA", "FAMILIAR"}
CATEGORIAS_ACTIVIDAD_VALIDAS = {"TOUR_GUIADO", "AVENTURA", "GASTRONOMIA", "ACUATICA", "CULTURAL"}
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


# HU-026: Esquemas de consulta de actividades del destino
class ActividadItemOut(BaseModel):
    id_actividad: str
    id_destino: str
    nombre: str
    categoria: str
    duracion_horas: int
    punto_encuentro: str
    incluye_guia: bool
    cupos_diarios: int
    precio_persona: float
    moneda: str


class ConsultaActividadesOut(BaseModel):
    mensaje: str
    data: Optional[List[ActividadItemOut]] = None
    success: bool


# HU-027: Esquemas de verificación de cupo y tarifa de actividad
class DisponibilidadActividadDataOut(BaseModel):
    id_actividad: str
    nombre_actividad: str
    id_destino: str
    fecha_actividad: date
    cantidad_personas: int
    cupos_disponibles: int
    tarifa_unitaria: float
    impuestos: float
    total_actividad: float
    moneda: str
    disponible: bool


class DisponibilidadActividadOut(BaseModel):
    mensaje: str
    data: Optional[DisponibilidadActividadDataOut] = None
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


# Entidad de dominio: Actividad Turística (AEX-03)
class Actividad:
    def __init__(
        self,
        id_actividad: str,
        id_destino: str,
        nombre: str,
        categoria: str,
        duracion_horas: int,
        punto_encuentro: str,
        incluye_guia: bool,
        cupos_diarios: int,
        precio_persona: float,
        moneda: str = "COP",
        activa: bool = True,
    ):
        self.id_actividad = id_actividad
        self.id_destino = id_destino
        self.nombre = nombre
        self.categoria = categoria
        self.duracion_horas = duracion_horas
        self.punto_encuentro = punto_encuentro
        self.incluye_guia = incluye_guia
        self.cupos_diarios = cupos_diarios
        self.precio_persona = precio_persona
        self.moneda = moneda
        self.activa = activa

    # HU-026: Serialización de la actividad
    def to_response(self) -> dict:
        return {
            "id_actividad": self.id_actividad,
            "id_destino": self.id_destino,
            "nombre": self.nombre,
            "categoria": self.categoria,
            "duracion_horas": self.duracion_horas,
            "punto_encuentro": self.punto_encuentro,
            "incluye_guia": self.incluye_guia,
            "cupos_diarios": self.cupos_diarios,
            "precio_persona": self.precio_persona,
            "moneda": self.moneda,
        }

    # HU-027: Cálculo de tarifa consolidada y verificación de aforo
    def calcular_disponibilidad_tarifa(self, fecha_actividad: date, cantidad_personas: int) -> dict:
        subtotal = round(self.precio_persona * cantidad_personas, 2)
        impuestos = round(subtotal * 0.19, 2)
        return {
            "id_actividad": self.id_actividad,
            "nombre_actividad": self.nombre,
            "id_destino": self.id_destino,
            "fecha_actividad": fecha_actividad,
            "cantidad_personas": cantidad_personas,
            "cupos_disponibles": self.cupos_diarios,
            "tarifa_unitaria": self.precio_persona,
            "impuestos": impuestos,
            "total_actividad": round(subtotal + impuestos, 2),
            "moneda": self.moneda,
            "disponible": self.cupos_diarios >= cantidad_personas,
        }