from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from domain.notificacion import (
    NotificacionCreate,
    NotificacionResponse,
    ReglaNegocioRN55Exception,
    ProveedorNoDisponibleException,
    ValidacionParametrosException
)
from service.notificacion_service import NotificacionService
from repository.notificacion_repository import notificacion_repository

router = APIRouter(
    prefix="/api/v1/soporte",
    tags=["Soporte - Notificaciones"]
)

# Inyección de dependencias
servicio = NotificacionService(repo=notificacion_repository)

@router.post(
    "/notificaciones",
    response_model=NotificacionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enviar notificación al viajero (HU-055)",
    description="Endpoint centralizado para procesar y despachar notificaciones vía EMAIL o SMS mediante AEX-06."
)
def enviar_notificacion(datos: NotificacionCreate):
    try:
        resultado = servicio.enviar_notificacion(datos)
        return resultado
    except ReglaNegocioRN55Exception as e:
        # Criterio Caso 2: Error de Regla de Negocio RN-55 -> 409 Conflict
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "mensaje": str(e),
                "data": None,
                "success": False
            }
        )
    except ValidacionParametrosException as e:
        # Criterio Caso 3: Datos o Parámetros Inválidos -> 400 Bad Request
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "mensaje": str(e),
                "data": None,
                "success": False
            }
        )
    except ProveedorNoDisponibleException as e:
        # Criterio Caso 4: Falla de Disponibilidad del Proveedor AEX-06 -> 503 Service Unavailable
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": str(e),
                "data": None,
                "success": False
            }
        )
    except Exception:
        # Fallo inesperado ocultando stacktraces técnicos -> 500 Internal Server Error
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "mensaje": "Error interno del servidor al procesar la notificación",
                "data": None,
                "success": False
            }
        )
