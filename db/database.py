import sqlite3
import os
import sys


def _db_path() -> str:
    """
    En desarrollo: carpeta raiz del proyecto.
    Empaquetado con PyInstaller --onefile: carpeta del .exe.
    """
    if hasattr(sys, "_MEIPASS"):
        # Ejecutable — guardar DB al lado del .exe
        return os.path.join(os.path.dirname(sys.executable), "beautybel.db")
    # Desarrollo
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "beautybel.db")


DB_PATH = _db_path()


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def inicializar_db():
    """Crea todas las tablas si no existen y carga datos iniciales."""
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
            servicio_id  INTEGER NOT NULL REFERENCES servicios(id),
            fecha_hora   TEXT    NOT NULL,
            estado       TEXT    NOT NULL DEFAULT 'pendiente'
                             CHECK(estado IN ('pendiente','confirmado','completado','cancelado')),
            notas        TEXT
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
    """
    Agrega columnas nuevas a tablas existentes si la DB ya existia
    sin ellas (ALTER TABLE es seguro: falla silenciosamente si la
    columna ya existe, por eso usamos el try/except por columna).
    """
    migraciones = [
        ("ALTER TABLE servicios    ADD COLUMN categoria TEXT NOT NULL DEFAULT ''",),
        ("ALTER TABLE lista_precios ADD COLUMN categoria TEXT NOT NULL DEFAULT ''",),
    ]
    for (sql,) in migraciones:
        try:
            conn.execute(sql)
            conn.commit()
        except Exception:
            # La columna ya existe — ignorar
            pass


def _cargar_seeds(conn: sqlite3.Connection):
    """Inserta datos iniciales solo si las tablas están vacías."""

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