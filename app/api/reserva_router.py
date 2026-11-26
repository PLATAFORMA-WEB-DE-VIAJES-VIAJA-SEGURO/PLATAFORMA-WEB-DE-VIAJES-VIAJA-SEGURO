import os
from typing import Optional
from dotenv import load_dotenv
from fastapi import APIRouter, Path, Query, status
from fastapi.responses import JSONResponse
from app.domain.reserva import (
    CartItemCreate,
    CartItemResponse,
    BusinessRuleRN33Exception,
    InvalidCartItemDataException,
    CartServicesUnavailableException,
    CartQueryResponse,
    BusinessRuleRN35Exception,
    InvalidCartUserException,
    CartQueryServicesUnavailableException,
    TotalCalculationResponse,
    BusinessRuleRN37Exception,
    UnidentifiedCartException,
    TotalCalculationServicesUnavailableException,
    CartCheckoutCreate,
    CartCheckoutResponse,
    BusinessRuleRN38Exception,
    InvalidCheckoutDataException,
    CheckoutServicesUnavailableException,
    ReservationCreate,
    ReservationResponse,
    BusinessRuleRN39Exception,
    InvalidReservationDataException,
    ReservationServicesUnavailableException,
    RegisterTravelersCreate,
    RegisterTravelersResponse,
    BusinessRuleRN40Exception,
    InvalidTravelersDataException,
    TravelersServicesUnavailableException,
    CancelReservationCreate,
    CancelReservationResponse,
    BusinessRuleRN43Exception,
    InvalidCancellationReasonException,
    CancellationServicesUnavailableException,
)
from app.services.reserva_service import ReservationService
from app.repositories.reserva_repository import reservation_repository

router = APIRouter(
    prefix="/api/v1/reservas",
    tags=["Compra y Reservas"],
)

service = ReservationService(repo=reservation_repository)

