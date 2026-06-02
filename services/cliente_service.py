from repository.cliente_repo import ClienteRepo


class ClienteService:
    """Lógica de negocio para clientes."""

    def __init__(self):
        self._repo = ClienteRepo()

    def obtener_todos(self) -> list:
        return self._repo.obtener_todos()

    def obtener_por_id(self, id: int):
        return self._repo.obtener_por_id(id)

    def buscar(self, texto: str) -> list:
        return self._repo.buscar(texto)

    def crear(self, nombre: str, telefono: str = "",
              email: str = "", observaciones: str = "") -> tuple[bool, str, int | None]:
        nombre = nombre.strip()
        if not nombre:
            return False, "El nombre no puede estar vacío.", None
        id_ = self._repo.crear(nombre, telefono.strip(), email.strip(), observaciones.strip())
        return True, "Cliente creado correctamente.", id_

    def actualizar(self, id: int, nombre: str, telefono: str,
                   email: str, observaciones: str) -> tuple[bool, str]:
        nombre = nombre.strip()
        if not nombre:
            return False, "El nombre no puede estar vacío."
        self._repo.actualizar(id, nombre, telefono.strip(), email.strip(), observaciones.strip())
        return True, "Cliente actualizado correctamente."

    def eliminar(self, id: int):
        self._repo.eliminar(id)