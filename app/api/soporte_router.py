import os
from dotenv import load_dotenv
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.domain.soporte import (
    CasoSoporteCreate,
    CasoSoporteResponse,
    ReglaNegocioRN51Exception,
    ServicioNoDisponibleException,
    ValidacionParametrosException
)
from app.services.soporte_service import SoporteService
from app.repositories.soporte_repository import soporte_repository

router = APIRouter(
    prefix="/api/v1/soporte",
    tags=["Soporte - Casos"]
)

# Inyección de dependencias
servicio = SoporteService(repo=soporte_repository)

# Esquemas y ejemplos para documentación OpenAPI / Swagger
RESPUESTAS_OPENAPI = {
    201: {
        "description": "Caso de soporte radicado exitosamente",
        "model": CasoSoporteResponse,
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
                        "fecha_radicacion": "2026-11-16T11:20:00Z"
                    },
                    "success": True
                }
            }
        }
    },
    400: {
        "description": "Parámetros inválidos o datos obligatorios faltantes",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "El tipo de caso, asunto o descripción son obligatorios",
                    "data": None,
                    "success": False
                }
            }
        }
    },
    409: {
        "description": "Violación de regla de negocio RN-51 (Caso duplicado para la misma reserva)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Ya existe un caso abierto idéntico para la misma reserva",
                    "data": None,
                    "success": False
                }
            }
        }
    },
    503: {
        "description": "Falla de disponibilidad en almacenamiento o dependencias externas",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "No fue posible radicar el caso de soporte en este momento",
                    "data": None,
                    "success": False
                }
            }
        }
    }
}

@router.post(
    "/casos",
    response_model=CasoSoporteResponse,
    status_code=status.HTTP_201_CREATED,
    responses=RESPUESTAS_OPENAPI,
    summary="Radicar caso de soporte (HU-051)",
    description="Endpoint para registrar formalmente una solicitud o PQR generando número único de radicado en estado ABIERTO."
)
def radicar_caso(datos: CasoSoporteCreate):
    # Recargar variables de entorno dinámicamente desde .env
    load_dotenv(override=True)
    simular_falla_env = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() in ("true", "1", "yes")

    # Caso 4 de pruebas: Falla de Disponibilidad (503 Service Unavailable)
    # Se activa si la variable de entorno SIMULAR_FALLA_SERVIDOR está en True
    # O si el código de reserva enviado es exactamente "VS-2026-503"
    es_codigo_simulacion = bool(datos.codigo_reserva and datos.codigo_reserva.strip().upper() == "VS-2026-503")

    if simular_falla_env or es_codigo_simulacion:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible radicar el caso de soporte en este momento",
                "data": None,
                "success": False
            }
        )

    try:
        resultado = servicio.radicar_caso(datos)
        return resultado
    except ReglaNegocioRN51Exception as e:
        # Caso 2: Error por Regla de Negocio RN-51 -> 409 Conflict
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
    except ServicioNoDisponibleException as e:
        # Caso 4: Error de Disponibilidad lanzado desde repository/service -> 503
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": str(e),
                "data": None,
                "success": False
            }
        )
    except Exception:
        # Fallos internos imprevistos -> 503 Service Unavailable
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible radicar el caso de soporte en este momento",
                "data": None,
                "success": False
            }
        )
