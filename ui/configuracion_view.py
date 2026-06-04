import customtkinter as ctk
from db.database import get_connection
from ui.vista_base import VistaBase
from ui.tema import COLORES, FUENTES
from ui.widgets import (
    boton_primario, boton_secundario, boton_peligro,
    campo_texto, etiqueta, etiqueta_suave, card,
    separador, mostrar_error, mostrar_exito, confirmar
)
from services.configuracion_service import ConfiguracionService


class ConfiguracionView(VistaBase):

    def __init__(self, parent, **kwargs):
        self._service = ConfiguracionService()
        super().__init__(parent, titulo="Configuracion", **kwargs)

    def _construir_contenido(self):
        self.contenido = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.contenido.pack(fill="both", expand=True, padx=24, pady=16)
        self.contenido.rowconfigure(1, weight=1)
        self.contenido.columnconfigure(0, weight=1)
        self._tab_activa = None
        self._panel_activo = None
        self._construir_tabs()

    def _construir_tabs(self):
        self._tab_bar = ctk.CTkFrame(self.contenido, fg_color="transparent", height=44)
        self._tab_bar.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        self._tabs = {}
        tabs_def = [
            ("servicios",    "Servicios"),
            ("empleadas",    "Empleadas"),
            ("metodos_pago", "Metodos de pago"),
        ]
        for clave, lbl in tabs_def:
            btn = ctk.CTkButton(
                self._tab_bar, text=lbl, width=160, height=38,
                fg_color="transparent", hover_color=COLORES["rosa_suave"],
                text_color=COLORES["texto_suave"], font=FUENTES["normal"],
                corner_radius=8, border_width=1, border_color=COLORES["borde"],
                command=lambda c=clave: self._activar_tab(c),
            )
            btn.pack(side="left", padx=(0, 6))
            self._tabs[clave] = btn

        self._area_tab = ctk.CTkFrame(self.contenido, fg_color="transparent", corner_radius=0)
        self._area_tab.grid(row=1, column=0, sticky="nsew")
        self._area_tab.rowconfigure(0, weight=1)
        self._area_tab.columnconfigure(0, weight=1)
        self._activar_tab("servicios")

    def _activar_tab(self, clave):
        for k, btn in self._tabs.items():
            if k == clave:
                btn.configure(fg_color=COLORES["rosa"], text_color=COLORES["texto_blanco"],
                              border_color=COLORES["rosa"], font=FUENTES["subtitulo"])
            else:
                btn.configure(fg_color="transparent", text_color=COLORES["texto_suave"],
                              border_color=COLORES["borde"], font=FUENTES["normal"])

        if self._panel_activo:
            self._panel_activo.destroy()

        if clave == "servicios":
            self._panel_activo = _PanelServicios(self._area_tab, self._service)
        elif clave == "empleadas":
            self._panel_activo = _PanelEmpleadas(self._area_tab, self._service)
        elif clave == "metodos_pago":
            self._panel_activo = _PanelMetodosPago(self._area_tab, self._service)

        if self._panel_activo:
            self._panel_activo.grid(row=0, column=0, sticky="nsew")
        self._tab_activa = clave

    def refrescar(self):
        if self._tab_activa:
            self._activar_tab(self._tab_activa)


# ------------------------------------------------------------------ #
#  Panel base                                                          #
# ------------------------------------------------------------------ #

class _PanelBase(ctk.CTkFrame):

    TITULO_NUEVO = "Nuevo"

    def __init__(self, parent, service):
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self._service = service
        self._seleccionado = None
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)
        self._construir()
        self._cargar()

    def _construir(self):
        panel_lista = card(self)
        panel_lista.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        panel_lista.rowconfigure(1, weight=1)
        panel_lista.columnconfigure(0, weight=1)

        cab = ctk.CTkFrame(panel_lista, fg_color="transparent")
        cab.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        cab.columnconfigure(0, weight=1)
        boton_primario(cab, "  " + self.TITULO_NUEVO,
                       comando=self._nuevo, ancho=0).grid(row=0, column=0, sticky="ew")

        self._lista = ctk.CTkScrollableFrame(
            panel_lista, fg_color="transparent",
            scrollbar_button_color=COLORES["rosa"],
            scrollbar_button_hover_color=COLORES["rosa_hover"],
        )
        self._lista.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))
        self._lista.columnconfigure(0, weight=1)

        self._panel_form = card(self)
        self._panel_form.grid(row=0, column=1, sticky="nsew")
        self._panel_form.columnconfigure(0, weight=1)
        self._mostrar_vacio()

    def _cargar(self, seleccionar_id=None):
        raise NotImplementedError

    def _nuevo(self):
        self._seleccionado = None
        self._mostrar_form(None)

    def _mostrar_vacio(self):
        for w in self._panel_form.winfo_children():
            w.destroy()
        etiqueta_suave(self._panel_form,
                       "Selecciona un item o crea uno nuevo"
                       ).place(relx=0.5, rely=0.5, anchor="center")

    def _mostrar_form(self, item):
        raise NotImplementedError

    def _item_seleccionado(self, item):
        self._seleccionado = item
        self._mostrar_form(item)

    def _eliminar_db(self, tabla, id_val):
        conn = get_connection()
        conn.execute("DELETE FROM " + tabla + " WHERE id = ?", (id_val,))
        conn.commit()
        conn.close()


