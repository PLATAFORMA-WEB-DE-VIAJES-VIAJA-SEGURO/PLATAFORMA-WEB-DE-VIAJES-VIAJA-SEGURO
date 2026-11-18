import os
from dotenv import load_dotenv
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.domain.soporte import (
    SupportCaseCreate,
    SupportCaseResponse,
    BusinessRuleRN51Exception,
    SupportServiceUnavailableException,
    SupportParameterValidationException,
)
from app.services.soporte_service import SupportService
from app.repositories.soporte_repository import support_repository

router = APIRouter(
    prefix="/api/v1/soporte",
    tags=["Soporte"],
)

# Inyección de dependencias
service = SupportService(repo=support_repository)

# Esquemas y ejemplos para documentación OpenAPI / Swagger
OPENAPI_SUPPORT_RESPONSES = {
    201: {
        "description": "Caso de soporte radicado exitosamente",
        "model": SupportCaseResponse,
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Caso de soporte radicado exitosamente",
                    "data": {
                        "id_caso": 51001,
                        "numero_radicado": "PQR-2026-0045",
                        "id_usuario": 1,
                        "tipo_caso": "MODIFICACION_ITINERARIO",
                        "estado": "ABIERTO",
                        "fecha_radicacion": "2026-11-16T11:20:00Z",
                    },
                    "success": True,
                }
            }
        },
    },
    400: {
        "description": "Parámetros inválidos o datos obligatorios faltantes",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "El tipo de caso, asunto o descripción son obligatorios",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    409: {
        "description": "Violación de regla de negocio RN-51 (Caso duplicado para la misma reserva)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Ya existe un caso abierto idéntico para la misma reserva",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    503: {
        "description": "Falla de disponibilidad en almacenamiento o dependencias externas",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "No fue posible radicar el caso de soporte en este momento",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
}


@router.post(
    "/casos",
    response_model=SupportCaseResponse,
    status_code=status.HTTP_201_CREATED,
    responses=OPENAPI_SUPPORT_RESPONSES,
    summary="Radicar caso de soporte (HU-051)",
    description="Endpoint para registrar formalmente una solicitud o PQR generando número único de radicado en estado ABIERTO.",
)
def file_support_case(payload: SupportCaseCreate):
    # Recargar variables de entorno dinámicamente desde .env
    load_dotenv(override=True)
    simulate_env_failure = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() in ("true", "1", "yes")

    # Caso 4 de pruebas: Falla de Disponibilidad (503 Service Unavailable)
    is_simulated_code = bool(payload.reservation_code and payload.reservation_code.strip().upper() == "VS-2026-503")

    if simulate_env_failure or is_simulated_code:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible radicar el caso de soporte en este momento",
                "data": None,
                "success": False,
            },
        )

    try:
        return service.file_case(payload)
    except BusinessRuleRN51Exception as exc:
        # Caso 2: Error por Regla de Negocio RN-51 -> 409 Conflict
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "mensaje": str(exc),
                "data": None,
                "success": False,
            },
        )
    except SupportParameterValidationException as exc:
        # Caso 3: Error de Validación o Parámetros -> 400 Bad Request
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "mensaje": str(exc),
                "data": None,
                "success": False,
            },
        )
    except SupportServiceUnavailableException as exc:
        # Caso 4: Error de Disponibilidad lanzado desde repository/service -> 503
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": str(exc),
                "data": None,
                "success": False,
            },
        )
    except Exception:
        # Fallos internos imprevistos -> 503 Service Unavailable
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible radicar el caso de soporte en este momento",
                "data": None,
                "success": False,
            },
        )
