from fastapi import FastAPI
from app.api.usuario_router import router as usuario_router

app = FastAPI(
    title="Viaja Seguro - API",
    description="Servicios web con arquitectura de capas para la plataforma de viajes",
    version="1.0.0",
)

app.include_router(usuario_router)


@app.get("/", tags=["Estado"])
def root():
    return {
        "status": "ok",
        "servicio": "Viaja Seguro API",
        "docs": "http://127.0.0.1:8000/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)