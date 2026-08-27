# CLAUDE.md

Este archivo le da contexto a Claude Code (claude.ai/code) al trabajar en este repositorio.

## Qué es esto

BeautyBel es una app de escritorio para Windows (Tkinter/customtkinter) para gestionar
una peluquería/salón de belleza: turnos, clientes, caja, proveedores/productos
(insumos/inventario), una lista de precios y el historial de clientas. Un solo usuario,
base de datos SQLite local, empaquetada con PyInstaller en un `.exe` independiente.

## Comandos

```bash
# Instalar dependencias (el venv ya está en .venv/)
./.venv/Scripts/python.exe -m pip install -r requirements.txt

# Correr la app
./.venv/Scripts/python.exe main.py

# Compilar el ejecutable de Windows (ver beautybel.spec)
pyinstaller beautybel.spec
```

No hay suite de tests ni linter configurado en este repo. Para verificar cambios,
corré la app manualmente o escribí un script descartable que apunte
`db.database.DB_PATH` a un archivo temporal, llame a `inicializar_db()`, y ejercite
la capa de repository/service directamente (así no se toca el `beautybel.db` real).

## Arquitectura

Tres capas, cada una hablando solo con la que está debajo:

```
ui/*_view.py  →  services/*_service.py  →  repository/*_repo.py  →  db/database.py (SQLite)
```

- **`db/database.py`** — única fuente de verdad del schema. `inicializar_db()`
  (llamada una vez desde `MainWindow.__init__`) ejecuta `_crear_tablas()` (`CREATE
  TABLE IF NOT EXISTS`, idempotente), luego `_migraciones()`, y después
  `_cargar_seeds()`. No hay archivos de migración separados ni versionado: los
  cambios de schema son sentencias `ALTER TABLE` aditivas agregadas a la lista de
  `_migraciones()`, cada una envuelta en try/except para que volver a correrlas sea
  seguro tanto en bases de datos nuevas como existentes. Los backfills de datos
  puntuales (por ejemplo, poblar una columna nueva a partir de una existente) también
  se escriben directamente en `_migraciones()`. `DB_PATH` resuelve al lado del `.exe`
  cuando está empaquetado (`sys._MEIPASS`) o a la raíz del proyecto en desarrollo.
- **`repository/*_repo.py`** — un repo por tabla/entidad, todos heredando de
  `BaseRepo` (`repository/base_repo.py`) para sus helpers `_ejecutar` / `_uno` /
  `_todos` / `_ultimo_id`. Los repos solo contienen SQL crudo, sin reglas de negocio.
- **`services/*_service.py`** — validaciones y reglas de negocio (por ejemplo,
  `TurnoService` valida turnos superpuestos por empleada, `CajaService` maneja pagos
  con múltiples métodos). Las vistas nunca llaman a los repos directamente.
- **`ui/*_view.py`** — un archivo por módulo del sidebar (`turnos`, `clientes`,
  `caja`, `proveedores`, `configuracion`, `precios`, `historial_clientas`),
  registrado en `MainWindow.MODULOS` (`ui/main_window.py`) e importado de forma
  perezosa (lazy) en `_crear_vista`. Cada vista hereda de `VistaBase`
  (`ui/vista_base.py`), que provee el encabezado con título y un frame `.contenido`;
  las vistas sobreescriben `_construir_contenido()`. Las fábricas de widgets
  compartidas (`boton_primario`, `campo_texto`, `card`, `mostrar_error`, `confirmar`,
  etc.) viven en `ui/widgets.py`; los colores/fuentes vienen de `ui/tema.py`
  (`COLORES`, `FUENTES`) — siempre hay que reusar esto en vez de poner colores hex o
  fuentes hardcodeadas en una vista.

### Turnos — el módulo más complejo

Un turno pertenece a una sola cliente pero puede tener **múltiples empleadas, cada
una con su propio conjunto de servicios**. Esto se modela como una lista plana de
líneas de servicio (`turno_servicios`: `turno_id, servicio_id, empleada_id, precio`),
no como una estructura anidada — el agrupamiento por empleada pasa en Python (capas
de vista y repo), no en SQL. `turnos.empleada_id` / `turnos.servicio_id` todavía
existen como columnas de conveniencia legacy (autocompletadas con la *primera* línea
de servicio) para que los joins viejos sigan funcionando; no agregues lógica nueva
que las lea como fuente de verdad — usá `turno["servicios"]`
(`TurnoRepo.obtener_servicios_de_turno` / `_enriquecer_con_servicios`) en su lugar.

La validación de superposición (`TurnoService._validar`) chequea el solapamiento
**por empleada** de forma independiente — dos empleadas distintas pueden tener
servicios en el mismo `fecha_hora` en el mismo turno, pero la misma empleada no puede
tener doble reserva entre turnos.

`ui/turnos_view.py::_FormTurno` renderiza una tarjeta por empleada
(`_grupos_empleados`), cada una con sus propias filas de servicio y subtotal;
`_TarjetaTurno` y `_DialogCobro` agrupan `turno["servicios"]` por `empleada_nombre`
para mostrarlos, y la descripción del cobro ("Cobro: Cliente - Servicios -
Empleadas") es parseada posicionalmente por `services/excel_export.py` — si tocás
eso, mantené ese formato unido por " - ".

### Historial Clientas

Cada fila de `historial_clientas` (`cliente_id, tipo, descripcion, fecha`) es **un
item individual**, no un registro por día: si en una misma visita se le hacen varios
servicios a la clienta (por ejemplo Color + Corte + Progresivo), se crea una fila por
cada tipo, cada una con su propia descripción libre, todas con la misma `fecha`
(default `date('now')`). `tipo` está restringido en `HistorialService.TIPOS`
(`Color`, `Baño Color`, `Corte`, `Progresivo`, `Tratamientos`) — no es una tabla
libre, así que si se agrega un tipo nuevo hay que sumarlo ahí.
`ui/historial_clientas_view.py` tiene dos formularios distintos: `_construir_form_multiple`
(alta, con checkbox + descripción por cada tipo, para cargar varios items de una
vez) y `_construir_form_edicion` (un solo tipo + descripción, para corregir un item
ya creado desde la lista).

### Empaquetado

`resource_path()` (duplicada en `Utils.py` y `ui/main_window.py`) resuelve las rutas
de assets (`assets/`) tanto en desarrollo como empaquetada con PyInstaller
(`sys._MEIPASS`). Cualquier asset nuevo tiene que agregarse a `datas=[...]` en
`beautybel.spec` o no se va a incluir en el `.exe` compilado.
