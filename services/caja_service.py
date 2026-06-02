from datetime import datetime
from repository.caja_repo import CajaRepo


# Categorías predefinidas — la UI las muestra como opciones
CATEGORIAS_INGRESO = [
    "Servicio",
    "Venta de producto",
    "Otro ingreso",
]

CATEGORIAS_EGRESO = [
    "Compra a proveedor",
    "Gasto operativo",
    "Retiro de caja",
    "Otro egreso",
]


class CajaService:
    """
    Lógica de negocio para caja.
    Registra ingresos y egresos, calcula saldos y prepara datos para exportar.
    """

    def __init__(self):
        self._repo = CajaRepo()

    # ------------------------------------------------------------------ #
    #  Consultas                                                           #
    # ------------------------------------------------------------------ #

    def obtener_hoy(self) -> list:
        hoy = datetime.now().strftime("%Y-%m-%d")
        return self._repo.obtener_por_fecha(hoy)

    def obtener_por_fecha(self, fecha: str) -> list:
        return self._repo.obtener_por_fecha(fecha)

    def obtener_por_rango(self, fecha_desde: str, fecha_hasta: str) -> list:
        return self._repo.obtener_por_rango(fecha_desde, fecha_hasta)

    def saldo_hoy(self) -> float:
        hoy = datetime.now().strftime("%Y-%m-%d")
        return self._repo.saldo_hasta(hoy)

    def saldo_hasta(self, fecha: str) -> float:
        return self._repo.saldo_hasta(fecha)

    def resumen_por_rango(self, fecha_desde: str, fecha_hasta: str) -> dict:
        """
        Devuelve totales agrupados para mostrar en la UI o exportar.
        {
            'total_ingresos': float,
            'total_egresos': float,
            'saldo': float,
            'por_categoria': { 'Servicio': 5000.0, ... },
            'por_metodo_pago': { 'Efectivo': 3000.0, ... },
        }
        """
        movimientos = self._repo.obtener_por_rango(fecha_desde, fecha_hasta)

        total_ingresos = 0.0
        total_egresos  = 0.0
        por_categoria  = {}
        por_metodo     = {}

        for m in movimientos:
            monto = m["monto"]
            cat   = m["categoria"]
            mp    = m["metodo_pago_nombre"] or "Sin especificar"

            if m["tipo"] == "ingreso":
                total_ingresos += monto
            else:
                total_egresos += monto

            por_categoria[cat] = por_categoria.get(cat, 0.0) + monto
            por_metodo[mp]     = por_metodo.get(mp, 0.0) + monto

        return {
            "total_ingresos": total_ingresos,
            "total_egresos":  total_egresos,
            "saldo":          total_ingresos - total_egresos,
            "por_categoria":  por_categoria,
            "por_metodo_pago": por_metodo,
        }

    # ------------------------------------------------------------------ #
    #  Registrar movimientos                                               #
    # ------------------------------------------------------------------ #

    def registrar_ingreso(self, categoria: str, monto: float,
                          metodo_pago_id: int = None, descripcion: str = "",
                          fecha: str = None, turno_id: int = None,
                          producto_id: int = None) -> tuple[bool, str, int | None]:

        ok, msg = self._validar_movimiento("ingreso", categoria, monto)
        if not ok:
            return False, msg, None

        id_ = self._repo.registrar(
            tipo="ingreso",
            categoria=categoria,
            monto=monto,
            metodo_pago_id=metodo_pago_id,
            descripcion=descripcion,
            fecha=fecha,
            turno_id=turno_id,
            producto_id=producto_id,
        )
        return True, "Ingreso registrado.", id_

    def registrar_egreso(self, categoria: str, monto: float,
                         metodo_pago_id: int = None, descripcion: str = "",
                         fecha: str = None, proveedor_id: int = None,
                         producto_id: int = None) -> tuple[bool, str, int | None]:

        ok, msg = self._validar_movimiento("egreso", categoria, monto)
        if not ok:
            return False, msg, None

        id_ = self._repo.registrar(
            tipo="egreso",
            categoria=categoria,
            monto=monto,
            metodo_pago_id=metodo_pago_id,
            descripcion=descripcion,
            fecha=fecha,
            proveedor_id=proveedor_id,
            producto_id=producto_id,
        )
        return True, "Egreso registrado.", id_

    def registrar_cobro_turno(self, turno_id: int, monto: float,
                              metodo_pago_id: int, descripcion: str = "") -> tuple[bool, str, int | None]:
        """Atajo para registrar el cobro de un turno completado."""
        return self.registrar_ingreso(
            categoria="Servicio",
            monto=monto,
            metodo_pago_id=metodo_pago_id,
            descripcion=descripcion or "Cobro de turno",
            turno_id=turno_id,
        )

    def eliminar(self, id: int):
        self._repo.eliminar(id)

    # ------------------------------------------------------------------ #
    #  Validaciones internas                                               #
    # ------------------------------------------------------------------ #

    def _validar_movimiento(self, tipo: str, categoria: str, monto: float) -> tuple[bool, str]:
        if monto <= 0:
            return False, "El monto debe ser mayor a cero."

        categorias_validas = CATEGORIAS_INGRESO if tipo == "ingreso" else CATEGORIAS_EGRESO
        if categoria not in categorias_validas:
            # Permitimos categoría libre si no está en la lista predefinida
            # (la UI puede dejar que el usuario escriba una personalizada)
            pass

        return True, ""

    # ------------------------------------------------------------------ #
    #  Helpers para la UI                                                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def categorias_ingreso() -> list[str]:
        return CATEGORIAS_INGRESO.copy()

    @staticmethod
    def categorias_egreso() -> list[str]:
        return CATEGORIAS_EGRESO.copy()