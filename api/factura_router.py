import os
from dotenv import load_dotenv
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from domain.factura import (
    FacturaCreate,
    FacturaResponse,
    ReglaNegocioRN48Exception,
    DatosFiscalesInvalidosException,
    FacturacionNoDisponibleException
)
from service.factura_service import FacturaService
from repository.factura_repository import factura_repository
from repository.transaccion_repository import transaccion_repository

router = APIRouter(
    prefix="/api/v1/pagos",
    tags=["Pagos"]
)

servicio = FacturaService(
    repo_factura=factura_repository,
    repo_transaccion=transaccion_repository
)

# Documentación OpenAPI para Swagger UI (/docs)
RESPUESTAS_OPENAPI_FACTURA = {
    201: {
        "description": "Factura electrónica emitida exitosamente",
        "model": FacturaResponse,
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Factura electrónica emitida exitosamente",
                    "data": {
                        "id_factura": 48001,
                        "numero_factura": "FE-VS-00125",
                        "id_transaccion": 47001,
                        "cufe": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
                        "total_facturado": 3000000.0,
                        "estado_dian": "VALIDADA"
                    },
                    "success": True
                }
            }
        }
    },
    400: {
        "description": "Datos fiscales del adquirente incompletos o inválidos",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Datos fiscales del adquirente incompletos",
                    "data": None,
                    "success": False
                }
            }
        }
    },
    409: {
        "description": "Error por Regla de Negocio RN-48 (transacción no aprobada o ya facturada)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "La transacción no está aprobada o ya cuenta con una factura emitida",
                    "data": None,
                    "success": False
                }
            }
        }
    },
    503: {
        "description": "Falla de Disponibilidad (Proveedor AEX-05 no disponible)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "El proveedor de facturación electrónica no está disponible",
                    "data": None,
                    "success": False
                }
            }
        }
    }
}


@router.post(
    "/facturas",
    response_model=FacturaResponse,
    status_code=status.HTTP_201_CREATED,
    responses=RESPUESTAS_OPENAPI_FACTURA,
    summary="Emitir factura electrónica (HU-048)",
    description="Genera la factura electrónica con CUFE ante el proveedor AEX-05 para una transacción aprobada. Aplica RN-48."
)
def emitir_factura(payload: FacturaCreate):
    # Recargar variables de entorno dinámicamente
    load_dotenv(override=True)
    simular_falla_env = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() in ("true", "1", "yes")

    # Caso 4: Simulación de fallo de AEX-05 (503 Service Unavailable)
    # Activado si SIMULAR_FALLA_SERVIDOR="True" en .env o si id_transaccion == 503
    es_simulacion_falla = payload.id_transaccion == 503

    if simular_falla_env or es_simulacion_falla:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "El proveedor de facturación electrónica no está disponible",
                "data": None,
                "success": False
            }
        )

    try:
        resultado = servicio.emitir_factura(
            id_transaccion=payload.id_transaccion,
            tipo_documento_fiscal=payload.tipo_documento_fiscal,
            numero_documento_fiscal=payload.numero_documento_fiscal,
            razon_social=payload.razon_social,
            correo_facturacion=payload.correo_facturacion
        )
        return resultado
    except ReglaNegocioRN48Exception as e:
        # Caso 2: Error por Regla de Negocio RN-48 -> 409 Conflict
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "mensaje": str(e),
                "data": None,
                "success": False
            }
        )
    except DatosFiscalesInvalidosException as e:
        # Caso 3: Error de Validación -> 400 Bad Request
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "mensaje": str(e),
                "data": None,
                "success": False
            }
        )
    except FacturacionNoDisponibleException as e:
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
                "mensaje": "El proveedor de facturación electrónica no está disponible",
                "data": None,
                "success": False
            }
        )
