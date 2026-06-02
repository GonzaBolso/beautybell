from repository.base_repo import BaseRepo


class CompraRepo(BaseRepo):

    def obtener_todas(self):
        return self._todos(
            """
            SELECT cp.*, p.nombre AS proveedor_nombre, mp.nombre AS metodo_pago_nombre
            FROM compras_proveedor cp
            JOIN proveedores  p  ON p.id  = cp.proveedor_id
            LEFT JOIN metodos_pago mp ON mp.id = cp.metodo_pago_id
            ORDER BY cp.fecha DESC
            """
        )

    def obtener_por_id(self, id: int):
        return self._uno(
            """
            SELECT cp.*, p.nombre AS proveedor_nombre, mp.nombre AS metodo_pago_nombre
            FROM compras_proveedor cp
            JOIN proveedores  p  ON p.id  = cp.proveedor_id
            LEFT JOIN metodos_pago mp ON mp.id = cp.metodo_pago_id
            WHERE cp.id = ?
            """,
            (id,)
        )

    def obtener_detalle(self, compra_id: int):
        return self._todos(
            """
            SELECT cd.*, pr.nombre AS producto_nombre
            FROM compras_detalle cd
            JOIN productos pr ON pr.id = cd.producto_id
            WHERE cd.compra_id = ?
            """,
            (compra_id,)
        )

    def crear_cabecera(self, proveedor_id: int, metodo_pago_id: int,
                       total: float, fecha: str = None, notas: str = "") -> int:
        cur = self._ejecutar(
            """INSERT INTO compras_proveedor (proveedor_id, metodo_pago_id, total, fecha, notas)
               VALUES (?, ?, ?, COALESCE(?, date('now')), ?)""",
            (proveedor_id, metodo_pago_id, total, fecha, notas)
        )
        return self._ultimo_id(cur)

    def agregar_detalle(self, compra_id: int, producto_id: int,
                        cantidad: int, precio_unitario: float) -> int:
        cur = self._ejecutar(
            """INSERT INTO compras_detalle (compra_id, producto_id, cantidad, precio_unitario)
               VALUES (?, ?, ?, ?)""",
            (compra_id, producto_id, cantidad, precio_unitario)
        )
        return self._ultimo_id(cur)

    def eliminar(self, id: int):
        self._ejecutar("DELETE FROM compras_detalle WHERE compra_id = ?", (id,))
        self._ejecutar("DELETE FROM compras_proveedor WHERE id = ?", (id,))