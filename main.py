import fastapi
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from api.notificacion_router import router as notificacion_router
from api.soporte_router import router as soporte_router

app = fastapi.FastAPI(
    title="API Viaja Seguro - Módulo Atención al Cliente (MOD-07)",
    description="Backend oficial para Soporte, Opiniones y Notificaciones (HU-055 / RN-55 - Enviar notificación).",
    version="1.0.0"
)

# Configuración de CORS para integración con cualquier frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Manejador global para errores de validación de esquema Pydantic (Caso 3: 400 Bad Request)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={
            "mensaje": "El canal de envío, destinatario o plantilla no son válidos",
            "data": None,
            "success": False
        }
    )

# Registrar enrutadores de la API (HU-055 Notificaciones y HU-051 Casos)
app.include_router(notificacion_router)
app.include_router(soporte_router)

@app.get("/", tags=["Root"])
def root():
    return {
        "modulo": "Atención al Cliente (MOD-07)",
        "submodulo": "Soporte, Opiniones y Notificaciones",
        "historia_activa": "[HU-055] Enviar notificación",
        "version": "1.0.0",
        "docs": "http://127.0.0.1:8000/docs",
        "success": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
