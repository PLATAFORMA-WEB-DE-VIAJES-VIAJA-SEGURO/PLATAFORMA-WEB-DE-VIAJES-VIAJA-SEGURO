"""
Casos de prueba funcional para HU-048 — Emitir factura electrónica
Endpoint: POST /api/v1/pagos/facturas
Regla de Negocio: RN-48
"""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# ─────────────────────────────────────────────────────────────
# Preparación: Crear una transacción aprobada (vía HU-047)
# para que exista id_transaccion disponible en el repositorio
# ─────────────────────────────────────────────────────────────
def crear_transaccion_aprobada():
    """Crea una transacción aprobada en el repositorio para pruebas de facturación."""
    payload = {
        "codigo_reserva": "VS-2026-8841",
        "monto": 3000000.0,
        "moneda": "COP",
        "codigo_medio_pago": "TC_VISA",
        "token_tarjeta": "tok_abc123456"
    }
    response = client.post("/api/v1/pagos/transacciones", json=payload)
    data = response.json()
    return data.get("data", {}).get("id_transaccion")


# ─────────────────────────────────────────────────────────────
# CASO 1: Flujo Exitoso (201 Created)
# ─────────────────────────────────────────────────────────────
def test_caso1_flujo_exitoso():
    print("=" * 60)
    print("CASO 1: Flujo Exitoso (201 Created)")
    print("=" * 60)

    id_transaccion = crear_transaccion_aprobada()
    assert id_transaccion is not None, "ERROR: No se pudo crear la transacción de prueba"

    payload = {
        "id_transaccion": id_transaccion,
        "tipo_documento_fiscal": "CC",
        "numero_documento_fiscal": "1095888777",
        "razon_social": "Juan Perez",
        "correo_facturacion": "juan.perez@email.com"
    }

    response = client.post("/api/v1/pagos/facturas", json=payload)
    body = response.json()

    print(f"  Status Code: {response.status_code}")
    print(f"  Response: {body}")

    assert response.status_code == 201, f"ERROR: Se esperaba 201, se obtuvo {response.status_code}"
    assert body["success"] is True
    assert body["data"] is not None
    assert body["data"]["id_transaccion"] == id_transaccion
    assert body["data"]["estado_dian"] == "VALIDADA"
    assert body["data"]["numero_factura"].startswith("FE-VS-")
    assert len(body["data"]["cufe"]) > 0
    assert body["mensaje"] == "Factura electrónica emitida exitosamente"
    print("  ✅ CASO 1 APROBADO\n")


# ─────────────────────────────────────────────────────────────
# CASO 2: Error de Regla de Negocio RN-48 (409 Conflict)
# ─────────────────────────────────────────────────────────────
def test_caso2_regla_negocio_rn48():
    print("=" * 60)
    print("CASO 2: Error por Regla de Negocio RN-48 (409 Conflict)")
    print("=" * 60)

    # Usar un id_transaccion que NO existe en el repositorio (nunca fue creada)
    payload = {
        "id_transaccion": 99999,
        "tipo_documento_fiscal": "CC",
        "numero_documento_fiscal": "1095888777",
        "razon_social": "Juan Perez",
        "correo_facturacion": "juan.perez@email.com"
    }

    response = client.post("/api/v1/pagos/facturas", json=payload)
    body = response.json()

    print(f"  Status Code: {response.status_code}")
    print(f"  Response: {body}")

    assert response.status_code == 409, f"ERROR: Se esperaba 409, se obtuvo {response.status_code}"
    assert body["success"] is False
    assert body["data"] is None
    assert "no está aprobada" in body["mensaje"] or "factura emitida" in body["mensaje"]
    print("  ✅ CASO 2 APROBADO\n")


# ─────────────────────────────────────────────────────────────
# CASO 3: Datos Faltantes o Parámetros Inválidos (400)
# ─────────────────────────────────────────────────────────────
def test_caso3_datos_invalidos():
    print("=" * 60)
    print("CASO 3: Datos Faltantes o Parámetros Inválidos (400 Bad Request)")
    print("=" * 60)

    # Payload con campos faltantes (sin razon_social ni correo_facturacion)
    payload = {
        "id_transaccion": 47001
    }

    response = client.post("/api/v1/pagos/facturas", json=payload)
    body = response.json()

    print(f"  Status Code: {response.status_code}")
    print(f"  Response: {body}")

    assert response.status_code == 400, f"ERROR: Se esperaba 400, se obtuvo {response.status_code}"
    assert body["success"] is False
    assert body["data"] is None
    print("  ✅ CASO 3 APROBADO\n")


# ─────────────────────────────────────────────────────────────
# CASO 4: Falla de Disponibilidad (503 Service Unavailable)
# ─────────────────────────────────────────────────────────────
def test_caso4_falla_disponibilidad():
    print("=" * 60)
    print("CASO 4: Falla de Disponibilidad (503 Service Unavailable)")
    print("=" * 60)

    # Enviar id_transaccion=503 como disparador de simulación de fallo
    payload = {
        "id_transaccion": 503,
        "tipo_documento_fiscal": "CC",
        "numero_documento_fiscal": "1095888777",
        "razon_social": "Juan Perez",
        "correo_facturacion": "juan.perez@email.com"
    }

    response = client.post("/api/v1/pagos/facturas", json=payload)
    body = response.json()

    print(f"  Status Code: {response.status_code}")
    print(f"  Response: {body}")

    assert response.status_code == 503, f"ERROR: Se esperaba 503, se obtuvo {response.status_code}"
    assert body["success"] is False
    assert body["data"] is None
    assert body["mensaje"] == "El proveedor de facturación electrónica no está disponible"
    print("  ✅ CASO 4 APROBADO\n")


# ─────────────────────────────────────────────────────────────
# Ejecutar todos los casos
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🧪 PRUEBAS FUNCIONALES — HU-048 Emitir Factura Electrónica\n")
    test_caso1_flujo_exitoso()
    test_caso2_regla_negocio_rn48()
    test_caso3_datos_invalidos()
    test_caso4_falla_disponibilidad()
    print("=" * 60)
    print("🎯 TODOS LOS CASOS DE PRUEBA APROBADOS")
    print("=" * 60)