# ------------------------------------------------------------------ #
#  Widget campo con sugerencias (autocompletado simple)               #
# ------------------------------------------------------------------ #

class _CampoConSugerencias(ctk.CTkFrame):

    def __init__(self, parent, sugerencias: list[str], placeholder="", **kwargs):
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

    def get(self) -> str:
        return self._var.get()

    def insert(self, index, valor: str):
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

    def _mostrar_popup(self, opciones: list[str]):
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
            btn = ctk.CTkButton(
                self._popup, text=op, anchor="w", height=34,
                fg_color="transparent", hover_color=COLORES["rosa_suave"],
                text_color=COLORES["texto"], font=FUENTES["normal"],
                corner_radius=0,
                command=lambda v=op: self._seleccionar(v),
            )
            btn.pack(fill="x")

    def _seleccionar(self, valor: str):
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
#  Panel Servicios — con categorias colapsables                        #
# ------------------------------------------------------------------ #

class _PanelServicios(_PanelBase):

    TITULO_NUEVO = "Nuevo servicio"

    def __init__(self, parent, service):
        self._colapsado = {}
        super().__init__(parent, service)

    def _cargar(self, seleccionar_id=None):
        for w in self._lista.winfo_children():
            w.destroy()
        servicios = self._service.obtener_servicios()
        if not servicios:
            etiqueta_suave(self._lista, "Sin servicios").pack(pady=12)
            return

        # Agrupar por categoria
        grupos: dict[str, list] = {}
        for s in servicios:
            cat = s["categoria"] or "Sin categoría"
            grupos.setdefault(cat, []).append(s)

        for cat, items in sorted(grupos.items()):
            colapsado = self._colapsado.get(cat, False)

            # Encabezado clickeable
            enc_frame = ctk.CTkFrame(self._lista, fg_color="transparent", cursor="hand2")
            enc_frame.pack(fill="x", padx=10, pady=(10, 2))
            enc_frame.columnconfigure(0, weight=1)

            flecha = "▶" if colapsado else "▼"
            lbl_cat = ctk.CTkLabel(
                enc_frame,
                text=flecha + "  " + cat.upper(),
                font=FUENTES["small"],
                text_color=COLORES["rosa"],
                anchor="w",
                cursor="hand2",
            )
            lbl_cat.grid(row=0, column=0, sticky="ew")

            ctk.CTkFrame(
                self._lista, height=1, fg_color=COLORES["rosa_suave"]
            ).pack(fill="x", padx=10, pady=(0, 4))

            items_frame = ctk.CTkFrame(self._lista, fg_color="transparent")
            items_frame.columnconfigure(0, weight=1)

            if not colapsado:
                items_frame.pack(fill="x")

            for s in items:
                _ItemToggle(
                    items_frame, item=s,
                    linea1=s["nombre"],
                    linea2="$" + str(int(s["precio"])) + "  -  " + str(s["duracion_min"]) + " min",
                    activo=bool(s["activo"]),
                    seleccionado=(seleccionar_id is not None and s["id"] == seleccionar_id),
                    al_seleccionar=self._item_seleccionado,
                ).pack(fill="x", padx=4, pady=2)

            def _toggle(c=cat):
                self._colapsado[c] = not self._colapsado.get(c, False)
                self._cargar(seleccionar_id=self._seleccionado["id"] if self._seleccionado else None)

            enc_frame.bind("<Button-1>", lambda _e, t=_toggle: t())
            lbl_cat.bind("<Button-1>", lambda _e, t=_toggle: t())

    def _mostrar_form(self, servicio):
        for w in self._panel_form.winfo_children():
            w.destroy()
        es_edicion = servicio is not None

        etiqueta(self._panel_form,
                 "Editar servicio" if es_edicion else "Nuevo servicio",
                 fuente="subtitulo").pack(anchor="w", padx=20, pady=(18, 0))
        separador(self._panel_form).pack(fill="x", padx=20, pady=12)

        form = ctk.CTkFrame(self._panel_form, fg_color="transparent")
        form.pack(fill="x", padx=20)
        form.columnconfigure(1, weight=1)

        cats_existentes = self._service.obtener_categorias_servicios()
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

        etiqueta_suave(form, "Duracion (min)").grid(row=3, column=0, sticky="w", pady=8)
        e_dur = campo_texto(form, placeholder="60", ancho=0)
        e_dur.grid(row=3, column=1, sticky="ew", padx=(12, 0), pady=8)

        var_activo = ctk.BooleanVar(value=True)
        if es_edicion:
            var_activo.set(bool(servicio["activo"]))
            ctk.CTkCheckBox(form, text="Activo", variable=var_activo,
                            fg_color=COLORES["rosa"], hover_color=COLORES["rosa_hover"],
                            font=FUENTES["normal"], text_color=COLORES["texto"],
                            ).grid(row=4, column=1, sticky="w", padx=(12, 0), pady=8)
            e_cat.insert(0, servicio["categoria"] or "")
            e_nombre.insert(0, servicio["nombre"] or "")
            e_precio.insert(0, str(servicio["precio"]))
            e_dur.insert(0, str(servicio["duracion_min"]))

        separador(self._panel_form).pack(fill="x", padx=20, pady=12)
        btns = ctk.CTkFrame(self._panel_form, fg_color="transparent")
        btns.pack(fill="x", padx=20)

        if es_edicion:
            boton_peligro(btns, "Eliminar",
                          comando=lambda: self._eliminar(servicio),
                          ancho=100).pack(side="left")

        def guardar():
            nombre = e_nombre.get().strip()
            categoria = e_cat.get().strip()
            try:
                precio = float(e_precio.get().strip() or 0)
                dur = int(e_dur.get().strip() or 60)
            except ValueError:
                mostrar_error("Error", "Precio y duracion deben ser numeros.")
                return
            if es_edicion:
                ok, msg = self._service.actualizar_servicio(
                    servicio["id"], nombre, categoria, precio, dur, var_activo.get())
                sid = servicio["id"]
            else:
                ok, msg, sid = self._service.crear_servicio(nombre, categoria, precio, dur)
            if not ok:
                mostrar_error("Error", msg)
                return
            mostrar_exito("Listo", msg)
            self._cargar(seleccionar_id=sid)
            self._mostrar_vacio()

        boton_primario(btns, "Guardar", comando=guardar, ancho=140).pack(side="right")
        boton_secundario(btns, "Cancelar",
                         comando=self._mostrar_vacio, ancho=110).pack(side="right", padx=(0, 8))

    def _eliminar(self, servicio):
        if confirmar("Eliminar servicio", "Eliminar " + servicio["nombre"] + "?"):
            try:
                self._eliminar_db("servicios", servicio["id"])
                self._cargar()
                self._mostrar_vacio()
            except Exception as e:
                if "FOREIGN KEY" in str(e):
                    mostrar_error("No se puede eliminar",
                                  "Tiene turnos asociados. Desactivalo en su lugar.")
                else:
                    mostrar_error("Error", str(e))


