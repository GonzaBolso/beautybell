# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

BeautyBel is a Windows desktop app (Tkinter/customtkinter) for managing a beauty
salon: turnos (appointments), clientes, caja (cash register), proveedores/productos
(suppliers/inventory), and a price list. Single-user, local SQLite database, packaged
with PyInstaller into a standalone `.exe`.

## Commands

```bash
# Install dependencies (venv already at .venv/)
./.venv/Scripts/python.exe -m pip install -r requirements.txt

# Run the app
./.venv/Scripts/python.exe main.py

# Build the Windows executable (see beautybel.spec)
pyinstaller beautybel.spec
```

There is no test suite and no linter configured in this repo. When verifying changes,
either run the app manually or write a throwaway script that points
`db.database.DB_PATH` at a temp file, calls `inicializar_db()`, and exercises the
repo/service layer directly (avoids touching the real `beautybel.db`).

## Architecture

Three layers, each only talking to the one below it:

```
ui/*_view.py  →  services/*_service.py  →  repository/*_repo.py  →  db/database.py (SQLite)
```

- **`db/database.py`** — single source of schema truth. `inicializar_db()` (called
  once from `MainWindow.__init__`) runs `_crear_tablas()` (idempotent `CREATE TABLE IF
  NOT EXISTS`), then `_migraciones()`, then `_cargar_seeds()`. There are no separate
  migration files/versioning: schema changes are additive `ALTER TABLE` statements
  appended to the `_migraciones()` list, each wrapped in try/except so re-running is
  safe on both fresh and existing databases. One-off data backfills (e.g. populating a
  new column from an existing one) are also written directly in `_migraciones()`.
  `DB_PATH` resolves next to the `.exe` when frozen (`sys._MEIPASS`) or to the project
  root in dev.
- **`repository/*_repo.py`** — one repo per table/entity, all inheriting `BaseRepo`
  (`repository/base_repo.py`) for its `_ejecutar` / `_uno` / `_todos` / `_ultimo_id`
  helpers. Repos hold raw SQL only, no business rules.
- **`services/*_service.py`** — validation and business rules (e.g. `TurnoService`
  validates overlapping appointments per empleada, `CajaService` handles multi-method
  payments). Views never call repos directly.
- **`ui/*_view.py`** — one file per sidebar module (`turnos`, `clientes`, `caja`,
  `proveedores`, `configuracion`, `precios`), registered in `MainWindow.MODULOS`
  (`ui/main_window.py`) and lazily imported in `_crear_vista`. Every view subclasses
  `VistaBase` (`ui/vista_base.py`), which provides the title header and a `.contenido`
  frame; views override `_construir_contenido()`. Shared widget factories
  (`boton_primario`, `campo_texto`, `card`, `mostrar_error`, `confirmar`, etc.) live in
  `ui/widgets.py`; colors/fonts come from `ui/tema.py` (`COLORES`, `FUENTES`) — always
  reuse these instead of hardcoding hex colors or fonts in a view.

### Turnos (appointments) — the most involved module

A turno belongs to one cliente but can have **multiple empleadas, each with their own
set of servicios**. This is modeled as a flat list of service lines
(`turno_servicios`: `turno_id, servicio_id, empleada_id, precio`), not a nested
structure — grouping by empleada happens in Python (view and repo layers), not SQL.
`turnos.empleada_id` / `turnos.servicio_id` still exist as legacy convenience columns
(auto-filled from the *first* service line) so older joins keep working; don't add new
logic that reads them as the source of truth — use `turno["servicios"]`
(`TurnoRepo.obtener_servicios_de_turno` / `_enriquecer_con_servicios`) instead.

Overlap validation (`TurnoService._validar`) checks solapamiento **per empleada**
independently — two different empleadas can have services at the same `fecha_hora` on
the same turno, but the same empleada can't be double-booked across turnos.

`ui/turnos_view.py::_FormTurno` renders one card per empleada (`_grupos_empleados`),
each with its own service rows and subtotal; `_TarjetaTurno` and `_DialogCobro` group
`turno["servicios"]` by `empleada_nombre` for display, and the cobro description
("Cobro: Cliente - Servicios - Empleadas") is parsed positionally by
`services/excel_export.py` — keep that " - "-joined format if you touch it.

### Packaging

`resource_path()` (duplicated in `Utils.py` and `ui/main_window.py`) resolves asset
paths (`assets/`) both in dev and when frozen via PyInstaller (`sys._MEIPASS`). Any
new asset file must be added to `datas=[...]` in `beautybel.spec` or it won't ship in
the built `.exe`.