from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


# ── EXCEPCIONES HU-037 (Calcular total de la compra) ────────────
class ReglaNegocioRN37Exception(Exception):
    """Excepción cuando el carrito está vacío o contiene servicios expirados (RN-37)."""
    def __init__(self, mensaje: str = "El carrito está vacío o contiene servicios expirados que impiden liquidar"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class CarritoNoIdentificadoException(Exception):
    """Excepción cuando no se puede identificar el carrito del usuario o el parámetro es inválido (400)."""
    def __init__(self, mensaje: str = "No se pudo identificar el carrito del usuario"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class ServiciosCalculoTotalNoDisponiblesException(Exception):
    """Excepción cuando falla la comunicación con AIN-05 o el cálculo del carrito (503)."""
    def __init__(self, mensaje: str = "Error al calcular el total de la compra"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


# ── EXCEPCIONES HU-038 (Cerrar compra) ──────────────────────────
class ReglaNegocioRN38Exception(Exception):
    """Excepción cuando el carrito ya fue cerrado, el bloqueo caducó o la identidad no es válida (RN-38)."""
    def __init__(self, mensaje: str = "El carrito ya fue cerrado previamente o algún bloqueo de servicio caducó"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class DatosCierreCompraInvalidosException(Exception):
    """Excepción para datos de facturación o medio de pago incompletos o inválidos (400)."""
    def __init__(self, mensaje: str = "Datos de facturación o medio de pago incompletos"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class ServiciosCierreNoDisponiblesException(Exception):
    """Excepción cuando las dependencias AIN-08, AIN-09, AIN-10 o AIN-14 no responden (503)."""
    def __init__(self, mensaje: str = "No fue posible procesar el cierre de compra por indisponibilidad de servicios"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


# ── EXCEPCIONES HU-039 (Crear reserva) ──────────────────────────
class ReglaNegocioRN39Exception(Exception):
    """Excepción cuando ya existe una reserva generada para el mismo carrito de compras (RN-39)."""
    def __init__(self, mensaje: str = "Ya existe una reserva generada para este carrito de compras"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class DatosReservaInvalidosException(Exception):
    """Excepción cuando los datos son inválidos o el carrito no existe (400)."""
    def __init__(self, mensaje: str = "Datos inválidos o carrito no encontrado para generar la reserva"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class ServiciosReservaNoDisponiblesException(Exception):
    """Excepción cuando las dependencias AIN-05, AIN-08, AIN-09 o AIN-10 no responden (503)."""
    def __init__(self, mensaje: str = "No fue posible crear la reserva en este momento"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


# ── EXCEPCIONES HU-040 (Registrar viajeros) ─────────────────────
class ReglaNegocioRN40Exception(Exception):
    """Excepción cuando la cantidad de viajeros no coincide con los cupos o hay documentos duplicados (RN-40)."""
    def __init__(self, mensaje: str = "La cantidad de viajeros no coincide con los cupos o hay documentos duplicados"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class DatosViajerosInvalidosException(Exception):
    """Excepción para datos de viajeros incompletos o tipo de documento inválido (400)."""
    def __init__(self, mensaje: str = "Datos de viajeros incompletos o tipo de documento inválido"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class ServiciosViajerosNoDisponiblesException(Exception):
    """Excepción cuando las dependencias AIN-01 o AIN-05 no responden al asociar viajeros (503)."""
    def __init__(self, mensaje: str = "No fue posible asociar los viajeros a la reserva"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


# ── MODELOS HU-037 (Calcular total de la compra) ────────────────
class CalculoTotalData(BaseModel):
    id_carrito: int = Field(..., description="Identificador del carrito liquidado")
    moneda: str = Field(..., description="Código ISO de la moneda (ej: COP)")
    subtotal: float = Field(..., description="Subtotal de los servicios antes de impuestos")
    impuestos: float = Field(..., description="Valor total de impuestos y tasas aplicables")
    descuentos: float = Field(..., description="Valor total de descuentos aplicados")
    total_pagar: float = Field(..., description="Valor total consolidado a pagar")


class CalculoTotalResponse(BaseModel):
    mensaje: str
    data: Optional[CalculoTotalData] = None
    success: bool


# ── MODELOS HU-038 (Cerrar compra) ──────────────────────────────
class CierreCarritoCreate(BaseModel):
    id_usuario: int = Field(..., gt=0, description="Identificador del viajero titular de la compra")
    id_carrito: int = Field(..., gt=0, description="Identificador del carrito de compras a cerrar")
    medio_pago: str = Field(..., min_length=2, description="Medio de pago seleccionado (ej: TARJETA_CREDITO, PSE)")
    direccion_facturacion: str = Field(..., min_length=5, description="Dirección física de facturación del viajero")

    @field_validator("medio_pago", "direccion_facturacion")
    @classmethod
    def validar_no_vacio(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("El campo no puede estar vacío.")
        return v.strip()


class CierreCarritoData(BaseModel):
    id_carrito: int = Field(..., description="Identificador del carrito cerrado")
    estado_carrito: str = Field(..., description="Nuevo estado del carrito (CERRADO)")
    codigo_reserva_preliminar: str = Field(..., description="Código de reserva preliminar generado (ej: VS-2026-8841)")
    total_liquidado: float = Field(..., description="Monto total congelado para el cobro")
    moneda: str = Field(..., description="Moneda de liquidación (ej: COP)")


class CierreCarritoResponse(BaseModel):
    mensaje: str
    data: Optional[CierreCarritoData] = None
    success: bool


# ── MODELOS HU-039 (Crear reserva) ──────────────────────────────
class ReservaCreate(BaseModel):
    id_usuario: int = Field(..., gt=0, description="Identificador del viajero titular de la reserva")
    id_carrito: int = Field(..., gt=0, description="Identificador del carrito de compras consolidado")
    moneda: str = Field(..., min_length=3, max_length=3, description="Código ISO de la moneda (ej: COP, USD)")
    total_reserva: float = Field(..., gt=0, description="Monto total liquidado para la reserva")

    @field_validator("moneda")
    @classmethod
    def validar_moneda_no_vacia(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("La moneda no puede estar vacía.")
        return v.strip()


class ReservaData(BaseModel):
    id_reserva: int = Field(..., description="Identificador único de la reserva creada")
    codigo_reserva: str = Field(..., description="Código localizador único (ej: VS-2026-8841)")
    id_usuario: int = Field(..., description="Identificador del viajero titular")
    estado: str = Field(..., description="Estado inicial de la reserva (PENDIENTE_PAGO)")
    total: float = Field(..., description="Monto total de la reserva")
    moneda: str = Field(..., description="Moneda de la reserva")
    fecha_creacion: str = Field(..., description="Fecha y hora de creación en formato ISO 8601")


class ReservaResponse(BaseModel):
    mensaje: str
    data: Optional[ReservaData] = None
    success: bool


# ── MODELOS HU-040 (Registrar viajeros) ─────────────────────────
class ViajeroItem(BaseModel):
    nombres: str = Field(..., description="Nombres del viajero")
    apellidos: str = Field(..., description="Apellidos del viajero")
    tipo_documento: str = Field(..., description="Tipo de documento según AIN-01 (ej: CC, CE, PA, TI)")
    numero_documento: str = Field(..., description="Número de documento legal del viajero")
    fecha_nacimiento: str = Field(..., description="Fecha de nacimiento en formato YYYY-MM-DD")
    es_titular: bool = Field(False, description="Indica si el viajero es el titular de la reserva")


class RegistrarViajerosCreate(BaseModel):
    viajeros: List[ViajeroItem] = Field(..., min_length=1, description="Listado de viajeros a asociar en la reserva")


class RegistrarViajerosData(BaseModel):
    id_reserva: int = Field(..., description="Identificador de la reserva")
    codigo_reserva: str = Field(..., description="Código localizador de la reserva (ej: VS-2026-8841)")
    total_viajeros_registrados: int = Field(..., description="Cantidad total de viajeros registrados")
    estado_nominacion: str = Field(..., description="Estado de nominación de la reserva (COMPLETA)")


class RegistrarViajerosResponse(BaseModel):
    mensaje: str
    data: Optional[RegistrarViajerosData] = None
    success: bool