# ------------------------------------------------------------------ #
#  Panel Empleadas                                                     #
# ------------------------------------------------------------------ #

class _PanelEmpleadas(_PanelBase):

    TITULO_NUEVO = "Nueva empleada"

    def _cargar(self, seleccionar_id=None):
        for w in self._lista.winfo_children():
            w.destroy()
        empleadas = self._service.obtener_empleadas()
        if not empleadas:
            etiqueta_suave(self._lista, "Sin empleadas").pack(pady=12)
            return
        for e in empleadas:
            _ItemToggle(
                self._lista, item=e,
                linea1=e["nombre"],
                linea2=e["telefono"] or "Sin telefono",
                activo=bool(e["activa"]),
                seleccionado=(seleccionar_id is not None and e["id"] == seleccionar_id),
                al_seleccionar=self._item_seleccionado,
            ).pack(fill="x", padx=4, pady=2)

    def _mostrar_form(self, empleada):
        for w in self._panel_form.winfo_children():
            w.destroy()
        es_edicion = empleada is not None

        etiqueta(self._panel_form,
                 "Editar empleada" if es_edicion else "Nueva empleada",
                 fuente="subtitulo").pack(anchor="w", padx=20, pady=(18, 0))
        separador(self._panel_form).pack(fill="x", padx=20, pady=12)

        form = ctk.CTkFrame(self._panel_form, fg_color="transparent")
        form.pack(fill="x", padx=20)
        form.columnconfigure(1, weight=1)

        etiqueta_suave(form, "Nombre *").grid(row=0, column=0, sticky="w", pady=8)
        e_nombre = campo_texto(form, ancho=0)
        e_nombre.grid(row=0, column=1, sticky="ew", padx=(12, 0), pady=8)

        etiqueta_suave(form, "Telefono").grid(row=1, column=0, sticky="w", pady=8)
        e_tel = campo_texto(form, ancho=0)
        e_tel.grid(row=1, column=1, sticky="ew", padx=(12, 0), pady=8)

        var_activa = ctk.BooleanVar(value=True)
        if es_edicion:
            var_activa.set(bool(empleada["activa"]))
            ctk.CTkCheckBox(form, text="Activa", variable=var_activa,
                            fg_color=COLORES["rosa"], hover_color=COLORES["rosa_hover"],
                            font=FUENTES["normal"], text_color=COLORES["texto"],
                            ).grid(row=2, column=1, sticky="w", padx=(12, 0), pady=8)
            e_nombre.insert(0, empleada["nombre"] or "")
            e_tel.insert(0, empleada["telefono"] or "")

        separador(self._panel_form).pack(fill="x", padx=20, pady=12)
        btns = ctk.CTkFrame(self._panel_form, fg_color="transparent")
        btns.pack(fill="x", padx=20)

        if es_edicion:
            boton_peligro(btns, "Eliminar",
                          comando=lambda: self._eliminar(empleada),
                          ancho=100).pack(side="left")

        def guardar():
            nombre = e_nombre.get().strip()
            tel = e_tel.get().strip()
            if es_edicion:
                ok, msg = self._service.actualizar_empleada(
                    empleada["id"], nombre, tel, var_activa.get())
                eid = empleada["id"]
            else:
                ok, msg, eid = self._service.crear_empleada(nombre, tel)
            if not ok:
                mostrar_error("Error", msg)
                return
            mostrar_exito("Listo", msg)
            self._cargar(seleccionar_id=eid)
            self._mostrar_vacio()

        boton_primario(btns, "Guardar", comando=guardar, ancho=140).pack(side="right")
        boton_secundario(btns, "Cancelar",
                         comando=self._mostrar_vacio, ancho=110).pack(side="right", padx=(0, 8))

    def _eliminar(self, empleada):
        if confirmar("Eliminar empleada", "Eliminar a " + empleada["nombre"] + "?"):
            try:
                self._eliminar_db("empleadas", empleada["id"])
                self._cargar()
                self._mostrar_vacio()
            except Exception as e:
                if "FOREIGN KEY" in str(e):
                    mostrar_error("No se puede eliminar",
                                  "Tiene turnos asociados. Desactivala en su lugar.")
                else:
                    mostrar_error("Error", str(e))


