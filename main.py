import fastapi
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from api.transaccion_router import router as transaccion_router
from api.pago_router import router as pago_router
from api.notificacion_router import router as notificacion_router
from api.soporte_router import router as soporte_router
from app.api.usuario_router import router as usuario_router

app = fastapi.FastAPI(
    title="API Viaja Seguro",
    description="Backend oficial con arquitectura de capas para la plataforma de viajes Viaja Seguro.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={
            "mensaje": "Parámetros de entrada inválidos o incompletos",
            "data": None,
            "success": False
        }
    )

app.include_router(usuario_router)
app.include_router(transaccion_router)
app.include_router(pago_router)
app.include_router(notificacion_router)
app.include_router(soporte_router)

@app.get("/", tags=["Root"])
def root():
    return {
        "servicio": "API Viaja Seguro",
        "version": "1.0.0",
        "docs": "http://127.0.0.1:8000/docs",
        "success": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)