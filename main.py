from fastapi import FastAPI

app = FastAPI(title="Viaja Seguro")


@app.get("/")
def raiz():
    return {"mensaje": "Servidor funcionando"}  
#prueba de commit