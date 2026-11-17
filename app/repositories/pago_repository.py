from typing import Dict, List, Any

class PagoRepository:
    """
    Repositorio que simula la interacción con AIN-06 (Catálogos Financieros PAR-06)
    y la pasarela de pagos externa AEX-04.
    """

    def __init__(self):
        # Catálogo PAR-06 / AIN-06 cruzado con la pasarela AEX-04
        # Solo COP y USD tienen medios de pago habilitados y activos
        self._catalogo_medios: Dict[str, List[Dict[str, Any]]] = {
            "COP": [
                {
                    "codigo": "TC_VISA",
                    "nombre": "Tarjeta de Crédito Visa",
                    "tipo": "TARJETA_CREDITO",
                    "activo": True
                },
                {
                    "codigo": "PSE",
                    "nombre": "Transferencia Bancaria PSE",
                    "tipo": "DEBITO_BANCARIO",
                    "activo": True
                },
                {
                    "codigo": "TC_MASTERCARD",
                    "nombre": "Tarjeta de Crédito MasterCard",
                    "tipo": "TARJETA_CREDITO",
                    "activo": True
                }
            ],
            "USD": [
                {
                    "codigo": "TC_VISA",
                    "nombre": "Tarjeta de Crédito Visa",
                    "tipo": "TARJETA_CREDITO",
                    "activo": True
                },
                {
                    "codigo": "TC_MASTERCARD",
                    "nombre": "Tarjeta de Crédito MasterCard",
                    "tipo": "TARJETA_CREDITO",
                    "activo": True
                },
                {
                    "codigo": "PAYPAL",
                    "nombre": "Billetera Digital PayPal",
                    "tipo": "BILLETERA_DIGITAL",
                    "activo": True
                }
            ]
        }

    def consultar_medios_activos(self, moneda: str) -> List[Dict[str, Any]]:
        """
        Consulta y filtra únicamente los medios de pago activos y habilitados
        en el catálogo PAR-06 para la moneda dada.
        Si la moneda no tiene medios activos (ej: XXX, EUR), retorna lista vacía.
        """
        moneda_normalizada = moneda.strip().upper()
        medios = self._catalogo_medios.get(moneda_normalizada, [])
        return [m for m in medios if m.get("activo", False)]

# Instancia singleton del repositorio
pago_repository = PagoRepository()
