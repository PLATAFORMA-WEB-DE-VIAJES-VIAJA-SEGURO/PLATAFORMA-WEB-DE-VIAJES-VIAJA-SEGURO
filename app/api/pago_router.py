import os
from typing import Optional
from dotenv import load_dotenv
from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse
from app.domain.pago import (
    MediosPagoResponse,
    ReglaNegocioRN45Exception,
    MonedaNoSoportadaException,
    PasarelaNoDisponibleException
)
from app.services.pago_service import PagoService
from app.repositories.pago_repository import pago_repository

router = APIRouter(
    prefix="/api/v1/pagos",
    tags=["Pagos - Medios"]
)

servicio = PagoService(repo=pago_repository)

# Documentación OpenAPI para Swagger UI (/docs)
RESPUESTAS_OPENAPI_PAGOS = {
    200: {
        "description": "Medios de pago consultados exitosamente",
        "model": MediosPagoResponse,
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Medios de pago consultados exitosamente",
                    "data": {
                        "moneda": "COP",
                        "medios_pago": [
                            {
                                "codigo": "TC_VISA",
                                "nombre": "Tarjeta de Crédito Visa",
                                "tipo": "TARJETA_CREDITO",
                                "activo": True
                            },
                            {
                                "codigo": "PSE",
                                "nombre": "Transferencia Bancaria PSE",
                                "tipo": "DEBITO_BANCARIO",
                                "activo": True
                            }
                        ]
                    },
                    "success": True
                }
            }
        }
    },
    400: {
        "description": "Código de moneda no soportado o inválido",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Código de moneda no soportado",
                    "data": None,
                    "success": False
                }
            }
        }
    },
    409: {
        "description": "Error por Regla de Negocio RN-45 (No hay medios de pago activos para la moneda)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "No hay medios de pago habilitados temporalmente para esta moneda",
                    "data": None,
                    "success": False
                }
            }
        }
    },
    503: {
        "description": "Falla de Disponibilidad (La pasarela AEX-04 no se encuentra disponible)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "La pasarela de pagos no se encuentra disponible",
                    "data": None,
                    "success": False
                }
            }
        }
    }
}

@router.get(
    "/medios",
    response_model=MediosPagoResponse,
    status_code=status.HTTP_200_OK,
    responses=RESPUESTAS_OPENAPI_PAGOS,
    summary="Consultar medios de pago vigentes (HU-045)",
    description="Retorna las alternativas y métodos de pago financieros activos habilitados por la pasarela AEX-04 y AIN-06."
)
def consultar_medios_pago(
    moneda: Optional[str] = Query("COP", description="Código ISO de la moneda (por defecto COP, ej: USD, EUR)")
):
    # Recargar variables de entorno dinámicamente
    load_dotenv(override=True)
    simular_falla_env = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() in ("true", "1", "yes")

    # Caso 4 de pruebas: Simulación de fallo de pasarela AEX-04 (503 Service Unavailable)
    # Activado si SIMULAR_FALLA_SERVIDOR="True" en .env o si se consulta con moneda="503" o "FAIL"
    es_simulacion_falla = (moneda or "").strip().upper() in ("503", "FAIL", "VS-2026-503")

    if simular_falla_env or es_simulacion_falla:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "La pasarela de pagos no se encuentra disponible",
                "data": None,
                "success": False
            }
        )

    try:
        resultado = servicio.consultar_medios_pago(moneda=moneda)
        return resultado
    except ReglaNegocioRN45Exception as e:
        # Caso 2: Error por Regla de Negocio RN-45 -> 409 Conflict
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "mensaje": str(e),
                "data": None,
                "success": False
            }
        )
    except MonedaNoSoportadaException as e:
        # Caso 3: Error de Validación o Parámetros -> 400 Bad Request
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "mensaje": str(e),
                "data": None,
                "success": False
            }
        )
    except PasarelaNoDisponibleException as e:
        # Caso 4: Falla de Disponibilidad -> 503 Service Unavailable
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": str(e),
                "data": None,
                "success": False
            }
        )
    except Exception:
        # Fallos imprevistos ocultando trazas técnicas -> 503
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "La pasarela de pagos no se encuentra disponible",
                "data": None,
                "success": False
            }
        )