# Documentación OpenAPI para HU-033 (Agregar ítem al carrito)
OPENAPI_ADD_ITEM_RESPONSES = {
    201: {
        "description": "Ítem agregado al carrito exitosamente",
        "model": CartItemResponse,
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Ítem agregado al carrito exitosamente",
                    "data": {
                        "id_carrito": 701,
                        "id_item": 1,
                        "tipo_servicio": "VUELO",
                        "id_referencia_bloqueo": "BLK-V-9001",
                        "cantidad": 2,
                        "subtotal": 900000.0,
                        "total_items_carrito": 1,
                    },
                    "success": True,
                }
            }
        },
    },
    400: {
        "description": "El tipo de servicio, cantidad o referencia de bloqueo no son válidos",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "El tipo de servicio, cantidad o referencia de bloqueo no son válidos",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    409: {
        "description": "Error por Regla de Negocio RN-33 (El bloqueo temporal ha expirado o el ítem ya está en el carrito)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "El bloqueo temporal del servicio ha expirado o el ítem ya está en el carrito",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    422: {
        "description": "Parámetros de entrada inválidos o incompletos (validación de esquema)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Parámetros de entrada inválidos o incompletos",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    503: {
        "description": "Falla de Disponibilidad (Indisponibilidad de servicios AIN-09, AIN-10 o AIN-13)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "No fue posible actualizar el carrito de compras en este momento",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
}

# Documentación OpenAPI para HU-035 (Consultar carrito)
OPENAPI_GET_CART_RESPONSES = {
    200: {
        "description": "Carrito consultado exitosamente",
        "model": CartQueryResponse,
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Carrito consultado exitosamente",
                    "data": {
                        "id_carrito": 701,
                        "id_usuario": 1,
                        "moneda": "COP",
                        "estado": "ABIERTO",
                        "items": [
                            {
                                "id_item": 1,
                                "tipo_servicio": "VUELO",
                                "descripcion": "Vuelo BOG - CTG (2 pasajeros)",
                                "cantidad": 2,
                                "subtotal": 900000.0,
                            },
                            {
                                "id_item": 2,
                                "tipo_servicio": "HOTEL",
                                "descripcion": "Hotel Caribe Cartagena (5 noches)",
                                "cantidad": 1,
                                "subtotal": 2100000.0,
                            },
                        ],
                    },
                    "success": True,
                }
            }
        },
    },
    400: {
        "description": "Identificador de usuario inválido o faltante",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Identificador de usuario inválido o faltante",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    409: {
        "description": "Error por Regla de Negocio RN-35 (El carrito contiene ítems cuyos bloqueos temporales han expirado)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "El carrito contiene ítems cuyos bloqueos temporales han expirado",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    422: {
        "description": "Parámetros de entrada inválidos o incompletos (validación de esquema)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Parámetros de entrada inválidos o incompletos",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    503: {
        "description": "Falla de Disponibilidad (No fue posible recuperar el carrito de compras)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "No fue posible recuperar el carrito de compras",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
}

# Documentación OpenAPI para HU-037 (Calcular total de la compra)
OPENAPI_CALCULATE_TOTAL_RESPONSES = {
    200: {
        "description": "Total de la compra calculado exitosamente",
        "model": TotalCalculationResponse,
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Total de la compra calculado exitosamente",
                    "data": {
                        "id_carrito": 701,
                        "moneda": "COP",
                        "subtotal": 2521008.0,
                        "impuestos": 478992.0,
                        "descuentos": 0.0,
                        "total_pagar": 3000000.0,
                    },
                    "success": True,
                }
            }
        },
    },
    400: {
        "description": "No se pudo identificar el carrito del usuario",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "No se pudo identificar el carrito del usuario",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    409: {
        "description": "Error por Regla de Negocio RN-37 (El carrito está vacío o contiene servicios expirados)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "El carrito está vacío o contiene servicios expirados que impiden liquidar",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    422: {
        "description": "Parámetros de entrada inválidos o incompletos (validación de esquema)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Parámetros de entrada inválidos o incompletos",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    503: {
        "description": "Falla de Disponibilidad (Error al calcular el total de la compra)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Error al calcular el total de la compra",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
}

# Documentación OpenAPI para HU-038 (Cerrar compra)
OPENAPI_CHECKOUT_RESPONSES = {
    201: {
        "description": "Compra cerrada exitosamente, pendiente de confirmación de pago",
        "model": CartCheckoutResponse,
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Compra cerrada exitosamente, pendiente de confirmación de pago",
                    "data": {
                        "id_carrito": 701,
                        "estado_carrito": "CERRADO",
                        "codigo_reserva_preliminar": "VS-2026-8841",
                        "total_liquidado": 3000000.0,
                        "moneda": "COP",
                    },
                    "success": True,
                }
            }
        },
    },
    400: {
        "description": "Datos de facturación o medio de pago incompletos o inválidos",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Datos de facturación o medio de pago incompletos",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    409: {
        "description": "Error por Regla de Negocio RN-38 (carrito ya cerrado o bloqueo caducado)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "El carrito ya fue cerrado previamente o algún bloqueo de servicio caducó",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    422: {
        "description": "Parámetros de entrada inválidos o incompletos (validación de esquema)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Parámetros de entrada inválidos o incompletos",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    503: {
        "description": "Falla de Disponibilidad (Indisponibilidad de servicios AIN-08, AIN-09, AIN-10 o AIN-14)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "No fue posible procesar el cierre de compra por indisponibilidad de servicios",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
}

# Documentación OpenAPI para HU-039 (Crear reserva)
OPENAPI_CREATE_RESERVATION_RESPONSES = {
    201: {
        "description": "Reserva creada exitosamente",
        "model": ReservationResponse,
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Reserva creada exitosamente",
                    "data": {
                        "id_reserva": 9001,
                        "codigo_reserva": "VS-2026-8841",
                        "id_usuario": 1,
                        "estado": "PENDIENTE_PAGO",
                        "total": 3000000.0,
                        "moneda": "COP",
                        "fecha_creacion": "2026-11-15T17:15:00Z",
                    },
                    "success": True,
                }
            }
        },
    },
    400: {
        "description": "Datos inválidos o carrito no encontrado para generar la reserva",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Datos inválidos o carrito no encontrado para generar la reserva",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    409: {
        "description": "Error por Regla de Negocio RN-39 (Ya existe una reserva generada para este carrito)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Ya existe una reserva generada para este carrito de compras",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    422: {
        "description": "Parámetros de entrada inválidos o incompletos (validación de esquema)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Parámetros de entrada inválidos o incompletos",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    503: {
        "description": "Falla de Disponibilidad (Indisponibilidad de servicios AIN-05, AIN-08, AIN-09 o AIN-10)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "No fue posible crear la reserva en este momento",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
}

# Documentación OpenAPI para HU-040 (Registrar viajeros)
OPENAPI_REGISTER_TRAVELERS_RESPONSES = {
    201: {
        "description": "Viajeros registrados en la reserva exitosamente",
        "model": RegisterTravelersResponse,
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Viajeros registrados en la reserva exitosamente",
                    "data": {
                        "id_reserva": 9001,
                        "codigo_reserva": "VS-2026-8841",
                        "total_viajeros_registrados": 2,
                        "estado_nominacion": "COMPLETA",
                    },
                    "success": True,
                }
            }
        },
    },
    400: {
        "description": "Datos de viajeros incompletos o tipo de documento inválido",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Datos de viajeros incompletos o tipo de documento inválido",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    409: {
        "description": "Error por Regla de Negocio RN-40 (Cantidad de viajeros no coincide con cupos o documentos duplicados)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "La cantidad de viajeros no coincide con los cupos o hay documentos duplicados",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    422: {
        "description": "Parámetros de entrada inválidos o incompletos (validación de esquema)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Parámetros de entrada inválidos o incompletos",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    503: {
        "description": "Falla de Disponibilidad (Indisponibilidad de servicios AIN-01 o AIN-05)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "No fue posible asociar los viajeros a la reserva",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
}

# Documentación OpenAPI para HU-043 (Cancelar reserva)
OPENAPI_CANCEL_RESERVATION_RESPONSES = {
    200: {
        "description": "Reserva cancelada exitosamente",
        "model": CancelReservationResponse,
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Reserva cancelada exitosamente",
                    "data": {
                        "id_reserva": 9001,
                        "codigo_reserva": "VS-2026-8841",
                        "estado_anterior": "CONFIRMADA",
                        "estado_actual": "CANCELADA",
                        "aplica_reembolso": True,
                        "fecha_cancelacion": "2026-11-16T10:00:00Z",
                    },
                    "success": True,
                }
            }
        },
    },
    400: {
        "description": "Debe proporcionar un motivo válido para cancelar la reserva",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Debe proporcionar un motivo válido para cancelar la reserva",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    409: {
        "description": "Error por Regla de Negocio RN-43 (La reserva ya se encuentra cancelada o en estado final)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "La reserva ya se encuentra cancelada o en un estado final que no permite anulación",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    422: {
        "description": "Parámetros de entrada inválidos o incompletos (validación de esquema)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Parámetros de entrada inválidos o incompletos",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    503: {
        "description": "Falla de Disponibilidad (No fue posible procesar la cancelación en este momento)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "No fue posible procesar la cancelación en este momento",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
}


@router.post(
    "/carrito/items",
    response_model=CartItemResponse,
    status_code=status.HTTP_201_CREATED,
    responses=OPENAPI_ADD_ITEM_RESPONSES,
    summary="Agregar ítem al carrito (HU-033)",
    description="Añade un servicio validado (vuelo, hotel o paquete) al carrito activo del viajero verificando vigencia y no duplicidad del bloqueo bajo RN-33.",
)
def add_cart_item(payload: CartItemCreate):
    load_dotenv(override=True)
    simulate_env_failure = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() in ("true", "1", "yes")
    is_simulated_failure = (
        payload.user_id == 503
        or payload.lock_reference_id.strip().upper() in ("BLK-503", "503")
    )

    if simulate_env_failure or is_simulated_failure:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible actualizar el carrito de compras en este momento",
                "data": None,
                "success": False,
            },
        )

    try:
        return service.add_cart_item(payload)
    except BusinessRuleRN33Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except InvalidCartItemDataException as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except CartServicesUnavailableException as exc:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible actualizar el carrito de compras en este momento",
                "data": None,
                "success": False,
            },
        )


