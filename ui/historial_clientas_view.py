from datetime import date
import customtkinter as ctk
from ui.vista_base import VistaBase
from ui.tema import COLORES, FUENTES
from ui.widgets import (
    boton_primario, boton_secundario, boton_peligro,
    campo_texto, etiqueta, etiqueta_suave, card,
    separador, selector, mostrar_error, mostrar_exito, confirmar,
)
from services.cliente_service import ClienteService
from services.historial_service import HistorialService, TIPOS


class HistorialClientasView(VistaBase):

    def __init__(self, parent, **kwargs):
        self._clientes_service  = ClienteService()
        self._historial_service = HistorialService()
        self._cliente_seleccionado = None
        super().__init__(parent, titulo="Historial Clientas", **kwargs)

    def _construir_contenido(self):
        self.contenido = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.contenido.pack(fill="both", expand=True, padx=24, pady=16)
        self.contenido.columnconfigure(0, weight=2)
        self.contenido.columnconfigure(1, weight=3)
        self.contenido.rowconfigure(0, weight=1)

        self._construir_panel_lista()
        self._construir_panel_detalle()
        self._cargar_clientes()

    # ---------------------------------------------------------------- #
    #  Panel izquierdo — lista de clientas                               #
    # ---------------------------------------------------------------- #

    def _construir_panel_lista(self):
        panel = card(self.contenido)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        panel.rowconfigure(2, weight=1)
        panel.columnconfigure(0, weight=1)

        busq = ctk.CTkFrame(panel, fg_color="transparent")
        busq.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        busq.columnconfigure(0, weight=1)

        self._var_busqueda = ctk.StringVar()
        self._var_busqueda.trace_add("write", lambda *_: self._filtrar())

        campo_busqueda = campo_texto(
            busq, placeholder="Buscar por nombre o teléfono...", ancho=0
        )
        campo_busqueda.configure(textvariable=self._var_busqueda)
        campo_busqueda.grid(row=0, column=0, sticky="ew")

        separador(panel).grid(row=1, column=0, sticky="ew", padx=12)

        self._lista_frame = ctk.CTkScrollableFrame(
            panel,
            fg_color="transparent",
            scrollbar_button_color=COLORES["rosa"],
            scrollbar_button_hover_color=COLORES["rosa_hover"],
        )
        self._lista_frame.grid(row=2, column=0, sticky="nsew", padx=6, pady=6)
        self._lista_frame.columnconfigure(0, weight=1)
        self._items_lista = []

    def _cargar_clientes(self, seleccionar_id=None):
        self._clientes = self._clientes_service.obtener_todos()
        self._renderizar_lista(self._clientes, seleccionar_id)

    def _filtrar(self):
        texto = self._var_busqueda.get().strip()
        resultados = self._clientes_service.buscar(texto) if texto else self._clientes
        self._renderizar_lista(resultados)

    def _renderizar_lista(self, clientes, seleccionar_id=None):
        for w in self._lista_frame.winfo_children():
            w.destroy()
        self._items_lista.clear()

        if not clientes:
            etiqueta_suave(self._lista_frame, "Sin resultados").pack(pady=20)
            return

        for c in clientes:
            item = _ItemClienteHistorial(
                self._lista_frame,
                cliente=c,
                seleccionado=(c["id"] == seleccionar_id),
                al_seleccionar=self._al_seleccionar,
            )
            item.pack(fill="x", padx=4, pady=2)
            self._items_lista.append(item)

    def _al_seleccionar(self, cliente):
        self._cliente_seleccionado = cliente
        for item in self._items_lista:
            item.set_activo(item.cliente["id"] == cliente["id"])
        self._mostrar_detalle(cliente)

    # ---------------------------------------------------------------- #
    #  Panel derecho — nombre + historial de la clienta                  #
    # ---------------------------------------------------------------- #

    def _construir_panel_detalle(self):
        self._panel_detalle = card(self.contenido)
        self._panel_detalle.grid(row=0, column=1, sticky="nsew")
        self._panel_detalle.columnconfigure(0, weight=1)
        self._panel_detalle.rowconfigure(0, weight=1)
        self._mostrar_detalle_vacio()

    def _mostrar_detalle_vacio(self):
        for w in self._panel_detalle.winfo_children():
            w.destroy()
        etiqueta_suave(
            self._panel_detalle,
            "Seleccioná una clienta para ver su historial"
        ).place(relx=0.5, rely=0.5, anchor="center")

    def _mostrar_detalle(self, cliente):
        for w in self._panel_detalle.winfo_children():
            w.destroy()

        cab = ctk.CTkFrame(self._panel_detalle, fg_color="transparent")
        cab.pack(fill="x", padx=20, pady=(18, 0))

        etiqueta(cab, cliente["nombre"], fuente="subtitulo").pack(side="left")
        boton_primario(cab, "＋  Nuevo item",
                       comando=lambda: self._mostrar_form(cliente),
                       ancho=140).pack(side="right")

        separador(self._panel_detalle).pack(fill="x", padx=20, pady=12)

        items_scroll = ctk.CTkScrollableFrame(
            self._panel_detalle, fg_color="transparent",
            scrollbar_button_color=COLORES["rosa"],
            scrollbar_button_hover_color=COLORES["rosa_hover"],
        )
        items_scroll.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        items_scroll.columnconfigure(0, weight=1)

        historial = self._historial_service.obtener_por_cliente(cliente["id"])
        if not historial:
            etiqueta_suave(items_scroll, "Sin items registrados").pack(pady=10)
        else:
            grupos = {}
            orden_fechas = []
            for h in historial:
                if h["fecha"] not in grupos:
                    grupos[h["fecha"]] = []
                    orden_fechas.append(h["fecha"])
                grupos[h["fecha"]].append(h)

            for fecha in orden_fechas:
                _GrupoFechaHistorial(
                    items_scroll, fecha=fecha, items=grupos[fecha],
                    al_editar=lambda h: self._mostrar_form(cliente, h),
                ).pack(fill="x", pady=4)

    # ---------------------------------------------------------------- #
    #  Formulario de item de historial                                   #
    # ---------------------------------------------------------------- #

    def _mostrar_form(self, cliente, item=None):
        for w in self._panel_detalle.winfo_children():
            w.destroy()
        es_edicion = item is not None

        etiqueta(
            self._panel_detalle,
            cliente["nombre"] + "  —  " + ("Editar item" if es_edicion else "Nuevo item"),
            fuente="subtitulo",
        ).pack(anchor="w", padx=20, pady=(18, 0))
        separador(self._panel_detalle).pack(fill="x", padx=20, pady=12)

        if es_edicion:
            self._construir_form_edicion(cliente, item)
        else:
            self._construir_form_multiple(cliente)

    def _construir_form_edicion(self, cliente, item):
        """Un solo tipo + descripción — para corregir un item ya creado."""
        form = ctk.CTkFrame(self._panel_detalle, fg_color="transparent")
        form.pack(fill="x", padx=20)
        form.columnconfigure(1, weight=1)

        etiqueta_suave(form, "Fecha (AAAA-MM-DD) *").grid(row=0, column=0, sticky="w", pady=8)
        e_fecha = campo_texto(form, ancho=0)
        e_fecha.grid(row=0, column=1, sticky="ew", padx=(12, 0), pady=8)

        etiqueta_suave(form, "Tipo *").grid(row=1, column=0, sticky="w", pady=8)
        sel_tipo, var_tipo = selector(form, valores=TIPOS, ancho=0)
        sel_tipo.grid(row=1, column=1, sticky="ew", padx=(12, 0), pady=8)

        etiqueta_suave(form, "Descripción *").grid(row=2, column=0, sticky="nw", pady=8)
        e_desc = ctk.CTkTextbox(
            form, height=90,
            fg_color=COLORES["fondo_input"],
            border_color=COLORES["borde"],
            border_width=2,
            text_color=COLORES["texto"],
            font=FUENTES["normal"],
            corner_radius=8,
        )
        e_desc.grid(row=2, column=1, sticky="ew", padx=(12, 0), pady=8)

        e_fecha.insert(0, item["fecha"])
        var_tipo.set(item["tipo"])
        e_desc.insert("1.0", item["descripcion"] or "")

        separador(self._panel_detalle).pack(fill="x", padx=20, pady=12)
        btns = ctk.CTkFrame(self._panel_detalle, fg_color="transparent")
        btns.pack(fill="x", padx=20)

        boton_peligro(
            btns, "Eliminar",
            comando=lambda: self._eliminar_item(cliente, item),
            ancho=100,
        ).pack(side="left")

        def guardar():
            fecha = e_fecha.get().strip()
            tipo = var_tipo.get()
            descripcion = e_desc.get("1.0", "end").strip()
            ok, msg = self._historial_service.actualizar(item["id"], tipo, descripcion, fecha)
            if not ok:
                mostrar_error("Error", msg)
                return
            mostrar_exito("Listo", msg)
            self._mostrar_detalle(cliente)

        boton_primario(btns, "Guardar", comando=guardar, ancho=140).pack(side="right")
        boton_secundario(btns, "Cancelar",
                         comando=lambda: self._mostrar_detalle(cliente),
                         ancho=110).pack(side="right", padx=(0, 8))

    def _construir_form_multiple(self, cliente):
        """Varios tipos a la vez (ej: Color + Corte + Progresivo el mismo día),
        cada uno con su propia descripción, bajo una única fecha elegible."""
        fila_fecha = ctk.CTkFrame(self._panel_detalle, fg_color="transparent")
        fila_fecha.pack(fill="x", padx=20, pady=(0, 8))
        etiqueta_suave(fila_fecha, "Fecha (AAAA-MM-DD) *").pack(side="left")
        e_fecha = campo_texto(fila_fecha, ancho=150)
        e_fecha.insert(0, date.today().strftime("%Y-%m-%d"))
        e_fecha.pack(side="left", padx=(12, 0))

        etiqueta_suave(
            self._panel_detalle,
            "Tildá los items de esa fecha y escribí una descripción para cada uno.",
        ).pack(anchor="w", padx=20, pady=(0, 8))

        lista = ctk.CTkScrollableFrame(
            self._panel_detalle, fg_color="transparent",
            scrollbar_button_color=COLORES["rosa"],
            scrollbar_button_hover_color=COLORES["rosa_hover"],
        )
        lista.pack(fill="both", expand=True, padx=14)
        lista.columnconfigure(0, weight=1)

        campos = {}  # tipo -> (var_check, textbox)
        for tipo in TIPOS:
            fila = ctk.CTkFrame(lista, fg_color="transparent")
            fila.pack(fill="x", padx=6, pady=(6, 2))
            fila.columnconfigure(0, weight=1)

            var_check = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(
                fila, text=tipo, variable=var_check,
                fg_color=COLORES["rosa"], hover_color=COLORES["rosa_hover"],
                font=FUENTES["normal"], text_color=COLORES["texto"],
            ).grid(row=0, column=0, sticky="w")

            e_desc = ctk.CTkTextbox(
                fila, height=50,
                fg_color=COLORES["fondo_input"],
                border_color=COLORES["borde"],
                border_width=2,
                text_color=COLORES["texto"],
                font=FUENTES["normal"],
                corner_radius=8,
            )
            e_desc.grid(row=1, column=0, sticky="ew", pady=(4, 0))
            campos[tipo] = (var_check, e_desc)

        separador(self._panel_detalle).pack(fill="x", padx=20, pady=12)
        btns = ctk.CTkFrame(self._panel_detalle, fg_color="transparent")
        btns.pack(fill="x", padx=20)

        def guardar():
            fecha = e_fecha.get().strip()
            tipos_marcados = [t for t, (var_check, _) in campos.items() if var_check.get()]
            if not tipos_marcados:
                mostrar_error("Error", "Tildá al menos un tipo.")
                return
            for tipo in tipos_marcados:
                _, e_desc = campos[tipo]
                descripcion = e_desc.get("1.0", "end").strip()
                if not descripcion:
                    mostrar_error("Error", f"Completá la descripción de {tipo}.")
                    return
            for tipo in tipos_marcados:
                _, e_desc = campos[tipo]
                descripcion = e_desc.get("1.0", "end").strip()
                ok, msg, _id = self._historial_service.crear(cliente["id"], tipo, descripcion, fecha)
                if not ok:
                    mostrar_error("Error", msg)
                    return
            plural = "s" if len(tipos_marcados) > 1 else ""
            mostrar_exito("Listo", f"Se agregó{plural} {len(tipos_marcados)} item{plural} al historial.")
            self._mostrar_detalle(cliente)

        boton_primario(btns, "Guardar", comando=guardar, ancho=140).pack(side="right")
        boton_secundario(btns, "Cancelar",
                         comando=lambda: self._mostrar_detalle(cliente),
                         ancho=110).pack(side="right", padx=(0, 8))

    def _eliminar_item(self, cliente, item):
        if confirmar("Eliminar item", "¿Eliminar este item del historial?"):
            self._historial_service.eliminar(item["id"])
            self._mostrar_detalle(cliente)

    def refrescar(self):
        self._cargar_clientes()


