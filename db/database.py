import sqlite3
import os
import sys


def _db_path() -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(os.path.dirname(sys.executable), "beautybel.db")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "beautybel.db")


DB_PATH = _db_path()


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def inicializar_db():
    conn = get_connection()
    try:
        _crear_tablas(conn)
        _migraciones(conn)
        _cargar_seeds(conn)
        conn.commit()
    finally:
        conn.close()


def _crear_tablas(conn: sqlite3.Connection):
    conn.executescript("""

        CREATE TABLE IF NOT EXISTS empleadas (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre  TEXT    NOT NULL,
            telefono TEXT,
            activa  INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS clientes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre          TEXT    NOT NULL,
            telefono        TEXT,
            email           TEXT,
            fecha_registro  TEXT    NOT NULL DEFAULT (date('now')),
            observaciones   TEXT
        );

        CREATE TABLE IF NOT EXISTS servicios (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre       TEXT    NOT NULL,
            categoria    TEXT    NOT NULL DEFAULT '',
            precio       REAL    NOT NULL DEFAULT 0,
            duracion_min INTEGER NOT NULL DEFAULT 60,
            activo       INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS metodos_pago (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT    NOT NULL UNIQUE,
            activo INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS turnos (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id   INTEGER NOT NULL REFERENCES clientes(id),
            empleada_id  INTEGER NOT NULL REFERENCES empleadas(id),
            servicio_id  INTEGER REFERENCES servicios(id),
            fecha_hora   TEXT    NOT NULL,
            estado       TEXT    NOT NULL DEFAULT 'pendiente'
                             CHECK(estado IN ('pendiente','confirmado','completado','cancelado')),
            notas        TEXT
        );

        -- Tabla para multiples servicios por turno
        CREATE TABLE IF NOT EXISTS turno_servicios (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            turno_id    INTEGER NOT NULL REFERENCES turnos(id) ON DELETE CASCADE,
            servicio_id INTEGER NOT NULL REFERENCES servicios(id),
            precio      REAL    NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS caja_movimientos (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha           TEXT    NOT NULL DEFAULT (date('now')),
            tipo            TEXT    NOT NULL CHECK(tipo IN ('ingreso','egreso')),
            categoria       TEXT    NOT NULL,
            monto           REAL    NOT NULL,
            metodo_pago_id  INTEGER REFERENCES metodos_pago(id),
            descripcion     TEXT,
            turno_id        INTEGER REFERENCES turnos(id),
            proveedor_id    INTEGER REFERENCES proveedores(id),
            producto_id     INTEGER REFERENCES productos(id)
        );

        CREATE TABLE IF NOT EXISTS proveedores (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre    TEXT NOT NULL,
            telefono  TEXT,
            email     TEXT,
            direccion TEXT,
            notas     TEXT
        );

        CREATE TABLE IF NOT EXISTS productos (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor_id   INTEGER REFERENCES proveedores(id),
            nombre         TEXT    NOT NULL,
            categoria      TEXT,
            precio_costo   REAL    NOT NULL DEFAULT 0,
            precio_venta   REAL    NOT NULL DEFAULT 0,
            stock          INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS compras_proveedor (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor_id   INTEGER NOT NULL REFERENCES proveedores(id),
            metodo_pago_id INTEGER REFERENCES metodos_pago(id),
            fecha          TEXT    NOT NULL DEFAULT (date('now')),
            total          REAL    NOT NULL DEFAULT 0,
            notas          TEXT
        );

        CREATE TABLE IF NOT EXISTS compras_detalle (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            compra_id       INTEGER NOT NULL REFERENCES compras_proveedor(id),
            producto_id     INTEGER NOT NULL REFERENCES productos(id),
            cantidad        INTEGER NOT NULL DEFAULT 1,
            precio_unitario REAL    NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS lista_precios (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT    NOT NULL,
            categoria   TEXT    NOT NULL DEFAULT '',
            precio      REAL    NOT NULL DEFAULT 0,
            descuento   REAL    NOT NULL DEFAULT 0,
            destacado   INTEGER NOT NULL DEFAULT 0,
            activo      INTEGER NOT NULL DEFAULT 1
        );

    """)


def _migraciones(conn: sqlite3.Connection):
    migraciones = [
        ("ALTER TABLE servicios     ADD COLUMN categoria TEXT NOT NULL DEFAULT ''",),
        ("ALTER TABLE lista_precios ADD COLUMN categoria TEXT NOT NULL DEFAULT ''",),
        ("ALTER TABLE lista_precios ADD COLUMN precios   TEXT NOT NULL DEFAULT ''",),
        # turno_servicios ya se crea en _crear_tablas, pero por si la DB es vieja:
        ("""CREATE TABLE IF NOT EXISTS turno_servicios (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            turno_id    INTEGER NOT NULL REFERENCES turnos(id) ON DELETE CASCADE,
            servicio_id INTEGER NOT NULL REFERENCES servicios(id),
            precio      REAL    NOT NULL DEFAULT 0
        )""",),
        # Cada servicio del turno puede pertenecer a una empleada distinta
        ("ALTER TABLE turno_servicios ADD COLUMN empleada_id INTEGER REFERENCES empleadas(id)",),
    ]
    for (sql,) in migraciones:
        try:
            conn.execute(sql)
            conn.commit()
        except Exception:
            pass

    # Migrar turnos existentes a turno_servicios si aun no tienen entradas
    try:
        rows = conn.execute(
            """SELECT t.id, t.servicio_id, t.empleada_id, s.precio
               FROM turnos t
               JOIN servicios s ON s.id = t.servicio_id
               WHERE t.servicio_id IS NOT NULL
                 AND NOT EXISTS (
                     SELECT 1 FROM turno_servicios ts WHERE ts.turno_id = t.id
                 )"""
        ).fetchall()
        for row in rows:
            conn.execute(
                "INSERT INTO turno_servicios (turno_id, servicio_id, empleada_id, precio) VALUES (?,?,?,?)",
                (row["id"], row["servicio_id"], row["empleada_id"], row["precio"])
            )
        if rows:
            conn.commit()
    except Exception:
        pass

    # Completar empleada_id en filas viejas de turno_servicios con la empleada del turno
    try:
        cur = conn.execute(
            """UPDATE turno_servicios
               SET empleada_id = (
                   SELECT empleada_id FROM turnos WHERE turnos.id = turno_servicios.turno_id
               )
               WHERE empleada_id IS NULL"""
        )
        if cur.rowcount:
            conn.commit()
    except Exception:
        pass


def _cargar_seeds(conn: sqlite3.Connection):
    metodos = ["Efectivo", "MercadoPago", "Débito", "Crédito"]
    for nombre in metodos:
        conn.execute(
            "INSERT OR IGNORE INTO metodos_pago (nombre) VALUES (?)",
            (nombre,)
        )

    existe_empleada = conn.execute("SELECT COUNT(*) FROM empleadas").fetchone()[0]
    if not existe_empleada:
        conn.execute(
            "INSERT INTO empleadas (nombre, telefono) VALUES (?, ?)",
            ("Propietaria", "")
        )