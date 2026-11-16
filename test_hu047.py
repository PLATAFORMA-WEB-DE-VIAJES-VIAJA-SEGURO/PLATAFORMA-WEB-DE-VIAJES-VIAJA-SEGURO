from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_caso_1_flujo_exitoso():
    print("\n--- CASO 1: Flujo Exitoso (201 Created) ---")
    payload = {
        "codigo_reserva": "VS-2026-8841",
        "monto": 3000000.0,
        "moneda": "COP",
        "codigo_medio_pago": "TC_VISA",
        "token_tarjeta": "tok_visa_987654321"
    }
    response = client.post("/api/v1/pagos/transacciones", json=payload)
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["mensaje"] == "Cobro aprobado y reserva confirmada exitosamente"
    assert body["data"]["id_transaccion"] == 47001
    assert body["data"]["referencia_pasarela"] == "PAY-99887766"
    assert body["data"]["codigo_reserva"] == "VS-2026-8841"
    assert body["data"]["monto_cobrado"] == 3000000.0
    assert body["data"]["moneda"] == "COP"
    assert body["data"]["estado_transaccion"] == "APROBADO"
    assert body["data"]["estado_reserva"] == "CONFIRMADA"
    print("✓ CASO 1 PASÓ EXITOSAMENTE")

def test_caso_2_regla_rn47():
    print("\n--- CASO 2: Error por Regla de Negocio RN-47 (409 Conflict) ---")
    
    # 2.1: Discrepancia entre monto enviado y saldo liquidado en AIN-15a
    payload_monto_erroneo = {
        "codigo_reserva": "VS-2026-8841",
        "monto": 2500000.0,  # Esperado: 3000000.0
        "moneda": "COP",
        "codigo_medio_pago": "TC_VISA",
        "token_tarjeta": "tok_visa_987654321"
    }
    res1 = client.post("/api/v1/pagos/transacciones", json=payload_monto_erroneo)
    print("Discrepancia de monto -> Status:", res1.status_code, "Body:", res1.json())
    assert res1.status_code == 409
    assert res1.json()["success"] is False
    assert res1.json()["data"] is None
    assert res1.json()["mensaje"] == "El monto enviado no coincide con el saldo de la reserva o la transacción fue rechazada"

    # 2.2: Rechazo bancario simulado por token
    payload_rechazo = {
        "codigo_reserva": "VS-2026-8841",
        "monto": 3000000.0,
        "moneda": "COP",
        "codigo_medio_pago": "TC_VISA",
        "token_tarjeta": "tok_rechazado"
    }
    res2 = client.post("/api/v1/pagos/transacciones", json=payload_rechazo)
    print("Rechazo de pasarela -> Status:", res2.status_code, "Body:", res2.json())
    assert res2.status_code == 409
    assert res2.json()["success"] is False
    assert res2.json()["mensaje"] == "El monto enviado no coincide con el saldo de la reserva o la transacción fue rechazada"
    print("✓ CASO 2 PASÓ EXITOSAMENTE")

def test_caso_3_parametros_invalidos():
    print("\n--- CASO 3: Parámetros Inválidos o Datos Faltantes (400 Bad Request) ---")
    # Petición incompleta sin monto ni token
    payload_incompleto = {
        "codigo_reserva": "VS-2026-8841",
        "moneda": "COP"
    }
    response = client.post("/api/v1/pagos/transacciones", json=payload_incompleto)
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["mensaje"] == "Datos de pago incompletos o token de tarjeta inválido"
    print("✓ CASO 3 PASÓ EXITOSAMENTE")

def test_caso_4_falla_disponibilidad():
    print("\n--- CASO 4: Falla de Disponibilidad Pasarela AEX-04 (503 Service Unavailable) ---")
    payload = {
        "codigo_reserva": "VS-2026-503",
        "monto": 3000000.0,
        "moneda": "COP",
        "codigo_medio_pago": "TC_VISA",
        "token_tarjeta": "tok_503"
    }
    response = client.post("/api/v1/pagos/transacciones", json=payload)
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

    assert response.status_code == 503
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["mensaje"] == "La pasarela de pagos externa no responde en este momento"
    print("✓ CASO 4 PASÓ EXITOSAMENTE")

if __name__ == "__main__":
    test_caso_1_flujo_exitoso()
    test_caso_2_regla_rn47()
    test_caso_3_parametros_invalidos()
    test_caso_4_falla_disponibilidad()
    print("\n🎉 ¡TODOS LOS CRITERIOS DE ACEPTACIÓN DE [HU-047] FUERON SATISFECHOS!")
