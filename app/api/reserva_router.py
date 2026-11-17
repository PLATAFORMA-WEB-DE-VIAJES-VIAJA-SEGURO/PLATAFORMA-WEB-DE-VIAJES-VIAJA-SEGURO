import os
from typing import Optional
from dotenv import load_dotenv
from fastapi import APIRouter, Path, Query, status
from fastapi.responses import JSONResponse
from app.domain.reserva import (
    ItemCarritoCreate,
    ItemCarritoResponse,
    ReglaNegocioRN33Exception,
    DatosItemCarritoInvalidosException,
    ServiciosCarritoNoDisponiblesException,
    ConsultaCarritoResponse,
    ReglaNegocioRN35Exception,
    UsuarioCarritoInvalidoException,
    ServiciosConsultaCarritoNoDisponiblesException,
    CalculoTotalResponse,
    ReglaNegocioRN37Exception,
    CarritoNoIdentificadoException,
    ServiciosCalculoTotalNoDisponiblesException,
    CierreCarritoCreate,
    CierreCarritoResponse,
    ReglaNegocioRN38Exception,
    DatosCierreCompraInvalidosException,
    ServiciosCierreNoDisponiblesException,
    ReservaCreate,
    ReservaResponse,
    ReglaNegocioRN39Exception,
    DatosReservaInvalidosException,
    ServiciosReservaNoDisponiblesException,
    RegistrarViajerosCreate,
    RegistrarViajerosResponse,
    ReglaNegocioRN40Exception,
    DatosViajerosInvalidosException,
    ServiciosViajerosNoDisponiblesException,
    CancelarReservaCreate,
    CancelarReservaResponse,
    ReglaNegocioRN43Exception,
    MotivoCancelacionInvalidoException,
    ServiciosCancelacionNoDisponiblesException,
)
from app.services.reserva_service import ReservaService
from app.repositories.reserva_repository import reserva_repository

router = APIRouter(
    prefix="/api/v1/reservas",
    tags=["Compra y Reservas"],
)

servicio = ReservaService(repo=reserva_repository)

