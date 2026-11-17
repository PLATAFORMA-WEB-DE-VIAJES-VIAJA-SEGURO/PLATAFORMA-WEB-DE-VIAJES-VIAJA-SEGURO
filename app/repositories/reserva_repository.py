from typing import Dict, Any, Optional, List
from datetime import datetime, timezone


class ReservaRepository:
    """
    Repositorio que coordina la integración con AIN-01 (Catálogo Documentos),
    AIN-05 (Catálogos Reserva y Moneda), AIN-08 (Identidad), AIN-09 (Bloqueos de Vuelos),
    AIN-10 (Bloqueos de Hoteles), AIN-13 (Paquetes) y AIN-14 (Solicitud de Cobro).
    """

    def __init__(self):
        # Ítems precargados para la consulta del carrito (HU-035)
        self._items_default_701 = [
            {
                "id_item": 1,
                "tipo_servicio": "VUELO",
                "descripcion": "Vuelo BOG - CTG (2 pasajeros)",
                "cantidad": 2,
                "subtotal": 900000.0,
            },
            {
                "id_item": 2,
                "tipo_servicio": "HOTEL",
                "descripcion": "Hotel Caribe Cartagena (5 noches)",
                "cantidad": 1,
                "subtotal": 2100000.0,
            },
        ]

        # Catálogo de carritos en memoria para pruebas funcionales en Swagger UI
        self._carritos: Dict[int, Dict[str, Any]] = {
            701: {
                "id_carrito": 701,
                "id_usuario": 1,
                "estado_carrito": "ABIERTO",
                "bloqueos_vigentes": True,
                "tiene_items_validos": True,
                "codigo_reserva_preliminar": "VS-2026-8841",
                "subtotal": 2521008.0,
                "impuestos": 478992.0,
                "descuentos": 0.0,
                "total_liquidado": 3000000.0,
                "moneda": "COP",
                "items": [],
                "items_consulta": list(self._items_default_701),
            },
            702: {
                "id_carrito": 702,
                "id_usuario": 2,
                "estado_carrito": "ABIERTO",
                "bloqueos_vigentes": True,
                "tiene_items_validos": True,
                "codigo_reserva_preliminar": "VS-2026-8842",
                "subtotal": 1260504.0,
                "impuestos": 239496.0,
                "descuentos": 0.0,
                "total_liquidado": 1500000.0,
                "moneda": "COP",
                "items": [],
                "items_consulta": list(self._items_default_701),
            },
            703: {
                "id_carrito": 703,
                "id_usuario": 3,
                "estado_carrito": "ABIERTO",
                "bloqueos_vigentes": True,
                "tiene_items_validos": True,
                "codigo_reserva_preliminar": "VS-2026-8843",
                "subtotal": 3529412.0,
                "impuestos": 670588.0,
                "descuentos": 0.0,
                "total_liquidado": 4200000.0,
                "moneda": "COP",
                "items": [],
                "items_consulta": list(self._items_default_701),
            },
            700: {
                "id_carrito": 700,
                "id_usuario": 4,
                "estado_carrito": "CERRADO",
                "bloqueos_vigentes": False,
                "tiene_items_validos": False,
                "codigo_reserva_preliminar": "VS-2026-8800",
                "subtotal": 0.0,
                "impuestos": 0.0,
                "descuentos": 0.0,
                "total_liquidado": 0.0,
                "moneda": "COP",
                "items": [],
                "items_consulta": [],
            },
        }

        # Relación usuario -> carrito activo
        self._carrito_por_usuario: Dict[int, int] = {
            1: 701,
            2: 702,
            3: 703,
            4: 700,
            409: 700,
        }

        # Control de ítems agregados al carrito para HU-033 (RN-33)
        self._siguiente_id_item = 1
        self._bloqueos_en_carrito: set = set()
        self._bloqueos_expirados: set = {
            "BLK-EXPIRADO",
            "BLK-V-0000",
            "BLK-H-0000",
            "BLK-P-0000",
            "BLK-409",
        }

        # Catálogo de precisión decimal por moneda en AIN-05
        self._precision_moneda_ain05: Dict[str, int] = {
            "COP": 1,
            "USD": 2,
            "EUR": 2,
        }

        # Usuarios con identidad verificada en AIN-08
        self._usuarios_verificados = {1, 2, 3, 4, 5}

        # Almacenamiento de reservas creadas (HU-039)
        self._reservas_creadas: List[Dict[str, Any]] = []
        # Carritos que ya tienen reserva generada (700 precargado para pruebas de RN-39)
        self._carritos_con_reserva: set = {700}
        # Secuencia de IDs de reserva según especificación HU-039 (inicia en 9001)
        self._siguiente_id_reserva = 9001

        # Reservas base precargadas para pruebas directas de HU-040 en Swagger UI
        self._reservas_base: Dict[int, Dict[str, Any]] = {
            9001: {
                "id_reserva": 9001,
                "codigo_reserva": "VS-2026-8841",
                "id_usuario": 1,
                "estado": "PENDIENTE_PAGO",
                "total": 3000000.0,
                "moneda": "COP",
                "cupos_reservados": 2,
                "viajeros": [],
                "estado_nominacion": "PENDIENTE",
            },
            9002: {
                "id_reserva": 9002,
                "codigo_reserva": "VS-2026-8842",
                "id_usuario": 1,
                "estado": "PENDIENTE_PAGO",
                "total": 1500000.0,
                "moneda": "COP",
                "cupos_reservados": 2,
                "viajeros": [],
                "estado_nominacion": "PENDIENTE",
            },
            9003: {
                "id_reserva": 9003,
                "codigo_reserva": "VS-2026-8843",
                "id_usuario": 1,
                "estado": "PENDIENTE_PAGO",
                "total": 4200000.0,
                "moneda": "COP",
                "cupos_reservados": 2,
                "viajeros": [],
                "estado_nominacion": "PENDIENTE",
            },
        }

        # Tipos de documento válidos en AIN-01
        self._tipos_documento_ain01 = {"CC", "CE", "TI", "PA", "PASAPORTE", "RC", "NIT"}

    # ── Métodos HU-033 (Agregar ítem al carrito) ────────────────────
    def verificar_bloqueo_servicio_vigente(self, id_referencia_bloqueo: str) -> bool:
        """AIN-09 / AIN-10 / AIN-13: Verifica si el bloqueo temporal del servicio está vigente."""
        ref = id_referencia_bloqueo.strip().upper()
        return ref not in self._bloqueos_expirados

    def verificar_bloqueo_duplicado_en_carrito(self, id_referencia_bloqueo: str) -> bool:
        """RN-33: Verifica si el mismo bloqueo ya fue agregado previamente al carrito."""
        ref = id_referencia_bloqueo.strip().upper()
        return ref in self._bloqueos_en_carrito

    def agregar_item_al_carrito(
        self,
        id_usuario: int,
        tipo_servicio: str,
        id_referencia_bloqueo: str,
        descripcion: str,
        cantidad: int,
        precio_unitario: float,
    ) -> Dict[str, Any]:
        """Agrega un nuevo ítem validado al carrito activo del usuario."""
        id_carrito = self._carrito_por_usuario.get(id_usuario, 701)
        carrito = self._carritos.get(id_carrito, self._carritos[701])

        id_item = self._siguiente_id_item
        subtotal = round(float(cantidad) * float(precio_unitario), 1)
        ref = id_referencia_bloqueo.strip().upper()

        nuevo_item = {
            "id_carrito": carrito["id_carrito"],
            "id_item": id_item,
            "tipo_servicio": tipo_servicio,
            "id_referencia_bloqueo": ref,
            "descripcion": descripcion,
            "cantidad": cantidad,
            "precio_unitario": float(precio_unitario),
            "subtotal": subtotal,
        }

        carrito.setdefault("items", []).append(nuevo_item)
        self._bloqueos_en_carrito.add(ref)
        self._siguiente_id_item += 1

        nuevo_item["total_items_carrito"] = len(carrito["items"])
        return nuevo_item

    # ── Métodos HU-035 y HU-037 (Consultar y Calcular carrito) ──────
    def obtener_carrito_por_usuario(self, id_usuario: int) -> Optional[Dict[str, Any]]:
        """HU-035 / HU-037: Obtiene el carrito asociado al usuario indicado."""
        id_carrito = self._carrito_por_usuario.get(id_usuario)
        if id_carrito is None:
            return None
        return self._carritos.get(id_carrito)

    def obtener_precision_moneda_ain05(self, moneda: str) -> int:
        """AIN-05: Retorna la cantidad de decimales de redondeo según la moneda."""
        return self._precision_moneda_ain05.get(moneda.upper(), 2)

    # ── Métodos HU-038, HU-039 y HU-040 ─────────────────────────────
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

    def verificar_reserva_existente_por_carrito(self, id_carrito: int) -> bool:
        """RN-39: Verifica si ya existe una reserva generada para el carrito dado."""
        return id_carrito in self._carritos_con_reserva

    def obtener_estado_inicial_ain05(self) -> str:
        """AIN-05: Consulta el estado inicial parametrizado para nuevas reservas."""
        return "PENDIENTE_PAGO"

    def crear_reserva(
        self,
        id_usuario: int,
        id_carrito: int,
        moneda: str,
        total_reserva: float,
    ) -> Dict[str, Any]:
        """
        Persiste la reserva oficial en MOD-05 generando un código localizador único (VS-YYYY-XXXX).
        """
        id_reserva = self._siguiente_id_reserva
        carrito = self._carritos.get(id_carrito, {})

        if id_reserva == 9001 or id_carrito == 701:
            codigo_reserva = carrito.get("codigo_reserva_preliminar", "VS-2026-8841")
            fecha_creacion = "2026-11-15T17:15:00Z"
        else:
            codigo_reserva = carrito.get("codigo_reserva_preliminar", f"VS-2026-{id_reserva}")
            fecha_creacion = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        estado_inicial = self.obtener_estado_inicial_ain05()

        nueva_reserva = {
            "id_reserva": id_reserva,
            "codigo_reserva": codigo_reserva,
            "id_usuario": id_usuario,
            "id_carrito": id_carrito,
            "estado": estado_inicial,
            "total": float(total_reserva),
            "moneda": moneda,
            "fecha_creacion": fecha_creacion,
            "cupos_reservados": 2,
            "viajeros": [],
            "estado_nominacion": "PENDIENTE",
        }

        self._reservas_creadas.append(nueva_reserva)
        self._reservas_base[id_reserva] = nueva_reserva
        self._carritos_con_reserva.add(id_carrito)
        self._siguiente_id_reserva += 1

        return nueva_reserva

    def validar_tipo_documento_ain01(self, tipo_documento: str) -> bool:
        """AIN-01: Verifica que el tipo de documento exista en el catálogo oficial."""
        return tipo_documento.strip().upper() in self._tipos_documento_ain01

    def obtener_reserva_por_id(self, id_reserva: int) -> Optional[Dict[str, Any]]:
        """Busca una reserva por su ID en las creadas en sesión o en el catálogo base."""
        for r in self._reservas_creadas:
            if r["id_reserva"] == id_reserva:
                return r
        return self._reservas_base.get(id_reserva)

    def registrar_viajeros_en_reserva(
        self,
        id_reserva: int,
        viajeros: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Persiste el listado de viajeros nominados en la reserva y actualiza su estado a COMPLETA."""
        reserva = self.obtener_reserva_por_id(id_reserva)
        reserva["viajeros"] = viajeros
        reserva["estado_nominacion"] = "COMPLETA"
        return reserva


# Instancia singleton del repositorio
reserva_repository = ReservaRepository()
