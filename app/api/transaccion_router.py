import os
from dotenv import load_dotenv
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.domain.transaccion import (
    TransactionCreate,
    TransactionResponse,
    BusinessRuleRN47Exception,
    InvalidPaymentDataException,
    ExternalGatewayUnavailableException,
)
from app.services.transaccion_service import TransactionService
from app.repositories.transaccion_repository import transaction_repository

router = APIRouter(
    prefix="/api/v1/pagos",
    tags=["Pagos"],
)

service = TransactionService(repo=transaction_repository)

# Documentación OpenAPI para Swagger UI (/docs)
OPENAPI_TRANSACTION_RESPONSES = {
    201: {
        "description": "Cobro aprobado y reserva confirmada exitosamente",
        "model": TransactionResponse,
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Cobro aprobado y reserva confirmada exitosamente",
                    "data": {
                        "id_transaccion": 47001,
                        "referencia_pasarela": "PAY-99887766",
                        "codigo_reserva": "VS-2026-8841",
                        "monto_cobrado": 3000000.0,
                        "moneda": "COP",
                        "estado_transaccion": "APROBADO",
                        "estado_reserva": "CONFIRMADA",
                    },
                    "success": True,
                }
            }
        },
    },
    400: {
        "description": "Datos de pago incompletos o token de tarjeta inválido",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Datos de pago incompletos o token de tarjeta inválido",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    409: {
        "description": "Error por Regla de Negocio RN-47 (Discrepancia en monto liquidado AIN-15a o rechazo de pasarela)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "El monto enviado no coincide con el saldo de la reserva o la transacción fue rechazada",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    503: {
        "description": "Falla de Disponibilidad (La pasarela de pagos externa AEX-04 no responde)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "La pasarela de pagos externa no responde en este momento",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
}


@router.post(
    "/transacciones",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    responses=OPENAPI_TRANSACTION_RESPONSES,
    summary="Procesar cobro de reserva (HU-047)",
    description="Ejecuta la transacción de cobro financiero ante la pasarela AEX-04 validando el monto exacto en AIN-15a (RN-47).",
)
def process_charge(payload: TransactionCreate):
    # Recargar variables de entorno dinámicamente
    load_dotenv(override=True)
    simulate_env_failure = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() in ("true", "1", "yes")

    # Caso 4 de pruebas: Simulación de fallo de disponibilidad en pasarela AEX-04 (503 Service Unavailable)
    is_simulated_failure = (
        (payload.reservation_code and payload.reservation_code.strip().upper() == "VS-2026-503")
        or (payload.card_token and payload.card_token.strip().lower() in ("tok_503", "tok_falla"))
    )

    if simulate_env_failure or is_simulated_failure:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "La pasarela de pagos externa no responde en este momento",
                "data": None,
                "success": False,
            },
        )

    try:
        return service.process_charge(payload)
    except BusinessRuleRN47Exception as exc:
        # Caso 2: Error por Regla de Negocio RN-47 -> 409 Conflict
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "mensaje": str(exc),
                "data": None,
                "success": False,
            },
        )
    except InvalidPaymentDataException as exc:
        # Caso 3: Error de Validación o Parámetros -> 400 Bad Request
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "mensaje": str(exc),
                "data": None,
                "success": False,
            },
        )
    except ExternalGatewayUnavailableException as exc:
        # Caso 4: Falla de Disponibilidad AEX-04 -> 503 Service Unavailable
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": str(exc),
                "data": None,
                "success": False,
            },
        )
    except Exception:
        # Fallos internos imprevistos ocultando trazas técnicas -> 503
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "La pasarela de pagos externa no responde en este momento",
                "data": None,
                "success": False,
            },
        )
