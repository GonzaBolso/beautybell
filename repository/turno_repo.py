from repository.base_repo import BaseRepo


class TurnoRepo(BaseRepo):

    def obtener_por_fecha(self, fecha: str):
        """fecha en formato YYYY-MM-DD"""
        return self._todos(
            """
            SELECT t.*, c.nombre AS cliente_nombre, e.nombre AS empleada_nombre,
                   s.nombre AS servicio_nombre, s.precio AS servicio_precio
            FROM turnos t
            JOIN clientes  c ON c.id = t.cliente_id
            JOIN empleadas e ON e.id = t.empleada_id
            JOIN servicios s ON s.id = t.servicio_id
            WHERE date(t.fecha_hora) = ?
            ORDER BY t.fecha_hora
            """,
            (fecha,)
        )

    def obtener_por_rango(self, fecha_desde: str, fecha_hasta: str):
        return self._todos(
            """
            SELECT t.*, c.nombre AS cliente_nombre, e.nombre AS empleada_nombre,
                   s.nombre AS servicio_nombre, s.precio AS servicio_precio
            FROM turnos t
            JOIN clientes  c ON c.id = t.cliente_id
            JOIN empleadas e ON e.id = t.empleada_id
            JOIN servicios s ON s.id = t.servicio_id
            WHERE date(t.fecha_hora) BETWEEN ? AND ?
            ORDER BY t.fecha_hora
            """,
            (fecha_desde, fecha_hasta)
        )

    def obtener_por_id(self, id: int):
        return self._uno(
            """
            SELECT t.*, c.nombre AS cliente_nombre, e.nombre AS empleada_nombre,
                   s.nombre AS servicio_nombre, s.precio AS servicio_precio
            FROM turnos t
            JOIN clientes  c ON c.id = t.cliente_id
            JOIN empleadas e ON e.id = t.empleada_id
            JOIN servicios s ON s.id = t.servicio_id
            WHERE t.id = ?
            """,
            (id,)
        )

    def obtener_solapados(self, empleada_id: int, fecha_hora: str, duracion_min: int, excluir_id: int = None):
        """
        Devuelve turnos activos de la misma empleada que se solapan con el horario dado.
        Usado por TurnoService para validar conflictos.
        """
        sql = """
            SELECT t.* FROM turnos t
            JOIN servicios s ON s.id = t.servicio_id
            WHERE t.empleada_id = ?
              AND t.estado NOT IN ('cancelado')
              AND t.id != COALESCE(?, -1)
              AND datetime(t.fecha_hora) < datetime(?, '+' || ? || ' minutes')
              AND datetime(t.fecha_hora, '+' || s.duracion_min || ' minutes') > datetime(?)
        """
        return self._todos(sql, (empleada_id, excluir_id, fecha_hora, duracion_min, fecha_hora))

    def crear(self, cliente_id: int, empleada_id: int, servicio_id: int,
              fecha_hora: str, estado: str = "pendiente", notas: str = "") -> int:
        cur = self._ejecutar(
            """INSERT INTO turnos (cliente_id, empleada_id, servicio_id, fecha_hora, estado, notas)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (cliente_id, empleada_id, servicio_id, fecha_hora, estado, notas)
        )
        return self._ultimo_id(cur)

    def actualizar_estado(self, id: int, estado: str):
        self._ejecutar(
            "UPDATE turnos SET estado = ? WHERE id = ?",
            (estado, id)
        )

    def actualizar(self, id: int, cliente_id: int, empleada_id: int, servicio_id: int,
                   fecha_hora: str, estado: str, notas: str):
        self._ejecutar(
            """UPDATE turnos SET cliente_id=?, empleada_id=?, servicio_id=?,
               fecha_hora=?, estado=?, notas=? WHERE id=?""",
            (cliente_id, empleada_id, servicio_id, fecha_hora, estado, notas, id)
        )

    def eliminar(self, id: int):
        self._ejecutar("DELETE FROM turnos WHERE id = ?", (id,))