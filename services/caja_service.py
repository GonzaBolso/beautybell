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

    def obtener_por_id(self, id_: int):
        return self._repo.obtener_por_id(id_)

    def saldo_hoy(self) -> float:
        hoy = datetime.now().strftime("%Y-%m-%d")
        return self._repo.saldo_hasta(hoy)

    def saldo_hasta(self, fecha: str) -> float:
        return self._repo.saldo_hasta(fecha)

    def resumen_por_rango(self, fecha_desde: str, fecha_hasta: str) -> dict:
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
    #  Registrar / editar movimientos                                      #
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
                              metodo_pago_id: int, descripcion: str = "",
                              fecha: str = None) -> tuple[bool, str, int | None]:
        return self.registrar_ingreso(
            categoria="Servicio",
            monto=monto,
            metodo_pago_id=metodo_pago_id,
            descripcion=descripcion or "Cobro de turno",
            turno_id=turno_id,
            fecha=fecha,
        )

    def registrar_cobro_turno_multiple(self, turno_id: int, pagos: list,
                                       descripcion: str = "",
                                       fecha: str = None) -> tuple[bool, str, list]:
        """
        pagos: lista de dicts {metodo_pago_id, monto}
        Registra un movimiento de caja separado por cada metodo de pago,
        todos vinculados al mismo turno_id, en una unica transaccion
        (si alguno es invalido o falla, no se registra ninguno).
        """
        if not pagos:
            return False, "Debes ingresar al menos un metodo de pago.", []

        for p in pagos:
            ok, msg = self._validar_movimiento("ingreso", "Servicio", p["monto"])
            if not ok:
                return False, msg, []

        try:
            ids_creados = self._repo.registrar_multiple(
                tipo="ingreso",
                categoria="Servicio",
                pagos=pagos,
                descripcion=descripcion or "Cobro de turno",
                fecha=fecha,
                turno_id=turno_id,
            )
        except Exception as e:
            return False, f"Error al registrar el cobro: {e}", []

        return True, "Cobro registrado correctamente.", ids_creados

    def actualizar(self, id_: int, tipo: str, categoria: str, monto: float,
                   metodo_pago_id: int = None, descripcion: str = "",
                   fecha: str = None) -> tuple[bool, str]:
        ok, msg = self._validar_movimiento(tipo, categoria, monto)
        if not ok:
            return False, msg
        self._repo.actualizar(id_, tipo, categoria, monto, metodo_pago_id, descripcion, fecha)
        return True, "Movimiento actualizado."

    def eliminar(self, id: int):
        self._repo.eliminar(id)

    # ------------------------------------------------------------------ #
    #  Validaciones internas                                               #
    # ------------------------------------------------------------------ #

    def _validar_movimiento(self, tipo: str, categoria: str, monto: float) -> tuple[bool, str]:
        if monto <= 0:
            return False, "El monto debe ser mayor a cero."
        return True, ""

    @staticmethod
    def categorias_ingreso() -> list[str]:
        return CATEGORIAS_INGRESO.copy()

    @staticmethod
    def categorias_egreso() -> list[str]:
        return CATEGORIAS_EGRESO.copy()