@router.get(
    "/carrito",
    response_model=CartQueryResponse,
    status_code=status.HTTP_200_OK,
    responses=OPENAPI_GET_CART_RESPONSES,
    summary="Consultar carrito (HU-035)",
    description="Retorna el detalle completo del carrito activo del viajero verificando la vigencia de los bloqueos temporales de cada ítem bajo RN-35.",
)
def get_cart(
    user_id: Optional[int] = Query(default=1, alias="id_usuario", description="Identificador del usuario titular del carrito (ej: 1)"),
):
    load_dotenv(override=True)
    simulate_env_failure = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() in ("true", "1", "yes")
    is_simulated_failure = user_id == 503

    if simulate_env_failure or is_simulated_failure:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible recuperar el carrito de compras",
                "data": None,
                "success": False,
            },
        )

    try:
        return service.get_cart(user_id=user_id)
    except BusinessRuleRN35Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except InvalidCartUserException as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except CartQueryServicesUnavailableException as exc:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible recuperar el carrito de compras",
                "data": None,
                "success": False,
            },
        )


@router.get(
    "/carrito/total",
    response_model=TotalCalculationResponse,
    status_code=status.HTTP_200_OK,
    responses=OPENAPI_CALCULATE_TOTAL_RESPONSES,
    summary="Calcular total de la compra (HU-037)",
    description="Liquida matemáticamente el valor exacto consolidado del carrito incluyendo subtotal, impuestos y descuentos aplicando precisión decimal según AIN-05 y validando RN-37.",
)
def calculate_purchase_total(
    user_id: Optional[int] = Query(default=1, alias="id_usuario", description="Identificador del usuario titular del carrito (ej: 1)"),
):
    load_dotenv(override=True)
    simulate_env_failure = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() in ("true", "1", "yes")
    is_simulated_failure = user_id == 503

    if simulate_env_failure or is_simulated_failure:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "Error al calcular el total de la compra",
                "data": None,
                "success": False,
            },
        )

    try:
        return service.calculate_purchase_total(user_id=user_id)
    except BusinessRuleRN37Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except UnidentifiedCartException as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except TotalCalculationServicesUnavailableException as exc:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "Error al calcular el total de la compra",
                "data": None,
                "success": False,
            },
        )