# ------------------------------------------------------------------ #
#  Items de lista                                                      #
# ------------------------------------------------------------------ #

class _ItemClienteHistorial(ctk.CTkFrame):

    def __init__(self, parent, cliente, seleccionado, al_seleccionar):
        super().__init__(
            parent,
            fg_color=COLORES["rosa_suave"] if seleccionado else "transparent",
            corner_radius=8,
            cursor="hand2",
        )
        self.cliente = cliente
        self._al_seleccionar = al_seleccionar
        self.columnconfigure(0, weight=1)

        lbl_nombre = ctk.CTkLabel(
            self, text=cliente["nombre"],
            font=FUENTES["normal"],
            text_color=COLORES["rosa"] if seleccionado else COLORES["texto"],
            anchor="w",
        )
        lbl_nombre.grid(row=0, column=0, sticky="w", padx=12, pady=(8, 2))

        lbl_tel = ctk.CTkLabel(
            self, text=cliente["telefono"] or "Sin teléfono",
            font=FUENTES["small"],
            text_color=COLORES["texto_suave"],
            anchor="w",
        )
        lbl_tel.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 8))

        for w in [self, lbl_nombre, lbl_tel]:
            w.bind("<Button-1>", lambda _e: self._al_seleccionar(self.cliente))

    def set_activo(self, activo):
        self.configure(fg_color=COLORES["rosa_suave"] if activo else "transparent")
        for w in self.winfo_children():
            if isinstance(w, ctk.CTkLabel):
                es_nombre = w.cget("font") == FUENTES["normal"]
                w.configure(text_color=COLORES["rosa"] if (activo and es_nombre)
                            else COLORES["texto_suave"] if not es_nombre
                            else COLORES["texto"])


