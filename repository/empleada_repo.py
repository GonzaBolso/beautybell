from repository.base_repo import BaseRepo


class EmpleadaRepo(BaseRepo):

    def obtener_todas(self):
        return self._todos(
            "SELECT * FROM empleadas ORDER BY nombre"
        )

    def obtener_activas(self):
        return self._todos(
            "SELECT * FROM empleadas WHERE activa = 1 ORDER BY nombre"
        )

    def obtener_por_id(self, id: int):
        return self._uno(
            "SELECT * FROM empleadas WHERE id = ?", (id,)
        )

    def crear(self, nombre: str, telefono: str = "") -> int:
        cur = self._ejecutar(
            "INSERT INTO empleadas (nombre, telefono) VALUES (?, ?)",
            (nombre, telefono)
        )
        return self._ultimo_id(cur)

    def actualizar(self, id: int, nombre: str, telefono: str, activa: bool):
        self._ejecutar(
            "UPDATE empleadas SET nombre=?, telefono=?, activa=? WHERE id=?",
            (nombre, telefono, int(activa), id)
        )