@router.post(
    "/carrito/cierre",
    response_model=CartCheckoutResponse,
    status_code=status.HTTP_201_CREATED,
    responses=OPENAPI_CHECKOUT_RESPONSES,
    summary="Cerrar compra (HU-038)",
    description="Ejecuta el cierre formal del carrito de compras transicionándolo de ABIERTO a CERRADO, revalidando identidad (AIN-08), bloqueos (AIN-09, AIN-10) e iniciando el cobro (AIN-14) bajo RN-38.",
)
def close_purchase(payload: CartCheckoutCreate):
    load_dotenv(override=True)
    simulate_env_failure = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() in ("true", "1", "yes")
    is_simulated_failure = payload.cart_id == 503 or payload.user_id == 503

    if simulate_env_failure or is_simulated_failure:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible procesar el cierre de compra por indisponibilidad de servicios",
                "data": None,
                "success": False,
            },
        )

    try:
        return service.close_purchase(payload)
    except BusinessRuleRN38Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except InvalidCheckoutDataException as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except CheckoutServicesUnavailableException as exc:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible procesar el cierre de compra por indisponibilidad de servicios",
                "data": None,
                "success": False,
            },
        )


@router.post(
    "",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
    responses=OPENAPI_CREATE_RESERVATION_RESPONSES,
    summary="Crear reserva (HU-039)",
    description="Crea el registro maestro de la reserva con un código único localizador (VS-YYYY-XXXX) en estado PENDIENTE_PAGO consultando AIN-05 y validando RN-39.",
)
def create_reservation(payload: ReservationCreate):
    load_dotenv(override=True)
    simulate_env_failure = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() in ("true", "1", "yes")
    is_simulated_failure = payload.cart_id == 503 or payload.user_id == 503

    if simulate_env_failure or is_simulated_failure:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible crear la reserva en este momento",
                "data": None,
                "success": False,
            },
        )

    try:
        return service.create_reservation(payload)
    except BusinessRuleRN39Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except InvalidReservationDataException as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except ReservationServicesUnavailableException as exc:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible crear la reserva en este momento",
                "data": None,
                "success": False,
            },
        )


@router.post(
    "/{id_reserva}/viajeros",
    response_model=RegisterTravelersResponse,
    status_code=status.HTTP_201_CREATED,
    responses=OPENAPI_REGISTER_TRAVELERS_RESPONSES,
    summary="Registrar viajeros (HU-040)",
    description="Registra el listado nominal de viajeros en la reserva validando tipos de documento en AIN-01 y verificando coincidencia de cupos y unicidad de documento bajo RN-40.",
)
def register_travelers(
    payload: RegisterTravelersCreate,
    reservation_id: int = Path(..., alias="id_reserva", gt=0, description="Identificador único de la reserva (ej: 9001)"),
):
    load_dotenv(override=True)
    simulate_env_failure = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() in ("true", "1", "yes")
    is_simulated_failure = reservation_id == 503

    if simulate_env_failure or is_simulated_failure:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible asociar los viajeros a la reserva",
                "data": None,
                "success": False,
            },
        )

    try:
        return service.register_travelers(reservation_id=reservation_id, data=payload)
    except BusinessRuleRN40Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except InvalidTravelersDataException as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except TravelersServicesUnavailableException as exc:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible asociar los viajeros a la reserva",
                "data": None,
                "success": False,
            },
        )


@router.post(
    "/{id_reserva}/cancelacion",
    response_model=CancelReservationResponse,
    status_code=status.HTTP_200_OK,
    responses=OPENAPI_CANCEL_RESERVATION_RESPONSES,
    summary="Cancelar reserva (HU-043)",
    description="Ejecuta la cancelación controlada de la reserva validando que su estado admita anulación en AIN-05 bajo RN-43 y notificando vía AIN-16.",
)
def cancel_reservation(
    payload: CancelReservationCreate,
    reservation_id: int = Path(..., alias="id_reserva", gt=0, description="Identificador único de la reserva a cancelar (ej: 9001)"),
):
    load_dotenv(override=True)
    simulate_env_failure = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() in ("true", "1", "yes")
    is_simulated_failure = reservation_id == 503 or payload.user_id == 503

    if simulate_env_failure or is_simulated_failure:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible procesar la cancelación en este momento",
                "data": None,
                "success": False,
            },
        )

    try:
        return service.cancel_reservation(reservation_id=reservation_id, data=payload)
    except BusinessRuleRN43Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except InvalidCancellationReasonException as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except CancellationServicesUnavailableException as exc:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"mensaje": str(exc), "data": None, "success": False},
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible procesar la cancelación en este momento",
                "data": None,
                "success": False,
            },
        )
