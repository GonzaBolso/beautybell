from repository.base_repo import BaseRepo


class ClienteRepo(BaseRepo):

    def obtener_todos(self):
        return self._todos(
            "SELECT * FROM clientes ORDER BY nombre"
        )

    def obtener_por_id(self, id: int):
        return self._uno(
            "SELECT * FROM clientes WHERE id = ?", (id,)
        )

    def buscar(self, texto: str):
        like = f"%{texto}%"
        return self._todos(
            "SELECT * FROM clientes WHERE nombre LIKE ? OR telefono LIKE ? ORDER BY nombre",
            (like, like)
        )

    def crear(self, nombre: str, telefono: str = "", email: str = "", observaciones: str = "") -> int:
        cur = self._ejecutar(
            "INSERT INTO clientes (nombre, telefono, email, observaciones) VALUES (?, ?, ?, ?)",
            (nombre, telefono, email, observaciones)
        )
        return self._ultimo_id(cur)

    def actualizar(self, id: int, nombre: str, telefono: str, email: str, observaciones: str):
        self._ejecutar(
            "UPDATE clientes SET nombre=?, telefono=?, email=?, observaciones=? WHERE id=?",
            (nombre, telefono, email, observaciones, id)
        )

    def eliminar(self, id: int):
        self._ejecutar("DELETE FROM clientes WHERE id = ?", (id,))