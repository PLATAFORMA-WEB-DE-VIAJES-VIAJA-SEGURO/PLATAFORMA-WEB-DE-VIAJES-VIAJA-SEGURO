from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ── EXCEPCIONES HU-033 (Agregar ítem al carrito) ────────────────
class BusinessRuleRN33Exception(Exception):
    """Excepción cuando el bloqueo temporal expiró o el ítem ya está en el carrito (RN-33)."""
    def __init__(self, message: str = "El bloqueo temporal del servicio ha expirado o el ítem ya está en el carrito"):
        self.message = message
        super().__init__(self.message)


class InvalidCartItemDataException(Exception):
    """Excepción cuando el tipo de servicio, cantidad o referencia de bloqueo no son válidos (400)."""
    def __init__(self, message: str = "El tipo de servicio, cantidad o referencia de bloqueo no son válidos"):
        self.message = message
        super().__init__(self.message)


class CartServicesUnavailableException(Exception):
    """Excepción cuando falla la comunicación con AIN-09, AIN-10 o AIN-13 al actualizar el carrito (503)."""
    def __init__(self, message: str = "No fue posible actualizar el carrito de compras en este momento"):
        self.message = message
        super().__init__(self.message)


# ── EXCEPCIONES HU-035 (Consultar carrito) ──────────────────────
class BusinessRuleRN35Exception(Exception):
    """Excepción cuando el carrito contiene ítems cuyos bloqueos temporales han expirado (RN-35)."""
    def __init__(self, message: str = "El carrito contiene ítems cuyos bloqueos temporales han expirado"):
        self.message = message
        super().__init__(self.message)


class InvalidCartUserException(Exception):
    """Excepción cuando el identificador de usuario es inválido o faltante (400)."""
    def __init__(self, message: str = "Identificador de usuario inválido o faltante"):
        self.message = message
        super().__init__(self.message)


class CartQueryServicesUnavailableException(Exception):
    """Excepción cuando falla la recuperación del carrito de compras (503)."""
    def __init__(self, message: str = "No fue posible recuperar el carrito de compras"):
        self.message = message
        super().__init__(self.message)


# ── EXCEPCIONES HU-037 (Calcular total de la compra) ────────────
class BusinessRuleRN37Exception(Exception):
    """Excepción cuando el carrito está vacío o contiene servicios expirados (RN-37)."""
    def __init__(self, message: str = "El carrito está vacío o contiene servicios expirados que impiden liquidar"):
        self.message = message
        super().__init__(self.message)


class UnidentifiedCartException(Exception):
    """Excepción cuando no se puede identificar el carrito del usuario o el parámetro es inválido (400)."""
    def __init__(self, message: str = "No se pudo identificar el carrito del usuario"):
        self.message = message
        super().__init__(self.message)


class TotalCalculationServicesUnavailableException(Exception):
    """Excepción cuando falla la comunicación con AIN-05 o el cálculo del carrito (503)."""
    def __init__(self, message: str = "Error al calcular el total de la compra"):
        self.message = message
        super().__init__(self.message)


# ── EXCEPCIONES HU-038 (Cerrar compra) ──────────────────────────
class BusinessRuleRN38Exception(Exception):
    """Excepción cuando el carrito ya fue cerrado, el bloqueo caducó o la identidad no es válida (RN-38)."""
    def __init__(self, message: str = "El carrito ya fue cerrado previamente o algún bloqueo de servicio caducó"):
        self.message = message
        super().__init__(self.message)


class InvalidCheckoutDataException(Exception):
    """Excepción para datos de facturación o medio de pago incompletos o inválidos (400)."""
    def __init__(self, message: str = "Datos de facturación o medio de pago incompletos"):
        self.message = message
        super().__init__(self.message)


class CheckoutServicesUnavailableException(Exception):
    """Excepción cuando las dependencias AIN-08, AIN-09, AIN-10 o AIN-14 no responden (503)."""
    def __init__(self, message: str = "No fue posible procesar el cierre de compra por indisponibilidad de servicios"):
        self.message = message
        super().__init__(self.message)