def _formatear_fecha(fecha_iso: str) -> str:
    """'2026-08-26' -> '26/08/2026'."""
    partes = fecha_iso.split("-")
    if len(partes) == 3:
        return partes[2] + "/" + partes[1] + "/" + partes[0]
    return fecha_iso


class _GrupoFechaHistorial(ctk.CTkFrame):
    """Todos los items de una misma fecha, agrupados bajo un solo encabezado
    para que un día con varios servicios no ocupe una tarjeta grande por item."""

    def __init__(self, parent, fecha, items, al_editar):
        super().__init__(
            parent, fg_color=COLORES["fondo_card"], corner_radius=8,
            border_width=1, border_color=COLORES["borde"],
        )
        self.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text=_formatear_fecha(fecha),
            font=FUENTES["small"], text_color=COLORES["rosa"], anchor="w",
        ).pack(fill="x", padx=12, pady=(8, 2))

        separador(self).pack(fill="x", padx=12, pady=(0, 4))

        for i, item in enumerate(items):
            fila = ctk.CTkFrame(self, fg_color="transparent", cursor="hand2")
            fila.pack(fill="x", padx=12, pady=(0, 8 if i == len(items) - 1 else 3))
            fila.columnconfigure(1, weight=1)

            ctk.CTkLabel(
                fila, text=item["tipo"], font=FUENTES["small"],
                text_color=COLORES["rosa"], anchor="w", width=90,
            ).grid(row=0, column=0, sticky="w")

            lbl_desc = ctk.CTkLabel(
                fila, text=item["descripcion"], font=FUENTES["normal"],
                text_color=COLORES["texto"], anchor="w", justify="left",
                wraplength=280,
            )
            lbl_desc.grid(row=0, column=1, sticky="ew", padx=(8, 0))

            for w in (fila, lbl_desc):
                w.bind("<Button-1>", lambda _e, h=item: al_editar(h))