# ------------------------------------------------------------------ #
#  Panel Metodos de pago                                               #
# ------------------------------------------------------------------ #

class _PanelMetodosPago(_PanelBase):

    TITULO_NUEVO = "Nuevo metodo"

    def _cargar(self, seleccionar_id=None):
        for w in self._lista.winfo_children():
            w.destroy()
        metodos = self._service.obtener_metodos_pago()
        if not metodos:
            etiqueta_suave(self._lista, "Sin metodos de pago").pack(pady=12)
            return
        for m in metodos:
            _ItemToggle(
                self._lista, item=m,
                linea1=m["nombre"],
                linea2="Activo" if m["activo"] else "Inactivo",
                activo=bool(m["activo"]),
                seleccionado=(seleccionar_id is not None and m["id"] == seleccionar_id),
                al_seleccionar=self._item_seleccionado,
            ).pack(fill="x", padx=4, pady=2)

    def _mostrar_form(self, metodo):
        for w in self._panel_form.winfo_children():
            w.destroy()
        es_edicion = metodo is not None

        etiqueta(self._panel_form,
                 "Editar metodo" if es_edicion else "Nuevo metodo de pago",
                 fuente="subtitulo").pack(anchor="w", padx=20, pady=(18, 0))
        separador(self._panel_form).pack(fill="x", padx=20, pady=12)

        form = ctk.CTkFrame(self._panel_form, fg_color="transparent")
        form.pack(fill="x", padx=20)
        form.columnconfigure(1, weight=1)

        etiqueta_suave(form, "Nombre *").grid(row=0, column=0, sticky="w", pady=8)
        e_nombre = campo_texto(form, ancho=0)
        e_nombre.grid(row=0, column=1, sticky="ew", padx=(12, 0), pady=8)

        var_activo = ctk.BooleanVar(value=True)
        if es_edicion:
            var_activo.set(bool(metodo["activo"]))
            ctk.CTkCheckBox(form, text="Activo", variable=var_activo,
                            fg_color=COLORES["rosa"], hover_color=COLORES["rosa_hover"],
                            font=FUENTES["normal"], text_color=COLORES["texto"],
                            ).grid(row=1, column=1, sticky="w", padx=(12, 0), pady=8)
            e_nombre.insert(0, metodo["nombre"] or "")

        separador(self._panel_form).pack(fill="x", padx=20, pady=12)
        btns = ctk.CTkFrame(self._panel_form, fg_color="transparent")
        btns.pack(fill="x", padx=20)

        if es_edicion:
            boton_peligro(btns, "Eliminar",
                          comando=lambda: self._eliminar(metodo),
                          ancho=100).pack(side="left")

        def guardar():
            nombre = e_nombre.get().strip()
            if es_edicion:
                ok, msg = self._service.actualizar_metodo_pago(
                    metodo["id"], nombre, var_activo.get())
                mid = metodo["id"]
            else:
                ok, msg, mid = self._service.crear_metodo_pago(nombre)
            if not ok:
                mostrar_error("Error", msg)
                return
            mostrar_exito("Listo", msg)
            self._cargar(seleccionar_id=mid)
            self._mostrar_vacio()

        boton_primario(btns, "Guardar", comando=guardar, ancho=140).pack(side="right")
        boton_secundario(btns, "Cancelar",
                         comando=self._mostrar_vacio, ancho=110).pack(side="right", padx=(0, 8))

    def _eliminar(self, metodo):
        if confirmar("Eliminar metodo", "Eliminar " + metodo["nombre"] + "?"):
            try:
                self._eliminar_db("metodos_pago", metodo["id"])
                self._cargar()
                self._mostrar_vacio()
            except Exception as e:
                if "FOREIGN KEY" in str(e):
                    mostrar_error("No se puede eliminar",
                                  "Tiene movimientos asociados. Desactivalo en su lugar.")
                else:
                    mostrar_error("Error", str(e))


