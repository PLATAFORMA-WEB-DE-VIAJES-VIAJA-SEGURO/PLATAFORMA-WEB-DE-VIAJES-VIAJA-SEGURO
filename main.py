import fastapi
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.transaccion_router import router as transaction_router
from app.api.pago_router import router as payment_router
from app.api.factura_router import router as invoice_router
from app.api.notificacion_router import router as notification_router
from app.api.soporte_router import router as support_router
from app.api.usuario_router import router as user_router
from app.api.documento_viaje_router import router as travel_document_router
from app.api.vuelo_router import router as flight_router
from app.api.hotel_router import router as hotel_router
from app.api.reserva_router import router as reservation_router
from app.api.paquete_router import router as package_router

app = fastapi.FastAPI(
    title="API Viaja Seguro",
    description="Backend oficial con arquitectura de capas para la plataforma de viajes Viaja Seguro.",
    version="1.0.0",
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
            "success": False,
        },
    )


app.include_router(user_router)
app.include_router(travel_document_router)
app.include_router(flight_router)
app.include_router(hotel_router)
app.include_router(package_router)
app.include_router(reservation_router)
app.include_router(payment_router)
app.include_router(transaction_router)
app.include_router(invoice_router)
app.include_router(support_router)
app.include_router(notification_router)


@app.get("/", tags=["Root"])
def root():
    return {
        "servicio": "API Viaja Seguro",
        "version": "1.0.0",
        "docs": "http://127.0.0.1:8000/docs",
        "success": True,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