# Documentación OpenAPI para HU-033 (Agregar ítem al carrito)
RESPUESTAS_OPENAPI_AGREGAR_ITEM = {
    201: {
        "description": "Ítem agregado al carrito exitosamente",
        "model": ItemCarritoResponse,
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
RESPUESTAS_OPENAPI_CONSULTAR_CARRITO = {
    200: {
        "description": "Carrito consultado exitosamente",
        "model": ConsultaCarritoResponse,
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
RESPUESTAS_OPENAPI_CALCULAR_TOTAL = {
    200: {
        "description": "Total de la compra calculado exitosamente",
        "model": CalculoTotalResponse,
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
RESPUESTAS_OPENAPI_CIERRE_COMPRA = {
    201: {
        "description": "Compra cerrada exitosamente, pendiente de confirmación de pago",
        "model": CierreCarritoResponse,
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
RESPUESTAS_OPENAPI_CREAR_RESERVA = {
    201: {
        "description": "Reserva creada exitosamente",
        "model": ReservaResponse,
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
RESPUESTAS_OPENAPI_REGISTRAR_VIAJEROS = {
    201: {
        "description": "Viajeros registrados en la reserva exitosamente",
        "model": RegistrarViajerosResponse,
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
RESPUESTAS_OPENAPI_CANCELAR_RESERVA = {
    200: {
        "description": "Reserva cancelada exitosamente",
        "model": CancelarReservaResponse,
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
    response_model=ItemCarritoResponse,
    status_code=status.HTTP_201_CREATED,
    responses=RESPUESTAS_OPENAPI_AGREGAR_ITEM,
    summary="Agregar ítem al carrito (HU-033)",
    description="Añade un servicio validado (vuelo, hotel o paquete) al carrito activo del viajero verificando vigencia y no duplicidad del bloqueo bajo RN-33.",
)
def agregar_item_carrito(payload: ItemCarritoCreate):
    load_dotenv(override=True)
    simular_falla_env = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() in ("true", "1", "yes")
    es_simulacion_falla = (
        payload.id_usuario == 503
        or payload.id_referencia_bloqueo.strip().upper() in ("BLK-503", "503")
    )

    if simular_falla_env or es_simulacion_falla:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible actualizar el carrito de compras en este momento",
                "data": None,
                "success": False,
            },
        )

    try:
        return servicio.agregar_item_carrito(payload)
    except ReglaNegocioRN33Exception as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(e), "data": None, "success": False},
        )
    except DatosItemCarritoInvalidosException as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(e), "data": None, "success": False},
        )
    except ServiciosCarritoNoDisponiblesException as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"mensaje": str(e), "data": None, "success": False},
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
    response_model=ConsultaCarritoResponse,
    status_code=status.HTTP_200_OK,
    responses=RESPUESTAS_OPENAPI_CONSULTAR_CARRITO,
    summary="Consultar carrito (HU-035)",
    description="Retorna el detalle completo del carrito activo del viajero verificando la vigencia de los bloqueos temporales de cada ítem bajo RN-35.",
)
def consultar_carrito(
    id_usuario: Optional[int] = Query(default=1, description="Identificador del usuario titular del carrito (ej: 1)"),
):
    load_dotenv(override=True)
    simular_falla_env = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() in ("true", "1", "yes")
    es_simulacion_falla = id_usuario == 503

    if simular_falla_env or es_simulacion_falla:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible recuperar el carrito de compras",
                "data": None,
                "success": False,
            },
        )

    try:
        return servicio.consultar_carrito(id_usuario=id_usuario)
    except ReglaNegocioRN35Exception as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(e), "data": None, "success": False},
        )
    except UsuarioCarritoInvalidoException as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(e), "data": None, "success": False},
        )
    except ServiciosConsultaCarritoNoDisponiblesException as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"mensaje": str(e), "data": None, "success": False},
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
    response_model=CalculoTotalResponse,
    status_code=status.HTTP_200_OK,
    responses=RESPUESTAS_OPENAPI_CALCULAR_TOTAL,
    summary="Calcular total de la compra (HU-037)",
    description="Liquida matemáticamente el valor exacto consolidado del carrito incluyendo subtotal, impuestos y descuentos aplicando precisión decimal según AIN-05 y validando RN-37.",
)
def calcular_total_compra(
    id_usuario: Optional[int] = Query(default=1, description="Identificador del usuario titular del carrito (ej: 1)"),
):
    load_dotenv(override=True)
    simular_falla_env = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() in ("true", "1", "yes")
    es_simulacion_falla = id_usuario == 503

    if simular_falla_env or es_simulacion_falla:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "Error al calcular el total de la compra",
                "data": None,
                "success": False,
            },
        )

    try:
        return servicio.calcular_total_compra(id_usuario=id_usuario)
    except ReglaNegocioRN37Exception as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(e), "data": None, "success": False},
        )
    except CarritoNoIdentificadoException as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(e), "data": None, "success": False},
        )
    except ServiciosCalculoTotalNoDisponiblesException as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"mensaje": str(e), "data": None, "success": False},
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
    response_model=CierreCarritoResponse,
    status_code=status.HTTP_201_CREATED,
    responses=RESPUESTAS_OPENAPI_CIERRE_COMPRA,
    summary="Cerrar compra (HU-038)",
    description="Ejecuta el cierre formal del carrito de compras transicionándolo de ABIERTO a CERRADO, revalidando identidad (AIN-08), bloqueos (AIN-09, AIN-10) e iniciando el cobro (AIN-14) bajo RN-38.",
)
def cerrar_compra(payload: CierreCarritoCreate):
    load_dotenv(override=True)
    simular_falla_env = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() in ("true", "1", "yes")
    es_simulacion_falla = payload.id_carrito == 503 or payload.id_usuario == 503

    if simular_falla_env or es_simulacion_falla:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible procesar el cierre de compra por indisponibilidad de servicios",
                "data": None,
                "success": False,
            },
        )

    try:
        return servicio.cerrar_compra(payload)
    except ReglaNegocioRN38Exception as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(e), "data": None, "success": False},
        )
    except DatosCierreCompraInvalidosException as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(e), "data": None, "success": False},
        )
    except ServiciosCierreNoDisponiblesException as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"mensaje": str(e), "data": None, "success": False},
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
    response_model=ReservaResponse,
    status_code=status.HTTP_201_CREATED,
    responses=RESPUESTAS_OPENAPI_CREAR_RESERVA,
    summary="Crear reserva (HU-039)",
    description="Crea el registro maestro de la reserva con un código único localizador (VS-YYYY-XXXX) en estado PENDIENTE_PAGO consultando AIN-05 y validando RN-39.",
)
def crear_reserva(payload: ReservaCreate):
    load_dotenv(override=True)
    simular_falla_env = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() in ("true", "1", "yes")
    es_simulacion_falla = payload.id_carrito == 503 or payload.id_usuario == 503

    if simular_falla_env or es_simulacion_falla:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible crear la reserva en este momento",
                "data": None,
                "success": False,
            },
        )

    try:
        return servicio.crear_reserva(payload)
    except ReglaNegocioRN39Exception as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(e), "data": None, "success": False},
        )
    except DatosReservaInvalidosException as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(e), "data": None, "success": False},
        )
    except ServiciosReservaNoDisponiblesException as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"mensaje": str(e), "data": None, "success": False},
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
    response_model=RegistrarViajerosResponse,
    status_code=status.HTTP_201_CREATED,
    responses=RESPUESTAS_OPENAPI_REGISTRAR_VIAJEROS,
    summary="Registrar viajeros (HU-040)",
    description="Registra el listado nominal de viajeros en la reserva validando tipos de documento en AIN-01 y verificando coincidencia de cupos y unicidad de documento bajo RN-40.",
)
def registrar_viajeros(
    payload: RegistrarViajerosCreate,
    id_reserva: int = Path(..., gt=0, description="Identificador único de la reserva (ej: 9001)"),
):
    load_dotenv(override=True)
    simular_falla_env = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() in ("true", "1", "yes")
    es_simulacion_falla = id_reserva == 503

    if simular_falla_env or es_simulacion_falla:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible asociar los viajeros a la reserva",
                "data": None,
                "success": False,
            },
        )

    try:
        return servicio.registrar_viajeros(id_reserva=id_reserva, datos=payload)
    except ReglaNegocioRN40Exception as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"mensaje": str(e), "data": None, "success": False},
        )
    except DatosViajerosInvalidosException as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"mensaje": str(e), "data": None, "success": False},
        )
    except ServiciosViajerosNoDisponiblesException as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"mensaje": str(e), "data": None, "success": False},
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
    response_model=CancelarReservaResponse,
    status_code=status.HTTP_200_OK,
    responses=RESPUESTAS_OPENAPI_CANCELAR_RESERVA,
    summary="Cancelar reserva (HU-043)",
    description="Ejecuta la cancelación controlada de la reserva validando que su estado admita anulación en AIN-05 bajo RN-43 y notificando vía AIN-16.",
)
def cancelar_reserva(
    payload: CancelarReservaCreate,
    id_reserva: int = Path(..., gt=0, description="Identificador único de la reserva a cancelar (ej: 9001)"),
):
    load_dotenv(override=True)
    simular_falla_env = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() in ("true", "1", "yes")

    # Caso 4: Simulación de fallo de disponibilidad (503 Service Unavailable)
    es_simulacion_falla = id_reserva == 503 or payload.id_usuario == 503

    if simular_falla_env or es_simulacion_falla:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible procesar la cancelación en este momento",
                "data": None,
                "success": False,
            },
        )

    try:
        return servicio.cancelar_reserva(id_reserva=id_reserva, datos=payload)
    except ReglaNegocioRN43Exception as e:
        # Caso 2: Error por Regla de Negocio RN-43 -> 409 Conflict
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "mensaje": str(e),
                "data": None,
                "success": False,
            },
        )
    except MotivoCancelacionInvalidoException as e:
        # Caso 3: Error de Validación -> 400 Bad Request
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "mensaje": str(e),
                "data": None,
                "success": False,
            },
        )
    except ServiciosCancelacionNoDisponiblesException as e:
        # Caso 4: Falla de Disponibilidad -> 503 Service Unavailable
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": str(e),
                "data": None,
                "success": False,
            },
        )
    except Exception:
        # Fallos imprevistos ocultando trazas técnicas -> 503
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible procesar la cancelación en este momento",
                "data": None,
                "success": False,
            },
        )
