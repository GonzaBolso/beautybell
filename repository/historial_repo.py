from repository.base_repo import BaseRepo


class HistorialRepo(BaseRepo):

    def obtener_por_cliente(self, cliente_id: int):
        return self._todos(
            "SELECT * FROM historial_clientas WHERE cliente_id = ? "
            "ORDER BY fecha DESC, id DESC",
            (cliente_id,)
        )

    def obtener_por_id(self, id: int):
        return self._uno(
            "SELECT * FROM historial_clientas WHERE id = ?", (id,)
        )

    def crear(self, cliente_id: int, tipo: str, descripcion: str, fecha: str = None) -> int:
        if fecha:
            cur = self._ejecutar(
                "INSERT INTO historial_clientas (cliente_id, tipo, descripcion, fecha) VALUES (?, ?, ?, ?)",
                (cliente_id, tipo, descripcion, fecha)
            )
        else:
            cur = self._ejecutar(
                "INSERT INTO historial_clientas (cliente_id, tipo, descripcion) VALUES (?, ?, ?)",
                (cliente_id, tipo, descripcion)
            )
        return self._ultimo_id(cur)

    def actualizar(self, id: int, tipo: str, descripcion: str, fecha: str):
        self._ejecutar(
            "UPDATE historial_clientas SET tipo=?, descripcion=?, fecha=? WHERE id=?",
            (tipo, descripcion, fecha, id)
        )

    def eliminar(self, id: int):
        self._ejecutar("DELETE FROM historial_clientas WHERE id = ?", (id,))
