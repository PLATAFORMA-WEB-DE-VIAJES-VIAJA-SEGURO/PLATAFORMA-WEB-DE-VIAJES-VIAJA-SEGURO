import os
from dotenv import load_dotenv
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.domain.factura import (
    InvoiceCreate,
    InvoiceResponse,
    BusinessRuleRN48Exception,
    InvalidTaxDataException,
    BillingProviderUnavailableException,
)
from app.services.factura_service import InvoiceService
from app.repositories.factura_repository import invoice_repository
from app.repositories.transaccion_repository import transaction_repository

router = APIRouter(
    prefix="/api/v1/pagos",
    tags=["Pagos"],
)

service = InvoiceService(
    invoice_repo=invoice_repository,
    transaction_repo=transaction_repository,
)

# Documentación OpenAPI para Swagger UI (/docs)
OPENAPI_INVOICE_RESPONSES = {
    201: {
        "description": "Factura electrónica emitida exitosamente",
        "model": InvoiceResponse,
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
                        "estado_dian": "VALIDADA",
                    },
                    "success": True,
                }
            }
        },
    },
    400: {
        "description": "Datos fiscales del adquirente incompletos o inválidos",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "Datos fiscales del adquirente incompletos",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    409: {
        "description": "Error por Regla de Negocio RN-48 (transacción no aprobada o ya facturada)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "La transacción no está aprobada o ya cuenta con una factura emitida",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
    503: {
        "description": "Falla de Disponibilidad (Proveedor AEX-05 no disponible)",
        "content": {
            "application/json": {
                "example": {
                    "mensaje": "El proveedor de facturación electrónica no está disponible",
                    "data": None,
                    "success": False,
                }
            }
        },
    },
}


@router.post(
    "/facturas",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    responses=OPENAPI_INVOICE_RESPONSES,
    summary="Emitir factura electrónica (HU-048)",
    description="Genera la factura electrónica con CUFE ante el proveedor AEX-05 para una transacción aprobada. Aplica RN-48.",
)
def issue_invoice(payload: InvoiceCreate):
    # Recargar variables de entorno dinámicamente
    load_dotenv(override=True)
    simulate_env_failure = os.getenv("SIMULAR_FALLA_SERVIDOR", "False").strip().lower() in ("true", "1", "yes")

    # Caso 4: Simulación de fallo de AEX-05 (503 Service Unavailable)
    is_simulated_failure = payload.transaction_id == 503

    if simulate_env_failure or is_simulated_failure:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "El proveedor de facturación electrónica no está disponible",
                "data": None,
                "success": False,
            },
        )

    try:
        return service.issue_invoice(
            transaction_id=payload.transaction_id,
            tax_document_type=payload.tax_document_type,
            tax_document_number=payload.tax_document_number,
            company_name=payload.company_name,
            billing_email=payload.billing_email,
        )
    except BusinessRuleRN48Exception as exc:
        # Caso 2: Error por Regla de Negocio RN-48 -> 409 Conflict
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "mensaje": str(exc),
                "data": None,
                "success": False,
            },
        )
    except InvalidTaxDataException as exc:
        # Caso 3: Error de Validación -> 400 Bad Request
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "mensaje": str(exc),
                "data": None,
                "success": False,
            },
        )
    except BillingProviderUnavailableException as exc:
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
                "mensaje": "El proveedor de facturación electrónica no está disponible",
                "data": None,
                "success": False,
            },
        )
