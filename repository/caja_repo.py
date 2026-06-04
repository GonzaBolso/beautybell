from repository.base_repo import BaseRepo


class CajaRepo(BaseRepo):

    def obtener_por_fecha(self, fecha: str):
        """fecha en formato YYYY-MM-DD"""
        return self._todos(
            """
            SELECT cm.*, mp.nombre AS metodo_pago_nombre,
                   p.nombre AS proveedor_nombre,
                   pr.nombre AS producto_nombre
            FROM caja_movimientos cm
            LEFT JOIN metodos_pago mp ON mp.id = cm.metodo_pago_id
            LEFT JOIN proveedores   p  ON p.id  = cm.proveedor_id
            LEFT JOIN productos     pr ON pr.id = cm.producto_id
            WHERE cm.fecha = ?
            ORDER BY cm.id
            """,
            (fecha,)
        )

    def obtener_por_rango(self, fecha_desde: str, fecha_hasta: str):
        return self._todos(
            """
            SELECT cm.*, mp.nombre AS metodo_pago_nombre,
                   p.nombre AS proveedor_nombre,
                   pr.nombre AS producto_nombre
            FROM caja_movimientos cm
            LEFT JOIN metodos_pago mp ON mp.id = cm.metodo_pago_id
            LEFT JOIN proveedores   p  ON p.id  = cm.proveedor_id
            LEFT JOIN productos     pr ON pr.id = cm.producto_id
            WHERE cm.fecha BETWEEN ? AND ?
            ORDER BY cm.fecha, cm.id
            """,
            (fecha_desde, fecha_hasta)
        )

    def obtener_por_id(self, id_: int):
        return self._uno(
            """
            SELECT cm.*, mp.nombre AS metodo_pago_nombre
            FROM caja_movimientos cm
            LEFT JOIN metodos_pago mp ON mp.id = cm.metodo_pago_id
            WHERE cm.id = ?
            """,
            (id_,)
        )

    def saldo_hasta(self, fecha: str) -> float:
        row = self._uno(
            """
            SELECT COALESCE(SUM(CASE WHEN tipo='ingreso' THEN monto ELSE -monto END), 0) AS saldo
            FROM caja_movimientos
            WHERE fecha <= ?
            """,
            (fecha,)
        )
        return row["saldo"] if row else 0.0

    def registrar(self, tipo: str, categoria: str, monto: float,
                  metodo_pago_id: int = None, descripcion: str = "",
                  fecha: str = None, turno_id: int = None,
                  proveedor_id: int = None, producto_id: int = None) -> int:
        from datetime import date as _date
        fecha_final = fecha or _date.today().strftime("%Y-%m-%d")
        cur = self._ejecutar(
            """INSERT INTO caja_movimientos
               (tipo, categoria, monto, metodo_pago_id, descripcion, fecha, turno_id, proveedor_id, producto_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (tipo, categoria, monto, metodo_pago_id, descripcion,
             fecha_final, turno_id, proveedor_id, producto_id)
        )
        return self._ultimo_id(cur)

    def actualizar(self, id_: int, tipo: str, categoria: str, monto: float,
                   metodo_pago_id: int = None, descripcion: str = "",
                   fecha: str = None):
        self._ejecutar(
            """UPDATE caja_movimientos
               SET tipo=?, categoria=?, monto=?, metodo_pago_id=?, descripcion=?, fecha=?
               WHERE id=?""",
            (tipo, categoria, monto, metodo_pago_id, descripcion, fecha, id_)
        )

    def eliminar(self, id: int):
        self._ejecutar("DELETE FROM caja_movimientos WHERE id = ?", (id,))