# ------------------------------------------------------------------ #
#  Item con indicador activo/inactivo                                  #
# ------------------------------------------------------------------ #

class _ItemToggle(ctk.CTkFrame):

    def __init__(self, parent, item, linea1, linea2,
                 activo, seleccionado, al_seleccionar):
        super().__init__(
            parent,
            fg_color=COLORES["rosa_suave"] if seleccionado else "transparent",
            corner_radius=8, cursor="hand2",
        )
        self.item = item
        self._al_seleccionar = al_seleccionar
        self.columnconfigure(1, weight=1)

        color_dot = COLORES["rosa"] if activo else COLORES["borde"]
        dot = ctk.CTkFrame(self, width=8, height=8,
                           fg_color=color_dot, corner_radius=4)
        dot.grid(row=0, column=0, rowspan=2, padx=(10, 0), pady=8)
        dot.grid_propagate(False)

        lbl1 = ctk.CTkLabel(self, text=linea1, font=FUENTES["normal"],
                            text_color=COLORES["rosa"] if seleccionado else COLORES["texto"],
                            anchor="w")
        lbl1.grid(row=0, column=1, sticky="w", padx=10, pady=(8, 1))

        lbl2 = ctk.CTkLabel(self, text=linea2, font=FUENTES["small"],
                            text_color=COLORES["texto_suave"], anchor="w")
        lbl2.grid(row=1, column=1, sticky="w", padx=10, pady=(1, 8))

        for w in [self, dot, lbl1, lbl2]:
            w.bind("<Button-1>", lambda _e: self._al_seleccionar(self.item))