from repository.base_repo import BaseRepo


class ProveedorRepo(BaseRepo):

    def obtener_todos(self):
        return self._todos(
            "SELECT * FROM proveedores ORDER BY nombre"
        )

    def obtener_por_id(self, id: int):
        return self._uno(
            "SELECT * FROM proveedores WHERE id = ?", (id,)
        )

    def buscar(self, texto: str):
        like = f"%{texto}%"
        return self._todos(
            "SELECT * FROM proveedores WHERE nombre LIKE ? OR telefono LIKE ? ORDER BY nombre",
            (like, like)
        )

    def crear(self, nombre: str, telefono: str = "", email: str = "",
              direccion: str = "", notas: str = "") -> int:
        cur = self._ejecutar(
            "INSERT INTO proveedores (nombre, telefono, email, direccion, notas) VALUES (?, ?, ?, ?, ?)",
            (nombre, telefono, email, direccion, notas)
        )
        return self._ultimo_id(cur)

    def actualizar(self, id: int, nombre: str, telefono: str, email: str,
                   direccion: str, notas: str):
        self._ejecutar(
            "UPDATE proveedores SET nombre=?, telefono=?, email=?, direccion=?, notas=? WHERE id=?",
            (nombre, telefono, email, direccion, notas, id)
        )

    def eliminar(self, id: int):
        self._ejecutar("DELETE FROM proveedores WHERE id = ?", (id,))