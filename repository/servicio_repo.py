from repository.base_repo import BaseRepo


class ServicioRepo(BaseRepo):

    def obtener_todos(self):
        return self._todos(
            "SELECT * FROM servicios ORDER BY categoria, nombre"
        )

    def obtener_activos(self):
        return self._todos(
            "SELECT * FROM servicios WHERE activo = 1 ORDER BY categoria, nombre"
        )

    def obtener_por_id(self, id: int):
        return self._uno(
            "SELECT * FROM servicios WHERE id = ?", (id,)
        )

    def obtener_categorias(self) -> list[str]:
        """Devuelve la lista de categorías únicas ya cargadas (sin vacías)."""
        rows = self._todos(
            "SELECT DISTINCT categoria FROM servicios "
            "WHERE categoria != '' ORDER BY categoria"
        )
        return [r["categoria"] for r in rows]

    def crear(self, nombre: str, categoria: str, precio: float,
              duracion_min: int = 60) -> int:
        cur = self._ejecutar(
            "INSERT INTO servicios (nombre, categoria, precio, duracion_min) "
            "VALUES (?, ?, ?, ?)",
            (nombre, categoria, precio, duracion_min)
        )
        return self._ultimo_id(cur)

    def actualizar(self, id: int, nombre: str, categoria: str,
                   precio: float, duracion_min: int, activo: bool):
        self._ejecutar(
            "UPDATE servicios "
            "SET nombre=?, categoria=?, precio=?, duracion_min=?, activo=? "
            "WHERE id=?",
            (nombre, categoria, precio, duracion_min, int(activo), id)
        )

    def eliminar(self, id: int):
        self._ejecutar("DELETE FROM servicios WHERE id = ?", (id,))