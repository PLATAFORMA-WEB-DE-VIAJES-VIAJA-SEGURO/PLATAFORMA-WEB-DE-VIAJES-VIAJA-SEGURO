from datetime import date, datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field

# Catálogos y reglas transversales (MOD-02 / AIN-02)
AEROPUERTOS_VALIDOS = {"BOG", "MDE", "CLO", "BGA", "CTG", "MIA", "MAD", "MEX", "PTY"}
CABINAS_VALIDAS = {"ECONOMICA", "EJECUTIVA", "PRIMERA"}
MONEDAS_VALIDAS_AIN02 = {"COP", "USD"}


# HU-011: Esquemas de búsqueda de vuelos
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


# HU-013: Esquemas de consulta de tarifas del vuelo
class TarifaVueloItemOut(BaseModel):
    codigo_tarifa: str
    nombre_tarifa: str
    cabina: str
    equipaje_incluido: str
    permite_cambios: bool
    precio_unitario: float
    impuestos: float
    precio_total_pasajero: float
    moneda: str


class ConsultaTarifasVueloOut(BaseModel):
    mensaje: str
    data: Optional[List[TarifaVueloItemOut]] = None
    success: bool


# HU-015: Esquemas de bloqueo temporal de puestos
class BloqueoPuestosCreate(BaseModel):
    cantidad_puestos: int = Field(..., ge=1, le=9)
    tiempo_bloqueo_minutos: int = Field(default=20, ge=5, le=20)
    codigo_tarifa: Optional[str] = Field(default=None)


class BloqueoPuestosDataOut(BaseModel):
    id_bloqueo: str
    id_vuelo: str
    numero_vuelo: str
    cantidad_puestos: int
    puestos_restantes_vuelo: int
    tiempo_bloqueo_minutos: int
    fecha_expiracion: str
    estado: str


class BloqueoPuestosOut(BaseModel):
    mensaje: str
    data: Optional[BloqueoPuestosDataOut] = None
    success: bool


# Entidad de dominio: Bloqueo de puestos (HU-015)
class BloqueoVuelo:
    def __init__(
        self,
        id_bloqueo: str,
        id_vuelo: str,
        numero_vuelo: str,
        cantidad_puestos: int,
        puestos_restantes_vuelo: int,
        tiempo_bloqueo_minutos: int = 20,
    ):
        self.id_bloqueo = id_bloqueo
        self.id_vuelo = id_vuelo
        self.numero_vuelo = numero_vuelo
        self.cantidad_puestos = cantidad_puestos
        self.puestos_restantes_vuelo = puestos_restantes_vuelo
        self.tiempo_bloqueo_minutos = tiempo_bloqueo_minutos
        self.fecha_expiracion = (
            datetime.utcnow() + timedelta(minutes=tiempo_bloqueo_minutos)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.estado = "ACTIVO"

    def to_response(self) -> dict:
        return {
            "id_bloqueo": self.id_bloqueo,
            "id_vuelo": self.id_vuelo,
            "numero_vuelo": self.numero_vuelo,
            "cantidad_puestos": self.cantidad_puestos,
            "puestos_restantes_vuelo": self.puestos_restantes_vuelo,
            "tiempo_bloqueo_minutos": self.tiempo_bloqueo_minutos,
            "fecha_expiracion": self.fecha_expiracion,
            "estado": self.estado,
        }


# Entidad de dominio: Vuelo
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

    # HU-011: Serialización del vuelo
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

    # HU-013: Cálculo de familias tarifarias
    def generar_familias_tarifarias(self, cabina: Optional[str] = None, equipaje_bodega: int = 0) -> List[dict]:
        factor_equipaje = equipaje_bodega * 85000.0
        familias = [
            {
                "codigo_tarifa": f"{self.id_vuelo}-ECO-BASIC",
                "nombre_tarifa": "Económica Básica",
                "cabina": "ECONOMICA",
                "equipaje_incluido": "1 artículo personal" + (f" + {equipaje_bodega} maleta(s) 23kg" if equipaje_bodega > 0 else ""),
                "permite_cambios": False,
                "multiplicador": 1.0,
            },
            {
                "codigo_tarifa": f"{self.id_vuelo}-ECO-FLEX",
                "nombre_tarifa": "Económica Flexible",
                "cabina": "ECONOMICA",
                "equipaje_incluido": f"1 equipaje de mano + {max(1, equipaje_bodega)} maleta(s) 23kg",
                "permite_cambios": True,
                "multiplicador": 1.25,
            },
            {
                "codigo_tarifa": f"{self.id_vuelo}-EJE-PLUS",
                "nombre_tarifa": "Ejecutiva Plus",
                "cabina": "EJECUTIVA",
                "equipaje_incluido": "2 maletas 32kg + sala VIP" + (f" + {equipaje_bodega} extra" if equipaje_bodega > 0 else ""),
                "permite_cambios": True,
                "multiplicador": 1.85,
            },
            {
                "codigo_tarifa": f"{self.id_vuelo}-PRI-SUITE",
                "nombre_tarifa": "Primera Clase Suite",
                "cabina": "PRIMERA",
                "equipaje_incluido": "3 maletas 32kg + embarque prioritario",
                "permite_cambios": True,
                "multiplicador": 2.6,
            },
        ]

        resultado = []
        for f in familias:
            if cabina and f["cabina"] != cabina:
                continue
            unitario = round((self.precio_base * f["multiplicador"]) + factor_equipaje, 2)
            impuestos = round(unitario * 0.19, 2)
            resultado.append({
                "codigo_tarifa": f["codigo_tarifa"],
                "nombre_tarifa": f["nombre_tarifa"],
                "cabina": f["cabina"],
                "equipaje_incluido": f["equipaje_incluido"],
                "permite_cambios": f["permite_cambios"],
                "precio_unitario": unitario,
                "impuestos": impuestos,
                "precio_total_pasajero": round(unitario + impuestos, 2),
                "moneda": self.moneda,
            })
        return resultado