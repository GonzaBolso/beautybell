import sqlite3
from db.database import get_connection


class BaseRepo:
    """
    Clase base para todos los repositorios.
    Provee una conexión SQLite y métodos de ejecución comunes.
    Cada repo hereda de esta clase y nunca llama a get_connection() directamente.
    """

    def __init__(self):
        self._conn: sqlite3.Connection = get_connection()

    def cerrar(self):
        """Cierra la conexión. Llamar al terminar la sesión."""
        if self._conn:
            self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self._conn.rollback()
        else:
            self._conn.commit()
        self.cerrar()
        return False

    # ------------------------------------------------------------------ #
    #  Métodos de ejecución internos (solo usan los repos hijos)          #
    # ------------------------------------------------------------------ #

    def _ejecutar(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Ejecuta INSERT / UPDATE / DELETE y hace commit."""
        cursor = self._conn.execute(sql, params)
        self._conn.commit()
        return cursor

    def _uno(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        """Devuelve una sola fila o None."""
        return self._conn.execute(sql, params).fetchone()

    def _todos(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        """Devuelve todas las filas como lista."""
        return self._conn.execute(sql, params).fetchall()

    def _ultimo_id(self, cursor: sqlite3.Cursor) -> int:
        """Devuelve el id del último INSERT."""
        return cursor.lastrowid