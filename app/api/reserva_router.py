import os
from dotenv import load_dotenv
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.domain.reserva import (
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
)
from app.services.reserva_service import ReservaService
from app.repositories.reserva_repository import reserva_repository

router = APIRouter(
    prefix="/api/v1/reservas",
    tags=["Compra y Reservas"],
)

servicio = ReservaService(repo=reserva_repository)

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
    # Recargar variables de entorno dinámicamente
    load_dotenv(override=True)
    simular_falla_env = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() in ("true", "1", "yes")

    # Caso 4: Simulación de fallo de disponibilidad (503 Service Unavailable)
    # Se activa con SIMULAR_FALLA_SERVIDOR="True" en .env o enviando id_carrito=503 o id_usuario=503
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
        # Caso 2: Error por Regla de Negocio RN-39 -> 409 Conflict
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "mensaje": str(e),
                "data": None,
                "success": False,
            },
        )
    except DatosReservaInvalidosException as e:
        # Caso 3: Error de Validación -> 400 Bad Request
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "mensaje": str(e),
                "data": None,
                "success": False,
            },
        )
    except ServiciosReservaNoDisponiblesException as e:
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
                "mensaje": "No fue posible crear la reserva en este momento",
                "data": None,
                "success": False,
            },
        )