# ── EXCEPCIONES HU-039 (Crear reserva) ──────────────────────────
class BusinessRuleRN39Exception(Exception):
    """Excepción cuando ya existe una reserva generada para el mismo carrito de compras (RN-39)."""
    def __init__(self, message: str = "Ya existe una reserva generada para este carrito de compras"):
        self.message = message
        super().__init__(self.message)


class InvalidReservationDataException(Exception):
    """Excepción cuando los datos son inválidos o el carrito no existe (400)."""
    def __init__(self, message: str = "Datos inválidos o carrito no encontrado para generar la reserva"):
        self.message = message
        super().__init__(self.message)


class ReservationServicesUnavailableException(Exception):
    """Excepción cuando las dependencias AIN-05, AIN-08, AIN-09 o AIN-10 no responden (503)."""
    def __init__(self, message: str = "No fue posible crear la reserva en este momento"):
        self.message = message
        super().__init__(self.message)


# ── EXCEPCIONES HU-040 (Registrar viajeros) ─────────────────────
class BusinessRuleRN40Exception(Exception):
    """Excepción cuando la cantidad de viajeros no coincide con los cupos o hay documentos duplicados (RN-40)."""
    def __init__(self, message: str = "La cantidad de viajeros no coincide con los cupos o hay documentos duplicados"):
        self.message = message
        super().__init__(self.message)


class InvalidTravelersDataException(Exception):
    """Excepción para datos de viajeros incompletos o tipo de documento inválido (400)."""
    def __init__(self, message: str = "Datos de viajeros incompletos o tipo de documento inválido"):
        self.message = message
        super().__init__(self.message)


class TravelersServicesUnavailableException(Exception):
    """Excepción cuando las dependencias AIN-01 o AIN-05 no responden al asociar viajeros (503)."""
    def __init__(self, message: str = "No fue posible asociar los viajeros a la reserva"):
        self.message = message
        super().__init__(self.message)


# ── EXCEPCIONES HU-043 (Cancelar reserva) ───────────────────────
class BusinessRuleRN43Exception(Exception):
    """Excepción cuando la reserva ya está cancelada o en un estado final que no permite anulación (RN-43)."""
    def __init__(self, message: str = "La reserva ya se encuentra cancelada o en un estado final que no permite anulación"):
        self.message = message
        super().__init__(self.message)


class InvalidCancellationReasonException(Exception):
    """Excepción cuando no se proporciona un motivo válido para cancelar la reserva (400)."""
    def __init__(self, message: str = "Debe proporcionar un motivo válido para cancelar la reserva"):
        self.message = message
        super().__init__(self.message)


class CancellationServicesUnavailableException(Exception):
    """Excepción cuando falla la comunicación con AIN-05 o AIN-16 al cancelar la reserva (503)."""
    def __init__(self, message: str = "No fue posible procesar la cancelación en este momento"):
        self.message = message
        super().__init__(self.message)


# ── MODELOS HU-033 (Agregar ítem al carrito) ────────────────────
class CartItemCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: int = Field(..., alias="id_usuario", gt=0, description="Identificador del viajero titular del carrito")
    service_type: str = Field(..., alias="tipo_servicio", min_length=2, description="Tipo de servicio (ej: VUELO, HOTEL, PAQUETE)")
    lock_reference_id: str = Field(..., alias="id_referencia_bloqueo", min_length=3, description="Identificador del bloqueo vigente (ej: BLK-V-9001)")
    description: str = Field(..., alias="descripcion", min_length=3, description="Descripción comercial del servicio")
    quantity: int = Field(..., alias="cantidad", gt=0, description="Cantidad de cupos o unidades del servicio")
    unit_price: float = Field(..., alias="precio_unitario", gt=0, description="Precio unitario del servicio")

    @field_validator("service_type", "lock_reference_id", "description")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("El campo no puede estar vacío.")
        return value.strip()


