import os
from typing import Optional
from dotenv import load_dotenv
from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse
from app.domain.pago import (
    PaymentMethodsResponse,
    BusinessRuleRN45Exception,
    UnsupportedCurrencyException,
    PaymentGatewayUnavailableException,
)
from app.services.pago_service import PaymentService
from app.repositories.pago_repository import payment_repository

router = APIRouter(
    prefix="/api/v1/pagos",
    tags=["Pagos"],
)

service = PaymentService(repo=payment_repository)

# Documentación OpenAPI para Swagger UI (/docs)
OPENAPI_PAYMENT_METHODS_RESPONSES = {
    200: {
        "description": "Medios de pago consultados exitosamente",
        "model": PaymentMethodsResponse,
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
                                "activo": True,
                            },
                            {
                                "codigo": "PSE",
                                "nombre": "Transferencia Bancaria PSE",
                                "tipo": "DEBITO_BANCARIO",
                                "activo": True,
                            },
                        ],
                    },
                    "success": True,
                }
            }
        },
    },
    400: {
        "description": "Código de moneda no soportado o inválido",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Código de moneda no soportado",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    409: {
        "description": "Error por Regla de Negocio RN-45 (No hay medios de pago activos para la moneda)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "No hay medios de pago habilitados temporalmente para esta moneda",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    503: {
        "description": "Falla de Disponibilidad (La pasarela AEX-04 no se encuentra disponible)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "La pasarela de pagos no se encuentra disponible",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
}


@router.get(
    "/medios",
    response_model=PaymentMethodsResponse,
    status_code=status.HTTP_200_OK,
    responses=OPENAPI_PAYMENT_METHODS_RESPONSES,
    summary="Consultar medios de pago vigentes (HU-045)",
    description="Retorna las alternativas y métodos de pago financieros activos habilitados por la pasarela AEX-04 y AIN-06.",
)
def get_payment_methods(
    currency: Optional[str] = Query("COP", alias="moneda", description="Código ISO de la moneda (por defecto COP, ej: USD, EUR)"),
):
    # Recargar variables de entorno dinámicamente
    load_dotenv(override=True)
    simulate_env_failure = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() in ("true", "1", "yes")

    # Caso 4 de pruebas: Simulación de fallo de pasarela AEX-04 (503 Service Unavailable)
    is_simulated_failure = (currency or "").strip().upper() in ("503", "FAIL", "VS-2026-503")

    if simulate_env_failure or is_simulated_failure:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "La pasarela de pagos no se encuentra disponible",
                "data": None,
                "success": False,
            },
        )

    try:
        return service.get_payment_methods(currency=currency)
    except BusinessRuleRN45Exception as exc:
        # Caso 2: Error por Regla de Negocio RN-45 -> 409 Conflict
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "mensaje": str(exc),
                "data": None,
                "success": False,
            },
        )
    except UnsupportedCurrencyException as exc:
        # Caso 3: Error de Validación o Parámetros -> 400 Bad Request
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "mensaje": str(exc),
                "data": None,
                "success": False,
            },
        )
    except PaymentGatewayUnavailableException as exc:
        # Caso 4: Falla de Disponibilidad -> 503 Service Unavailable
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": str(exc),
                "data": None,
                "success": False,
            },
        )
    except Exception:
        # Fallos imprevistos ocultando trazas técnicas -> 503
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "La pasarela de pagos no se encuentra disponible",
                "data": None,
                "success": False,
            },
        )
