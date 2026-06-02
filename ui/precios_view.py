"""
ui/precios_view.py
------------------
Vista de Precios — modulo independiente de Configuracion.
Lista servicios/productos con categoria, precio, descuento y destacado.
Incluye buscador en tiempo real; items destacados aparecen primero dentro
de cada categoria.
"""

import customtkinter as ctk
from db.database import get_connection
from ui.vista_base import VistaBase
from ui.tema import COLORES, FUENTES
from ui.widgets import (
    boton_primario, boton_secundario, boton_peligro,
    campo_texto, etiqueta, etiqueta_suave, card,
    separador, mostrar_error, mostrar_exito, confirmar,
)


# ------------------------------------------------------------------ #
#  Helpers de base de datos                                            #
# ------------------------------------------------------------------ #

def _crear_tabla_precios():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lista_precios (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT    NOT NULL,
            categoria   TEXT    NOT NULL DEFAULT '',
            precio      REAL    NOT NULL DEFAULT 0,
            descuento   REAL    NOT NULL DEFAULT 0,
            destacado   INTEGER NOT NULL DEFAULT 0,
            activo      INTEGER NOT NULL DEFAULT 1
        )
    """)
    try:
        conn.execute("ALTER TABLE lista_precios ADD COLUMN categoria TEXT NOT NULL DEFAULT ''")
    except Exception:
        pass
    conn.commit()
    conn.close()


def _obtener_todos():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM lista_precios ORDER BY categoria, destacado DESC, nombre"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _obtener_categorias() -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT categoria FROM lista_precios "
        "WHERE categoria != '' ORDER BY categoria"
    ).fetchall()
    conn.close()
    return [r["categoria"] for r in rows]


def _crear(nombre, categoria, precio, descuento, destacado):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO lista_precios (nombre, categoria, precio, descuento, destacado) "
        "VALUES (?,?,?,?,?)",
        (nombre, categoria, precio, descuento, int(destacado)),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def _actualizar(id_, nombre, categoria, precio, descuento, destacado, activo):
    conn = get_connection()
    conn.execute(
        "UPDATE lista_precios "
        "SET nombre=?, categoria=?, precio=?, descuento=?, destacado=?, activo=? "
        "WHERE id=?",
        (nombre, categoria, precio, descuento, int(destacado), int(activo), id_),
    )
    conn.commit()
    conn.close()


def _eliminar(id_):
    conn = get_connection()
    conn.execute("DELETE FROM lista_precios WHERE id=?", (id_,))
    conn.commit()
    conn.close()


# ------------------------------------------------------------------ #
#  Widget campo con sugerencias (autocompletado simple)               #
# ------------------------------------------------------------------ #

class _CampoConSugerencias(ctk.CTkFrame):
    def __init__(self, parent, sugerencias, placeholder="", **kwargs):
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.columnconfigure(0, weight=1)
        self._sugerencias = sugerencias
        self._popup = None

        self._var = ctk.StringVar()
        self._entry = ctk.CTkEntry(
            self,
            textvariable=self._var,
            placeholder_text=placeholder,
            height=36,
            fg_color=COLORES["fondo_input"],
            border_color=COLORES["borde"],
            text_color=COLORES["texto"],
            placeholder_text_color=COLORES["texto_suave"],
            corner_radius=8,
            font=FUENTES["normal"],
            **kwargs
        )
        self._entry.grid(row=0, column=0, sticky="ew")
        self._var.trace_add("write", self._on_cambio)
        self._entry.bind("<FocusOut>", lambda _: self._cerrar_popup())
        self._entry.bind("<Escape>",   lambda _: self._cerrar_popup())

    def get(self):
        return self._var.get()

    def insert(self, index, valor):
        self._var.set(valor)

    def _on_cambio(self, *_):
        texto = self._var.get().strip().upper()
        if not texto:
            self._cerrar_popup()
            return
        coincidencias = [s for s in self._sugerencias
                         if texto in s.upper() and s.upper() != texto]
        if coincidencias:
            self._mostrar_popup(coincidencias)
        else:
            self._cerrar_popup()

    def _mostrar_popup(self, opciones):
        self._cerrar_popup()
        root = self._entry.winfo_toplevel()
        self._popup = ctk.CTkToplevel(root)
        self._popup.overrideredirect(True)
        self._popup.attributes("-topmost", True)
        self._entry.update_idletasks()
        x = self._entry.winfo_rootx()
        y = self._entry.winfo_rooty() + self._entry.winfo_height() + 2
        ancho = self._entry.winfo_width()
        self._popup.geometry(f"{ancho}x{min(len(opciones)*36, 180)}+{x}+{y}")
        self._popup.configure(fg_color=COLORES["fondo_card"])
        for op in opciones[:6]:
            ctk.CTkButton(
                self._popup, text=op, anchor="w", height=34,
                fg_color="transparent", hover_color=COLORES["rosa_suave"],
                text_color=COLORES["texto"], font=FUENTES["normal"],
                corner_radius=0,
                command=lambda v=op: self._seleccionar(v),
            ).pack(fill="x")

    def _seleccionar(self, valor):
        self._var.set(valor)
        self._cerrar_popup()

    def _cerrar_popup(self):
        if self._popup:
            try:
                self._popup.destroy()
            except Exception:
                pass
            self._popup = None


# ------------------------------------------------------------------ #
#  Vista principal                                                     #
# ------------------------------------------------------------------ #

class PreciosView(VistaBase):

    def __init__(self, parent, **kwargs):
        _crear_tabla_precios()
        super().__init__(parent, titulo="Precios", **kwargs)

    def _construir_contenido(self):
        self._seleccionado = None

        outer = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        outer.pack(fill="both", expand=True, padx=24, pady=16)
        outer.rowconfigure(0, weight=1)
        outer.columnconfigure(0, weight=1)
        outer.columnconfigure(1, weight=2)

        # ---- Panel izquierdo ----
        self._panel_izq = card(outer)
        self._panel_izq.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self._panel_izq.rowconfigure(2, weight=1)
        self._panel_izq.columnconfigure(0, weight=1)

        cab = ctk.CTkFrame(self._panel_izq, fg_color="transparent")
        cab.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))
        cab.columnconfigure(0, weight=1)
        boton_primario(cab, "  + Nuevo precio",
                       comando=self._nuevo, ancho=0).grid(row=0, column=0, sticky="ew")

        self._var_busqueda = ctk.StringVar()
        self._var_busqueda.trace_add("write", lambda *_: self._filtrar())
        ctk.CTkEntry(
            self._panel_izq,
            textvariable=self._var_busqueda,
            placeholder_text="🔍  Buscar servicio o categoría...",
            height=34,
            fg_color=COLORES["fondo_input"],
            border_color=COLORES["borde"],
            text_color=COLORES["texto"],
            placeholder_text_color=COLORES["texto_suave"],
            corner_radius=8,
            font=FUENTES["normal"],
        ).grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 6))

        self._lista = ctk.CTkScrollableFrame(
            self._panel_izq, fg_color="transparent",
            scrollbar_button_color=COLORES["rosa"],
            scrollbar_button_hover_color=COLORES["rosa_hover"],
        )
        self._lista.grid(row=2, column=0, sticky="nsew", padx=6, pady=(0, 6))
        self._lista.columnconfigure(0, weight=1)

        # ---- Panel derecho ----
        self._panel_form = card(outer)
        self._panel_form.grid(row=0, column=1, sticky="nsew")
        self._panel_form.columnconfigure(0, weight=1)

        self._todos = []
        self._cargar()
        self._mostrar_vacio()

    # ---------------------------------------------------------------- #
    #  Carga y filtrado                                                  #
    # ---------------------------------------------------------------- #

    def _cargar(self, seleccionar_id=None):
        self._todos = _obtener_todos()
        self._renderizar(self._todos, seleccionar_id)

    def _filtrar(self):
        texto = self._var_busqueda.get().strip().lower()
        if not texto:
            self._renderizar(self._todos, None)
        else:
            filtrados = [p for p in self._todos
                         if texto in p["nombre"].lower()
                         or texto in p["categoria"].lower()]
            self._renderizar(filtrados, None)

    def _renderizar(self, items, seleccionar_id):
        for w in self._lista.winfo_children():
            w.destroy()

        if not items:
            etiqueta_suave(self._lista, "Sin resultados").pack(pady=16)
            return

        grupos = {}
        for p in items:
            cat = p["categoria"] or "Sin categoría"
            grupos.setdefault(cat, []).append(p)

        for cat in sorted(grupos.keys()):
            ctk.CTkLabel(
                self._lista,
                text=cat.upper(),
                font=FUENTES["small"],
                text_color=COLORES["rosa"],
                anchor="w",
            ).pack(fill="x", padx=10, pady=(10, 2))
            ctk.CTkFrame(
                self._lista, height=1, fg_color=COLORES["rosa_suave"]
            ).pack(fill="x", padx=10, pady=(0, 4))

            for p in grupos[cat]:
                sel = (seleccionar_id is not None and p["id"] == seleccionar_id)
                _ItemPrecio(
                    self._lista, item=p, seleccionado=sel,
                    al_seleccionar=self._item_seleccionado,
                ).pack(fill="x", padx=4, pady=2)

    # ---------------------------------------------------------------- #
    #  Seleccion / nuevo                                                 #
    # ---------------------------------------------------------------- #

    def _nuevo(self):
        self._seleccionado = None
        self._mostrar_form(None)

    def _item_seleccionado(self, item):
        self._seleccionado = item
        self._mostrar_form(item)

    def _mostrar_vacio(self):
        for w in self._panel_form.winfo_children():
            w.destroy()
        etiqueta_suave(
            self._panel_form,
            "Selecciona un precio o crea uno nuevo",
        ).place(relx=0.5, rely=0.5, anchor="center")

    # ---------------------------------------------------------------- #
    #  Formulario                                                        #
    # ---------------------------------------------------------------- #

    def _mostrar_form(self, precio):
        for w in self._panel_form.winfo_children():
            w.destroy()
        es_edicion = precio is not None

        etiqueta(
            self._panel_form,
            "Editar precio" if es_edicion else "Nuevo precio",
            fuente="subtitulo",
        ).pack(anchor="w", padx=20, pady=(18, 0))
        separador(self._panel_form).pack(fill="x", padx=20, pady=12)

        form = ctk.CTkFrame(self._panel_form, fg_color="transparent")
        form.pack(fill="x", padx=20)
        form.columnconfigure(1, weight=1)

        cats_existentes = _obtener_categorias()
        etiqueta_suave(form, "Categoría").grid(row=0, column=0, sticky="w", pady=8)
        e_cat = _CampoConSugerencias(form, sugerencias=cats_existentes,
                                     placeholder="Ej: PILETA, CLARITOS…")
        e_cat.grid(row=0, column=1, sticky="ew", padx=(12, 0), pady=8)

        etiqueta_suave(form, "Nombre *").grid(row=1, column=0, sticky="w", pady=8)
        e_nombre = campo_texto(form, ancho=0)
        e_nombre.grid(row=1, column=1, sticky="ew", padx=(12, 0), pady=8)

        etiqueta_suave(form, "Precio ($) *").grid(row=2, column=0, sticky="w", pady=8)
        e_precio = campo_texto(form, placeholder="0", ancho=0)
        e_precio.grid(row=2, column=1, sticky="ew", padx=(12, 0), pady=8)

        etiqueta_suave(form, "Descuento (%)").grid(row=3, column=0, sticky="w", pady=8)
        fila_desc = ctk.CTkFrame(form, fg_color="transparent")
        fila_desc.grid(row=3, column=1, sticky="ew", padx=(12, 0), pady=8)
        fila_desc.columnconfigure(0, weight=1)
        e_desc = campo_texto(fila_desc, placeholder="0", ancho=0)
        e_desc.grid(row=0, column=0, sticky="ew")
        lbl_final = ctk.CTkLabel(
            fila_desc, text="", font=FUENTES["small"],
            text_color=COLORES["exito"], anchor="w",
        )
        lbl_final.grid(row=1, column=0, sticky="w", pady=(2, 0))

        def _actualizar_preview(*_):
            try:
                p = float(e_precio.get().strip() or 0)
                d = float(e_desc.get().strip() or 0)
                if d > 0:
                    lbl_final.configure(text=f"-> Precio final: ${p * (1 - d / 100):,.0f}")
                else:
                    lbl_final.configure(text="")
            except ValueError:
                lbl_final.configure(text="")

        e_precio.bind("<KeyRelease>", _actualizar_preview)
        e_desc.bind("<KeyRelease>",   _actualizar_preview)

        var_destacado = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            form, text="Destacar (aparece primero en su categoria)",
            variable=var_destacado,
            fg_color=COLORES["rosa"], hover_color=COLORES["rosa_hover"],
            font=FUENTES["normal"], text_color=COLORES["texto"],
        ).grid(row=4, column=1, sticky="w", padx=(12, 0), pady=8)

        var_activo = ctk.BooleanVar(value=True)
        if es_edicion:
            ctk.CTkCheckBox(
                form, text="Activo",
                variable=var_activo,
                fg_color=COLORES["rosa"], hover_color=COLORES["rosa_hover"],
                font=FUENTES["normal"], text_color=COLORES["texto"],
            ).grid(row=5, column=1, sticky="w", padx=(12, 0), pady=8)

            e_cat.insert(0, precio["categoria"] or "")
            e_nombre.insert(0, precio["nombre"] or "")
            e_precio.insert(0, str(precio["precio"]))
            e_desc.insert(0, str(int(precio["descuento"])) if precio["descuento"] else "")
            var_destacado.set(bool(precio["destacado"]))
            var_activo.set(bool(precio["activo"]))
            _actualizar_preview()

        separador(self._panel_form).pack(fill="x", padx=20, pady=12)
        btns = ctk.CTkFrame(self._panel_form, fg_color="transparent")
        btns.pack(fill="x", padx=20)

        if es_edicion:
            boton_peligro(
                btns, "Eliminar",
                comando=lambda: self._eliminar_precio(precio),
                ancho=100,
            ).pack(side="left")

        def guardar():
            nombre = e_nombre.get().strip()
            if not nombre:
                mostrar_error("Error", "El nombre no puede estar vacio.")
                return
            try:
                p = float(e_precio.get().strip() or 0)
                d = float(e_desc.get().strip() or 0)
            except ValueError:
                mostrar_error("Error", "Precio y descuento deben ser numeros.")
                return
            if p < 0:
                mostrar_error("Error", "El precio no puede ser negativo.")
                return
            if not (0 <= d <= 100):
                mostrar_error("Error", "El descuento debe estar entre 0 y 100.")
                return

            categoria = e_cat.get().strip()
            if es_edicion:
                _actualizar(precio["id"], nombre, categoria, p, d,
                             var_destacado.get(), var_activo.get())
                sid = precio["id"]
                mostrar_exito("Listo", "Precio actualizado correctamente.")
            else:
                sid = _crear(nombre, categoria, p, d, var_destacado.get())
                mostrar_exito("Listo", "Precio creado correctamente.")

            self._cargar(seleccionar_id=sid)
            self._mostrar_vacio()

        boton_primario(btns, "Guardar", comando=guardar, ancho=140).pack(side="right")
        boton_secundario(btns, "Cancelar",
                         comando=self._mostrar_vacio, ancho=110).pack(side="right", padx=(0, 8))

    def _eliminar_precio(self, precio):
        if confirmar("Eliminar precio", "Eliminar '" + precio["nombre"] + "'?"):
            try:
                _eliminar(precio["id"])
                self._cargar()
                self._mostrar_vacio()
            except Exception as e:
                mostrar_error("Error", str(e))

    def refrescar(self):
        self._cargar()


# ------------------------------------------------------------------ #
#  Item de la lista                                                    #
# ------------------------------------------------------------------ #

class _ItemPrecio(ctk.CTkFrame):

    def __init__(self, parent, item, seleccionado, al_seleccionar):
        bg = COLORES["rosa_suave"] if seleccionado else "transparent"
        super().__init__(parent, fg_color=bg, corner_radius=8, cursor="hand2")
        self.item = item
        self._cb = al_seleccionar
        self.columnconfigure(1, weight=1)

        if item["destacado"]:
            dot_color, dot_text = COLORES["dorado"], "DEST"
        elif item["activo"]:
            dot_color, dot_text = COLORES["rosa"], "●"
        else:
            dot_color, dot_text = COLORES["borde"], "●"

        ctk.CTkLabel(
            self, text=dot_text, font=FUENTES["small"],
            text_color=dot_color, width=24,
        ).grid(row=0, column=0, rowspan=2, padx=(8, 0), pady=8)

        nombre_color = COLORES["rosa"] if seleccionado else COLORES["texto"]
        ctk.CTkLabel(
            self, text=item["nombre"],
            font=FUENTES["normal"], text_color=nombre_color, anchor="w",
        ).grid(row=0, column=1, sticky="w", padx=8, pady=(8, 1))

        precio = item["precio"]
        desc   = item["descuento"]
        if desc and desc > 0:
            linea2 = "$" + str(int(precio)) + "  ->  $" + str(int(precio * (1 - desc / 100))) + "  (-" + str(int(desc)) + "%)"
            color2 = COLORES["exito"]
        else:
            linea2 = "$" + str(int(precio))
            color2 = COLORES["texto_suave"]

        ctk.CTkLabel(
            self, text=linea2,
            font=FUENTES["small"], text_color=color2, anchor="w",
        ).grid(row=1, column=1, sticky="w", padx=8, pady=(1, 8))

        for w in self.winfo_children():
            w.bind("<Button-1>", lambda _e: self._cb(self.item))
        self.bind("<Button-1>", lambda _e: self._cb(self.item))