class CartItemData(BaseModel):
    id_carrito: int = Field(..., description="Identificador del carrito activo")
    id_item: int = Field(..., description="Identificador de la línea agregada al carrito")
    tipo_servicio: str = Field(..., description="Tipo de servicio agregado")
    id_referencia_bloqueo: str = Field(..., description="Referencia del bloqueo asociado")
    cantidad: int = Field(..., description="Cantidad agregada")
    subtotal: float = Field(..., description="Subtotal calculado para el ítem (cantidad * precio_unitario)")
    total_items_carrito: int = Field(..., description="Cantidad total de ítems acumulados en el carrito")


class CartItemResponse(BaseModel):
    mensaje: str
    data: Optional[CartItemData] = None
    success: bool


# ── MODELOS HU-035 (Consultar carrito) ──────────────────────────
class CartItemDetail(BaseModel):
    id_item: int = Field(..., description="Identificador de la línea en el carrito")
    tipo_servicio: str = Field(..., description="Tipo de servicio (ej: VUELO, HOTEL)")
    descripcion: str = Field(..., description="Descripción del servicio seleccionado")
    cantidad: int = Field(..., description="Cantidad de unidades o pasajeros")
    subtotal: float = Field(..., description="Subtotal de la línea")


class CartQueryData(BaseModel):
    id_carrito: int = Field(..., description="Identificador único del carrito")
    id_usuario: int = Field(..., description="Identificador del usuario titular")
    moneda: str = Field(..., description="Código ISO de la moneda (ej: COP)")
    estado: str = Field(..., description="Estado actual del carrito (ej: ABIERTO)")
    items: List[CartItemDetail] = Field(..., description="Listado de ítems activos en el carrito")


class CartQueryResponse(BaseModel):
    mensaje: str
    data: Optional[CartQueryData] = None
    success: bool


# ── MODELOS HU-037 (Calcular total de la compra) ────────────────
class TotalCalculationData(BaseModel):
    id_carrito: int = Field(..., description="Identificador del carrito liquidado")
    moneda: str = Field(..., description="Código ISO de la moneda (ej: COP)")
    subtotal: float = Field(..., description="Subtotal de los servicios antes de impuestos")
    impuestos: float = Field(..., description="Valor total de impuestos y tasas aplicables")
    descuentos: float = Field(..., description="Valor total de descuentos aplicados")
    total_pagar: float = Field(..., description="Valor total consolidado a pagar")


class TotalCalculationResponse(BaseModel):
    mensaje: str
    data: Optional[TotalCalculationData] = None
    success: bool


# ── MODELOS HU-038 (Cerrar compra) ──────────────────────────────
class CartCheckoutCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: int = Field(..., alias="id_usuario", gt=0, description="Identificador del viajero titular de la compra")
    cart_id: int = Field(..., alias="id_carrito", gt=0, description="Identificador del carrito de compras a cerrar")
    payment_method: str = Field(..., alias="medio_pago", min_length=2, description="Medio de pago seleccionado (ej: TARJETA_CREDITO, PSE)")
    billing_address: str = Field(..., alias="direccion_facturacion", min_length=5, description="Dirección física de facturación del viajero")

    @field_validator("payment_method", "billing_address")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("El campo no puede estar vacío.")
        return value.strip()


class CartCheckoutData(BaseModel):
    id_carrito: int = Field(..., description="Identificador del carrito cerrado")
    estado_carrito: str = Field(..., description="Nuevo estado del carrito (CERRADO)")
    codigo_reserva_preliminar: str = Field(..., description="Código de reserva preliminar generado (ej: VS-2026-8841)")
    total_liquidado: float = Field(..., description="Monto total congelado para el cobro")
    moneda: str = Field(..., description="Moneda de liquidación (ej: COP)")


class CartCheckoutResponse(BaseModel):
    mensaje: str
    data: Optional[CartCheckoutData] = None
    success: bool


