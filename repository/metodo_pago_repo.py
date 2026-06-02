from repository.base_repo import BaseRepo


class MetodoPagoRepo(BaseRepo):

    def obtener_todos(self):
        return self._todos(
            "SELECT * FROM metodos_pago ORDER BY nombre"
        )

    def obtener_activos(self):
        return self._todos(
            "SELECT * FROM metodos_pago WHERE activo = 1 ORDER BY nombre"
        )

    def obtener_por_id(self, id: int):
        return self._uno(
            "SELECT * FROM metodos_pago WHERE id = ?", (id,)
        )

    def crear(self, nombre: str) -> int:
        cur = self._ejecutar(
            "INSERT INTO metodos_pago (nombre) VALUES (?)",
            (nombre,)
        )
        return self._ultimo_id(cur)

    def actualizar(self, id: int, nombre: str, activo: bool):
        self._ejecutar(
            "UPDATE metodos_pago SET nombre=?, activo=? WHERE id=?",
            (nombre, int(activo), id)
        )

    def eliminar(self, id: int):
        self._ejecutar("DELETE FROM metodos_pago WHERE id = ?", (id,))