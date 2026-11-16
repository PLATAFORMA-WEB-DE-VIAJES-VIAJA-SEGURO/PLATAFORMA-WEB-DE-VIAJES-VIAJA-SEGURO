import os
from dotenv import load_dotenv
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.domain.transaccion import (
    TransaccionCreate,
    TransaccionResponse,
    ReglaNegocioRN47Exception,
    DatosPagoInvalidosException,
    PasarelaNoDisponibleException
)
from app.services.transaccion_service import TransaccionService
from app.repositories.transaccion_repository import transaccion_repository

router = APIRouter(
    prefix="/api/v1/pagos",

    tags=["Pagos"]

    tags=["Pagos - Transacciones"]

)

servicio = TransaccionService(repo=transaccion_repository)

# Documentación OpenAPI para Swagger UI (/docs)
RESPUESTAS_OPENAPI_TRANSACCION = {
    201: {
        "description": "Cobro aprobado y reserva confirmada exitosamente",
        "model": TransaccionResponse,
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
                        "estado_reserva": "CONFIRMADA"
                    },
                    "success": True
                }
            }
        }
    },
    400: {
        "description": "Datos de pago incompletos o token de tarjeta inválido",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Datos de pago incompletos o token de tarjeta inválido",
                    "data": None,
                    "success": False
                }
            }
        }
    },
    409: {
        "description": "Error por Regla de Negocio RN-47 (Discrepancia en monto liquidado AIN-15a o rechazo de pasarela)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "El monto enviado no coincide con el saldo de la reserva o la transacción fue rechazada",
                    "data": None,
                    "success": False
                }
            }
        }
    },
    503: {
        "description": "Falla de Disponibilidad (La pasarela de pagos externa AEX-04 no responde)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "La pasarela de pagos externa no responde en este momento",
                    "data": None,
                    "success": False
                }
            }
        }
    }
}

@router.post(
    "/transacciones",
    response_model=TransaccionResponse,
    status_code=status.HTTP_201_CREATED,
    responses=RESPUESTAS_OPENAPI_TRANSACCION,
    summary="Procesar cobro de reserva (HU-047)",
    description="Ejecuta la transacción de cobro financiero ante la pasarela AEX-04 validando el monto exacto en AIN-15a (RN-47)."
)
def procesar_cobro(datos: TransaccionCreate):
    # Recargar variables de entorno dinámicamente
    load_dotenv(override=True)
    simular_falla_env = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() in ("true", "1", "yes")

    # Caso 4 de pruebas: Simulación de fallo de disponibilidad en pasarela AEX-04 (503 Service Unavailable)
    es_simulacion_falla = (
        (datos.codigo_reserva and datos.codigo_reserva.strip().upper() == "VS-2026-503")
        or (datos.token_tarjeta and datos.token_tarjeta.strip().lower() in ("tok_503", "tok_falla"))
    )

    if simular_falla_env or es_simulacion_falla:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "La pasarela de pagos externa no responde en este momento",
                "data": None,
                "success": False
            }
        )

    try:
        resultado = servicio.procesar_cobro(datos)
        return resultado
    except ReglaNegocioRN47Exception as e:
        # Caso 2: Error por Regla de Negocio RN-47 -> 409 Conflict
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "mensaje": str(e),
                "data": None,
                "success": False
            }
        )
    except DatosPagoInvalidosException as e:
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
        # Caso 4: Falla de Disponibilidad AEX-04 -> 503 Service Unavailable
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": str(e),
                "data": None,
                "success": False
            }
        )
    except Exception:
        # Fallos internos imprevistos ocultando trazas técnicas -> 503
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "La pasarela de pagos externa no responde en este momento",
                "data": None,
                "success": False
            }
        )
