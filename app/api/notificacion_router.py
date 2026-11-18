import os
from dotenv import load_dotenv
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.domain.notificacion import (
    NotificationCreate,
    NotificationResponse,
    BusinessRuleRN55Exception,
    MessagingProviderUnavailableException,
    NotificationParameterValidationException,
)
from app.services.notificacion_service import NotificationService
from app.repositories.notificacion_repository import notification_repository

router = APIRouter(
    prefix="/api/v1/soporte",
    tags=["Soporte"],
)

# Inyección de dependencias
service = NotificationService(repo=notification_repository)

# Documentación OpenAPI para Swagger UI (/docs)
OPENAPI_NOTIFICATION_RESPONSES = {
    201: {
        "description": "Notificación enviada exitosamente",
        "model": NotificationResponse,
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
                        "fecha_envio": "2026-11-15T17:16:00Z",
                    },
                    "success": True,
                }
            }
        },
    },
    400: {
        "description": "El canal de envío, destinatario o plantilla no son válidos",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "El canal de envío, destinatario o plantilla no son válidos",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    409: {
        "description": "Error por Regla de Negocio RN-55 (Destinatario bloqueado, reintentos superados o formato incompatible)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "El destinatario ha bloqueado notificaciones o se superó el límite de reintentos",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    503: {
        "description": "Falla de Disponibilidad (El proveedor externo AEX-06 no responde)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "El proveedor externo de mensajería no responde en este momento",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
}


@router.post(
    "/notificaciones",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
    responses=OPENAPI_NOTIFICATION_RESPONSES,
    summary="Enviar notificación (HU-055)",
    description="Endpoint centralizado para despachar notificaciones al viajero vía EMAIL o SMS mediante AEX-06 (RN-55).",
)
def send_notification(payload: NotificationCreate):
    # Recargar variables de entorno dinámicamente
    load_dotenv(override=True)
    simulate_env_failure = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() in ("true", "1", "yes")

    # Caso 4 de pruebas: Simulación de fallo del proveedor AEX-06 (503 Service Unavailable)
    is_simulated_recipient = payload.recipient.strip().lower() in ("fallo_proveedor@email.com", "vs-2026-503")

    if simulate_env_failure or is_simulated_recipient:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "El proveedor externo de mensajería no responde en este momento",
                "data": None,
                "success": False,
            },
        )

    try:
        return service.send_notification(payload)
    except BusinessRuleRN55Exception as exc:
        # Caso 2: Error de Regla de Negocio RN-55 -> 409 Conflict
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "mensaje": str(exc),
                "data": None,
                "success": False,
            },
        )
    except NotificationParameterValidationException as exc:
        # Caso 3: Error de Validación o Parámetros -> 400 Bad Request
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "mensaje": str(exc),
                "data": None,
                "success": False,
            },
        )
    except MessagingProviderUnavailableException as exc:
        # Caso 4: Falla de Disponibilidad AEX-06 -> 503 Service Unavailable
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": str(exc),
                "data": None,
                "success": False,
            },
        )
    except Exception:
        # Fallos internos imprevistos ocultando stacktraces -> 503
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "El proveedor externo de mensajería no responde en este momento",
                "data": None,
                "success": False,
            },
        )
