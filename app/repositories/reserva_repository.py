from typing import Dict, Any, Optional


class ReservaRepository:
    """
    Repositorio que coordina la integración con AIN-08 (Identidad),
    AIN-09 (Bloqueos de Vuelos), AIN-10 (Bloqueos de Hoteles) y AIN-14 (Solicitud de Cobro).
    """

    def __init__(self):
        # Catálogo de carritos en memoria para pruebas funcionales en Swagger UI
        self._carritos: Dict[int, Dict[str, Any]] = {
            701: {
                "id_carrito": 701,
                "id_usuario": 1,
                "estado_carrito": "ABIERTO",
                "bloqueos_vigentes": True,
                "codigo_reserva_preliminar": "VS-2026-8841",
                "total_liquidado": 3000000.0,
                "moneda": "COP",
            },
            702: {
                "id_carrito": 702,
                "id_usuario": 1,
                "estado_carrito": "ABIERTO",
                "bloqueos_vigentes": True,
                "codigo_reserva_preliminar": "VS-2026-8842",
                "total_liquidado": 1500000.0,
                "moneda": "COP",
            },
            703: {
                "id_carrito": 703,
                "id_usuario": 1,
                "estado_carrito": "ABIERTO",
                "bloqueos_vigentes": True,
                "codigo_reserva_preliminar": "VS-2026-8843",
                "total_liquidado": 4200000.0,
                "moneda": "COP",
            },
            700: {
                "id_carrito": 700,
                "id_usuario": 1,
                "estado_carrito": "CERRADO",
                "bloqueos_vigentes": False,
                "codigo_reserva_preliminar": "VS-2026-8800",
                "total_liquidado": 3000000.0,
                "moneda": "COP",
            },
        }

        # Usuarios con identidad verificada en AIN-08
        self._usuarios_verificados = {1, 2, 3, 4, 5}

    def verificar_identidad_ain08(self, id_usuario: int) -> bool:
        """AIN-08: Revalida que la identidad del usuario esté activa y verificada."""
        return id_usuario in self._usuarios_verificados

    def obtener_carrito(self, id_carrito: int) -> Optional[Dict[str, Any]]:
        """Obtiene la información actual del carrito de compras."""
        return self._carritos.get(id_carrito)

    def verificar_bloqueos_ain09_ain10(self, carrito: Dict[str, Any]) -> bool:
        """AIN-09 y AIN-10: Verifica que los bloqueos temporales de vuelos y hoteles sigan vigentes."""
        return bool(carrito.get("bloqueos_vigentes", False))

    def cerrar_carrito_y_solicitar_cobro_ain14(
        self,
        id_carrito: int,
        medio_pago: str,
        direccion_facturacion: str,
    ) -> Dict[str, Any]:
        """
        Transiciona el carrito de ABIERTO a CERRADO, congela la liquidación
        y dispara la orden de reserva pendiente de pago hacia AIN-14.
        """
        carrito = self._carritos[id_carrito]
        carrito["estado_carrito"] = "CERRADO"
        carrito["medio_pago"] = medio_pago
        carrito["direccion_facturacion"] = direccion_facturacion
        return carrito


# Instancia singleton del repositorio
reserva_repository = ReservaRepository()
