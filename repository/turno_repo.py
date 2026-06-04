from repository.base_repo import BaseRepo


class TurnoRepo(BaseRepo):

    # ------------------------------------------------------------------ #
    #  Consultas principales                                               #
    # ------------------------------------------------------------------ #

    def obtener_por_fecha(self, fecha: str):
        """fecha en formato YYYY-MM-DD"""
        turnos = self._todos(
            """
            SELECT t.*, c.nombre AS cliente_nombre, e.nombre AS empleada_nombre,
                   s.nombre AS servicio_nombre, s.precio AS servicio_precio
            FROM turnos t
            JOIN clientes  c ON c.id = t.cliente_id
            JOIN empleadas e ON e.id = t.empleada_id
            LEFT JOIN servicios s ON s.id = t.servicio_id
            WHERE date(t.fecha_hora) = ?
            ORDER BY t.fecha_hora
            """,
            (fecha,)
        )
        return [self._enriquecer_con_servicios(dict(t)) for t in turnos]

    def obtener_por_rango(self, fecha_desde: str, fecha_hasta: str):
        turnos = self._todos(
            """
            SELECT t.*, c.nombre AS cliente_nombre, e.nombre AS empleada_nombre,
                   s.nombre AS servicio_nombre, s.precio AS servicio_precio
            FROM turnos t
            JOIN clientes  c ON c.id = t.cliente_id
            JOIN empleadas e ON e.id = t.empleada_id
            LEFT JOIN servicios s ON s.id = t.servicio_id
            WHERE date(t.fecha_hora) BETWEEN ? AND ?
            ORDER BY t.fecha_hora
            """,
            (fecha_desde, fecha_hasta)
        )
        return [self._enriquecer_con_servicios(dict(t)) for t in turnos]

    def obtener_por_id(self, id: int):
        row = self._uno(
            """
            SELECT t.*, c.nombre AS cliente_nombre, e.nombre AS empleada_nombre,
                   s.nombre AS servicio_nombre, s.precio AS servicio_precio
            FROM turnos t
            JOIN clientes  c ON c.id = t.cliente_id
            JOIN empleadas e ON e.id = t.empleada_id
            LEFT JOIN servicios s ON s.id = t.servicio_id
            WHERE t.id = ?
            """,
            (id,)
        )
        if row is None:
            return None
        return self._enriquecer_con_servicios(dict(row))

    def obtener_servicios_de_turno(self, turno_id: int) -> list:
        """Devuelve lista de {servicio_id, servicio_nombre, precio} del turno."""
        rows = self._todos(
            """
            SELECT ts.id AS ts_id, ts.servicio_id, ts.precio,
                   s.nombre AS servicio_nombre, s.duracion_min
            FROM turno_servicios ts
            JOIN servicios s ON s.id = ts.servicio_id
            WHERE ts.turno_id = ?
            ORDER BY ts.id
            """,
            (turno_id,)
        )
        return [dict(r) for r in rows]

    def _enriquecer_con_servicios(self, turno: dict) -> dict:
        """Agrega la lista de servicios al dict del turno."""
        servicios = self.obtener_servicios_de_turno(turno["id"])

        # Si no hay entradas en turno_servicios, construir desde campos legacy
        if not servicios and turno.get("servicio_id"):
            servicios = [{
                "ts_id": None,
                "servicio_id": turno["servicio_id"],
                "precio": turno.get("servicio_precio") or 0,
                "servicio_nombre": turno.get("servicio_nombre") or "",
                "duracion_min": 60,
            }]
            # Migrar al vuelo para que la proxima vez ya este en la tabla
            try:
                self._ejecutar(
                    "INSERT INTO turno_servicios (turno_id, servicio_id, precio) VALUES (?,?,?)",
                    (turno["id"], turno["servicio_id"], turno.get("servicio_precio") or 0)
                )
            except Exception:
                pass

        turno["servicios"] = servicios
        turno["precio_total"] = sum(s["precio"] for s in servicios)
        return turno

    def obtener_solapados(self, empleada_id: int, fecha_hora: str, duracion_min: int, excluir_id: int = None):
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

    # ------------------------------------------------------------------ #
    #  Escritura                                                           #
    # ------------------------------------------------------------------ #

    def crear(self, cliente_id: int, empleada_id: int, servicio_id: int,
              fecha_hora: str, estado: str = "pendiente", notas: str = "") -> int:
        cur = self._ejecutar(
            """INSERT INTO turnos (cliente_id, empleada_id, servicio_id, fecha_hora, estado, notas)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (cliente_id, empleada_id, servicio_id, fecha_hora, estado, notas)
        )
        return self._ultimo_id(cur)

    def guardar_servicios(self, turno_id: int, servicios: list):
        """
        servicios: lista de dicts con {servicio_id, precio}
        Reemplaza todos los servicios del turno.
        """
        self._ejecutar("DELETE FROM turno_servicios WHERE turno_id = ?", (turno_id,))
        for srv in servicios:
            self._ejecutar(
                "INSERT INTO turno_servicios (turno_id, servicio_id, precio) VALUES (?,?,?)",
                (turno_id, srv["servicio_id"], srv["precio"])
            )

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