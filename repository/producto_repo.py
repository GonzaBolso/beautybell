from repository.base_repo import BaseRepo


class ProductoRepo(BaseRepo):

    def obtener_todos(self):
        return self._todos(
            """
            SELECT p.*, pr.nombre AS proveedor_nombre
            FROM productos p
            LEFT JOIN proveedores pr ON pr.id = p.proveedor_id
            ORDER BY p.nombre
            """
        )

    def obtener_por_proveedor(self, proveedor_id: int):
        return self._todos(
            "SELECT * FROM productos WHERE proveedor_id = ? ORDER BY nombre",
            (proveedor_id,)
        )

    def obtener_por_id(self, id: int):
        return self._uno(
            "SELECT * FROM productos WHERE id = ?", (id,)
        )

    def crear(self, nombre: str, proveedor_id: int = None, categoria: str = "",
              precio_costo: float = 0, precio_venta: float = 0, stock: int = 0) -> int:
        cur = self._ejecutar(
            """INSERT INTO productos (nombre, proveedor_id, categoria, precio_costo, precio_venta, stock)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (nombre, proveedor_id, categoria, precio_costo, precio_venta, stock)
        )
        return self._ultimo_id(cur)

    def actualizar(self, id: int, nombre: str, proveedor_id: int, categoria: str,
                   precio_costo: float, precio_venta: float, stock: int):
        self._ejecutar(
            """UPDATE productos SET nombre=?, proveedor_id=?, categoria=?,
               precio_costo=?, precio_venta=?, stock=? WHERE id=?""",
            (nombre, proveedor_id, categoria, precio_costo, precio_venta, stock, id)
        )

    def ajustar_stock(self, id: int, cantidad: int):
        """cantidad positiva = suma, negativa = resta."""
        self._ejecutar(
            "UPDATE productos SET stock = stock + ? WHERE id = ?",
            (cantidad, id)
        )

    def eliminar(self, id: int):
        self._ejecutar("DELETE FROM productos WHERE id = ?", (id,))