# ── MODELOS HU-039 (Crear reserva) ──────────────────────────────
class ReservationCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: int = Field(..., alias="id_usuario", gt=0, description="Identificador del viajero titular de la reserva")
    cart_id: int = Field(..., alias="id_carrito", gt=0, description="Identificador del carrito de compras consolidado")
    currency: str = Field(..., alias="moneda", min_length=3, max_length=3, description="Código ISO de la moneda (ej: COP, USD)")
    total_reservation: float = Field(..., alias="total_reserva", gt=0, description="Monto total liquidado para la reserva")

    @field_validator("currency")
    @classmethod
    def validate_non_empty_currency(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("La moneda no puede estar vacía.")
        return value.strip()


class ReservationData(BaseModel):
    id_reserva: int = Field(..., description="Identificador único de la reserva creada")
    codigo_reserva: str = Field(..., description="Código localizador único (ej: VS-2026-8841)")
    id_usuario: int = Field(..., description="Identificador del viajero titular")
    estado: str = Field(..., description="Estado inicial de la reserva (PENDIENTE_PAGO)")
    total: float = Field(..., description="Monto total de la reserva")
    moneda: str = Field(..., description="Moneda de la reserva")
    fecha_creacion: str = Field(..., description="Fecha y hora de creación en formato ISO 8601")


class ReservationResponse(BaseModel):
    mensaje: str
    data: Optional[ReservationData] = None
    success: bool


# ── MODELOS HU-040 (Registrar viajeros) ─────────────────────────
class TravelerItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    first_name: str = Field(..., alias="nombres", description="Nombres del viajero")
    last_name: str = Field(..., alias="apellidos", description="Apellidos del viajero")
    document_type: str = Field(..., alias="tipo_documento", description="Tipo de documento según AIN-01 (ej: CC, CE, PA, TI)")
    document_number: str = Field(..., alias="numero_documento", description="Número de documento legal del viajero")
    birth_date: str = Field(..., alias="fecha_nacimiento", description="Fecha de nacimiento en formato YYYY-MM-DD")
    is_holder: bool = Field(False, alias="es_titular", description="Indica si el viajero es el titular de la reserva")


class RegisterTravelersCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    travelers: List[TravelerItem] = Field(..., alias="viajeros", min_length=1, description="Listado de viajeros a asociar en la reserva")


class RegisterTravelersData(BaseModel):
    id_reserva: int = Field(..., description="Identificador de la reserva")
    codigo_reserva: str = Field(..., description="Código localizador de la reserva (ej: VS-2026-8841)")
    total_viajeros_registrados: int = Field(..., description="Cantidad total de viajeros registrados")
    estado_nominacion: str = Field(..., description="Estado de nominación de la reserva (COMPLETA)")


class RegisterTravelersResponse(BaseModel):
    mensaje: str
    data: Optional[RegisterTravelersData] = None
    success: bool


# ── MODELOS HU-043 (Cancelar reserva) ───────────────────────────
class CancelReservationCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: int = Field(..., alias="id_usuario", gt=0, description="Identificador del viajero que solicita la cancelación")
    cancellation_reason: str = Field(..., alias="motivo_cancelacion", description="Motivo de cancelación de la reserva")


class CancelReservationData(BaseModel):
    id_reserva: int = Field(..., description="Identificador único de la reserva")
    codigo_reserva: str = Field(..., description="Código localizador de la reserva (ej: VS-2026-8841)")
    estado_anterior: str = Field(..., description="Estado de la reserva antes de cancelar (ej: CONFIRMADA)")
    estado_actual: str = Field(..., description="Nuevo estado de la reserva (CANCELADA)")
    aplica_reembolso: bool = Field(..., description="Indica si la cancelación aplica para reembolso")
    fecha_cancelacion: str = Field(..., description="Fecha y hora de cancelación en formato ISO 8601")


class CancelReservationResponse(BaseModel):
    mensaje: str
    data: Optional[CancelReservationData] = None
    success: bool
