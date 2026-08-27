from datetime import datetime
from repository.historial_repo import HistorialRepo

TIPOS = ["Color", "Baño Color", "Corte", "Progresivo", "Tratamientos"]


def _validar_fecha(fecha: str) -> str | None:
    """Devuelve la fecha normalizada (YYYY-MM-DD) o None si es inválida."""
    try:
        return datetime.strptime(fecha.strip(), "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return None


class HistorialService:
    """Lógica de negocio para el historial de clientas."""

    def __init__(self):
        self._repo = HistorialRepo()

    def obtener_por_cliente(self, cliente_id: int) -> list:
        return self._repo.obtener_por_cliente(cliente_id)

    def crear(self, cliente_id: int, tipo: str, descripcion: str,
              fecha: str = None) -> tuple[bool, str, int | None]:
        tipo = tipo.strip()
        descripcion = descripcion.strip()
        if tipo not in TIPOS:
            return False, "Elegí un tipo válido.", None
        if not descripcion:
            return False, "La descripción no puede estar vacía.", None
        fecha_norm = None
        if fecha is not None:
            fecha_norm = _validar_fecha(fecha)
            if fecha_norm is None:
                return False, "La fecha debe tener el formato AAAA-MM-DD.", None
        id_ = self._repo.crear(cliente_id, tipo, descripcion, fecha_norm)
        return True, "Item de historial creado correctamente.", id_

    def actualizar(self, id: int, tipo: str, descripcion: str, fecha: str) -> tuple[bool, str]:
        tipo = tipo.strip()
        descripcion = descripcion.strip()
        if tipo not in TIPOS:
            return False, "Elegí un tipo válido."
        if not descripcion:
            return False, "La descripción no puede estar vacía."
        fecha_norm = _validar_fecha(fecha)
        if fecha_norm is None:
            return False, "La fecha debe tener el formato AAAA-MM-DD."
        self._repo.actualizar(id, tipo, descripcion, fecha_norm)
        return True, "Item de historial actualizado correctamente."

    def eliminar(self, id: int):
        self._repo.eliminar(id)
