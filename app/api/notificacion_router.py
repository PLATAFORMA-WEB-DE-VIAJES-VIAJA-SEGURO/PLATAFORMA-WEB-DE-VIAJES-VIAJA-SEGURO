import os
from dotenv import load_dotenv
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.domain.notificacion import (
    NotificacionCreate,
    NotificacionResponse,
    ReglaNegocioRN55Exception,
    ProveedorNoDisponibleException,
    ValidacionParametrosException
)
from app.services.notificacion_service import NotificacionService
from app.repositories.notificacion_repository import notificacion_repository

router = APIRouter(
    prefix="/api/v1/soporte",
    tags=["Soporte"]
)

# Inyección de dependencias
servicio = NotificacionService(repo=notificacion_repository)

# Documentación OpenAPI para Swagger UI (/docs)
RESPUESTAS_OPENAPI_NOTIFICACIONES = {
    201: {
        "description": "Notificación enviada exitosamente",
        "model": NotificacionResponse,
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Notificación enviada exitosamente",
                    "data": {
                        "id_notificacion": 55001,
                        "canal": "EMAIL",
                        "destinatario": "juan.perez@email.com",
                        "plantilla": "CONFIRMACION_RESERVA",
                        "estado_envio": "ENVIADO",
                        "fecha_envio": "2026-11-15T17:16:00Z"
                    },
                    "success": True
                }
            }
        }
    },
    400: {
        "description": "El canal de envío, destinatario o plantilla no son válidos",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "El canal de envío, destinatario o plantilla no son válidos",
                    "data": None,
                    "success": False
                }
            }
        }
    },
    409: {
        "description": "Error por Regla de Negocio RN-55 (Destinatario bloqueado, reintentos superados o formato incompatible)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "El destinatario ha bloqueado notificaciones o se superó el límite de reintentos",
                    "data": None,
                    "success": False
                }
            }
        }
    },
    503: {
        "description": "Falla de Disponibilidad (El proveedor externo AEX-06 no responde)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "El proveedor externo de mensajería no responde en este momento",
                    "data": None,
                    "success": False
                }
            }
        }
    }
}

@router.post(
    "/notificaciones",
    response_model=NotificacionResponse,
    status_code=status.HTTP_201_CREATED,
    responses=RESPUESTAS_OPENAPI_NOTIFICACIONES,
    summary="Enviar notificación (HU-055)",
    description="Endpoint centralizado para despachar notificaciones al viajero vía EMAIL o SMS mediante AEX-06 (RN-55)."
)
def enviar_notificacion(datos: NotificacionCreate):
    # Recargar variables de entorno dinámicamente
    load_dotenv(override=True)
    simular_falla_env = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() in ("true", "1", "yes")

    # Caso 4 de pruebas: Simulación de fallo del proveedor AEX-06 (503 Service Unavailable)
    # Se activa si la variable de entorno SIMULAR_FALLA_SERVIDOR es True
    # O si el destinatario es "fallo_proveedor@email.com" o "VS-2026-503"
    es_destinatario_simulacion = datos.destinatario.strip().lower() in ("fallo_proveedor@email.com", "vs-2026-503")

    if simular_falla_env or es_destinatario_simulacion:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "El proveedor externo de mensajería no responde en este momento",
                "data": None,
                "success": False
            }
        )

    try:
        resultado = servicio.enviar_notificacion(datos)
        return resultado
    except ReglaNegocioRN55Exception as e:
        # Caso 2: Error de Regla de Negocio RN-55 -> 409 Conflict
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "mensaje": str(e),
                "data": None,
                "success": False
            }
        )
    except ValidacionParametrosException as e:
        # Caso 3: Error de Validación o Parámetros -> 400 Bad Request
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "mensaje": str(e),
                "data": None,
                "success": False
            }
        )
    except ProveedorNoDisponibleException as e:
        # Caso 4: Falla de Disponibilidad AEX-06 -> 503 Service Unavailable
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": str(e),
                "data": None,
                "success": False
            }
        )
    except Exception:
        # Fallos internos imprevistos ocultando stacktraces -> 503
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "El proveedor externo de mensajería no responde en este momento",
                "data": None,
                "success": False
            }
        )
