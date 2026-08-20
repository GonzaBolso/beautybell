import customtkinter as ctk
from ui.vista_base import VistaBase
from ui.tema import COLORES, FUENTES
from ui.widgets import (
    boton_primario, boton_secundario, boton_peligro,
    campo_texto, etiqueta, etiqueta_suave, card,
    separador, mostrar_error, mostrar_exito, confirmar
)
from services.cliente_service import ClienteService
from repository.turno_repo import TurnoRepo


class ClientesView(VistaBase):

    def __init__(self, parent, **kwargs):
        self._service = ClienteService()
        self._cliente_seleccionado = None
        super().__init__(parent, titulo="Clientes", **kwargs)

    def _construir_contenido(self):
        self.contenido = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.contenido.pack(fill="both", expand=True, padx=24, pady=16)

        boton_primario(
            self._acciones, "＋  Nuevo cliente",
            comando=self._abrir_form_nuevo, ancho=160
        ).pack()

        self.contenido.columnconfigure(0, weight=2)
        self.contenido.columnconfigure(1, weight=3)
        self.contenido.rowconfigure(0, weight=1)

        self._construir_panel_lista()
        self._construir_panel_detalle()
        self._cargar_clientes()

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

        self._campo_busqueda = campo_texto(
            busq, placeholder="Buscar por nombre o teléfono...", ancho=0
        )
        self._campo_busqueda.configure(textvariable=self._var_busqueda)
        self._campo_busqueda.grid(row=0, column=0, sticky="ew")

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

    def _construir_panel_detalle(self):
        self._panel_detalle = card(self.contenido)
        self._panel_detalle.grid(row=0, column=1, sticky="nsew")
        self._panel_detalle.columnconfigure(0, weight=1)
        self._panel_detalle.rowconfigure(0, weight=1)
        self._mostrar_detalle_vacio()

    def _cargar_clientes(self, seleccionar_id=None):
        self._clientes = self._service.obtener_todos()
        self._renderizar_lista(self._clientes, seleccionar_id)

    def _filtrar(self):
        texto = self._var_busqueda.get().strip()
        resultados = self._service.buscar(texto) if texto else self._clientes
        self._renderizar_lista(resultados)

    def _renderizar_lista(self, clientes, seleccionar_id=None):
        for w in self._lista_frame.winfo_children():
            w.destroy()
        self._items_lista.clear()

        if not clientes:
            etiqueta_suave(self._lista_frame, "Sin resultados").pack(pady=20)
            return

        for c in clientes:
            item = _ItemCliente(
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

    def _mostrar_detalle_vacio(self):
        for w in self._panel_detalle.winfo_children():
            w.destroy()
        etiqueta_suave(
            self._panel_detalle,
            "Seleccioná un cliente para ver el detalle"
        ).place(relx=0.5, rely=0.5, anchor="center")

    def _mostrar_detalle(self, cliente):
        for w in self._panel_detalle.winfo_children():
            w.destroy()

        cab = ctk.CTkFrame(self._panel_detalle, fg_color="transparent")
        cab.pack(fill="x", padx=20, pady=(18, 0))

        etiqueta(cab, cliente["nombre"], fuente="subtitulo").pack(side="left")
        boton_primario(cab, "✎  Editar",
                       comando=lambda: self._abrir_form_editar(cliente),
                       ancho=110).pack(side="right", padx=(6, 0))
        boton_peligro(cab, "Eliminar",
                      comando=lambda: self._eliminar(cliente),
                      ancho=90).pack(side="right")

        separador(self._panel_detalle).pack(fill="x", padx=20, pady=12)

        datos = ctk.CTkFrame(self._panel_detalle, fg_color="transparent")
        datos.pack(fill="x", padx=20)
        datos.columnconfigure(1, weight=1)

        campos = [
            ("Teléfono",  cliente["telefono"] or "—"),
            ("Email",     cliente["email"] or "—"),
            ("Desde",     cliente["fecha_registro"] or "—"),
        ]
        for i, (lbl, val) in enumerate(campos):
            etiqueta_suave(datos, lbl).grid(row=i, column=0, sticky="w", pady=4)
            etiqueta(datos, val).grid(row=i, column=1, sticky="w", padx=16, pady=4)

        if cliente["observaciones"]:
            separador(self._panel_detalle).pack(fill="x", padx=20, pady=12)
            etiqueta_suave(self._panel_detalle, "Observaciones").pack(anchor="w", padx=20)
            etiqueta(self._panel_detalle, cliente["observaciones"]).pack(
                anchor="w", padx=20, pady=(4, 0))

        separador(self._panel_detalle).pack(fill="x", padx=20, pady=12)

        # Historial de turnos
        cab_hist = ctk.CTkFrame(self._panel_detalle, fg_color="transparent")
        cab_hist.pack(fill="x", padx=20, pady=(0, 8))
        etiqueta(cab_hist, "Historial de turnos", fuente="subtitulo").pack(side="left")

        repo = TurnoRepo()
        turnos = repo._todos(
            """SELECT t.*, s.nombre AS servicio_nombre, e.nombre AS empleada_nombre
               FROM turnos t
               JOIN servicios s ON s.id = t.servicio_id
               JOIN empleadas e ON e.id = t.empleada_id
               WHERE t.cliente_id = ?
               ORDER BY t.fecha_hora DESC""",
            (cliente["id"],)
        )

        hist_scroll = ctk.CTkScrollableFrame(
            self._panel_detalle, fg_color="transparent",
            scrollbar_button_color=COLORES["rosa"],
            scrollbar_button_hover_color=COLORES["rosa_hover"],
        )
        hist_scroll.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        hist_scroll.columnconfigure(0, weight=1)

        if not turnos:
            etiqueta_suave(hist_scroll, "Sin turnos registrados").pack(pady=10)
        else:
            ESTADO_COLS = {
                "pendiente":  ("#FFF3CD", "#856404"),
                "confirmado": ("#D1ECF1", "#0C5460"),
                "completado": ("#D4EDDA", "#155724"),
                "cancelado":  ("#F8D7DA", "#721C24"),
            }
            for t in turnos:
                if not t["fecha_hora"]:
                    continue
                fila = ctk.CTkFrame(hist_scroll, fg_color=COLORES["fondo_card"],
                                    corner_radius=8, border_width=1,
                                    border_color=COLORES["borde"])
                fila.pack(fill="x", pady=2)

                colores = ESTADO_COLS.get(t["estado"], ("#F8F9FA", "#495057"))

                # Franja color
                ctk.CTkFrame(fila, width=5, fg_color=colores[1],
                             corner_radius=0).pack(side="left", fill="y")

                info = ctk.CTkFrame(fila, fg_color="transparent")
                info.pack(side="left", fill="x", expand=True, padx=10, pady=6)

                fila1 = ctk.CTkFrame(info, fg_color="transparent")
                fila1.pack(fill="x")

                fecha_hora = t["fecha_hora"]
                fecha_txt  = fecha_hora[:10] + "  " + fecha_hora[11:16]
                ctk.CTkLabel(fila1, text=fecha_txt,
                             font=FUENTES["small"],
                             text_color=COLORES["rosa"]).pack(side="left")
                ctk.CTkLabel(fila1, text=t["servicio_nombre"],
                             font=FUENTES["normal"],
                             text_color=COLORES["texto"]).pack(side="left", padx=(10, 0))

                badge = ctk.CTkLabel(
                    fila1,
                    text=" " + t["estado"].capitalize() + " ",
                    font=FUENTES["small"],
                    fg_color=colores[0],
                    text_color=colores[1],
                    corner_radius=6,
                )
                badge.pack(side="right")

                servicios_turno = repo.obtener_servicios_de_turno(t["id"])
                if servicios_turno:
                    grupos_por_empleada = {}
                    orden_empleadas = []
                    for s in servicios_turno:
                        nombre_emp = s.get("empleada_nombre") or t["empleada_nombre"]
                        if nombre_emp not in grupos_por_empleada:
                            grupos_por_empleada[nombre_emp] = []
                            orden_empleadas.append(nombre_emp)
                        grupos_por_empleada[nombre_emp].append(s["servicio_nombre"])
                    texto_emp = "  |  ".join(
                        nombre_emp + ": " + ", ".join(grupos_por_empleada[nombre_emp])
                        for nombre_emp in orden_empleadas
                    )
                else:
                    texto_emp = t["empleada_nombre"]

                ctk.CTkLabel(info, text=texto_emp,
                             font=FUENTES["small"],
                             text_color=COLORES["texto_suave"],
                             anchor="w").pack(fill="x")

                if t["notas"]:
                    ctk.CTkLabel(info, text=t["notas"],
                                 font=FUENTES["small"],
                                 text_color=COLORES["texto_suave"],
                                 anchor="w").pack(fill="x")

    def _abrir_form_nuevo(self):
        _FormCliente(self, service=self._service, al_guardar=self._al_guardar)

    def _abrir_form_editar(self, cliente):
        _FormCliente(self, service=self._service,
                     cliente=cliente, al_guardar=self._al_guardar)

    def _al_guardar(self, cliente_id):
        self._cargar_clientes(seleccionar_id=cliente_id)
        for item in self._items_lista:
            if item.cliente["id"] == cliente_id:
                self._al_seleccionar(item.cliente)
                break

    def _eliminar(self, cliente):
        if confirmar("Eliminar cliente",
                     f"¿Eliminás a {cliente['nombre']}?\nEsta acción no se puede deshacer."):
            try:
                self._service.eliminar(cliente["id"])
                self._cliente_seleccionado = None
                self._mostrar_detalle_vacio()
                self._cargar_clientes()
            except Exception as e:
                msg = str(e)
                if "FOREIGN KEY" in msg or "foreign key" in msg.lower():
                    mostrar_error(
                        "No se puede eliminar",
                        f"{cliente['nombre']} tiene turnos u otros datos asociados.\n"
                        "Primero eliminá o reasigná esos registros."
                    )
                else:
                    mostrar_error("Error al eliminar", msg)

    def refrescar(self):
        self._cargar_clientes()


class _ItemCliente(ctk.CTkFrame):

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


class _FormCliente(ctk.CTkToplevel):

    def __init__(self, parent, service, cliente=None, al_guardar=None):
        super().__init__(parent)
        self._service    = service
        self._cliente    = cliente
        self._al_guardar = al_guardar
        self._es_edicion = cliente is not None

        self.title("Editar cliente" if self._es_edicion else "Nuevo cliente")
        self.geometry("440x500")
        self.minsize(440, 500)
        self.resizable(True, True)
        self.configure(fg_color=COLORES["fondo"])
        self._construir()
        if self._es_edicion:
            self._rellenar(cliente)
        self.after(100, self._forzar_foco)

    def _forzar_foco(self):
        self.lift()
        self.grab_set()
        self.focus_force()
        self._nombre.focus()

    def _construir(self):
        pad = {"padx": 28, "pady": 6}

        # Botones ARRIBA — siempre visibles sin importar la escala
        btns = ctk.CTkFrame(self, fg_color=COLORES["fondo_card"],
                            corner_radius=0, border_width=0)
        btns.pack(fill="x", padx=0, pady=(0, 0))
        boton_secundario(btns, "Cancelar", comando=self.destroy, ancho=160).pack(
            side="left", padx=28, pady=12)
        boton_primario(btns, "✔  Guardar", comando=self._guardar, ancho=160).pack(
            side="right", padx=28, pady=12)

        separador(self).pack(fill="x")

        etiqueta(self, "Nombre *", fuente="small",
                 color=COLORES["texto_suave"]).pack(anchor="w", padx=28, pady=(16, 2))
        self._nombre = campo_texto(self, ancho=384)
        self._nombre.pack(**pad)

        etiqueta(self, "Teléfono", fuente="small",
                 color=COLORES["texto_suave"]).pack(anchor="w", padx=28, pady=(8, 2))
        self._telefono = campo_texto(self, ancho=384)
        self._telefono.pack(**pad)

        etiqueta(self, "Email", fuente="small",
                 color=COLORES["texto_suave"]).pack(anchor="w", padx=28, pady=(8, 2))
        self._email = campo_texto(self, ancho=384)
        self._email.pack(**pad)

        etiqueta(self, "Observaciones", fuente="small",
                 color=COLORES["texto_suave"]).pack(anchor="w", padx=28, pady=(8, 2))
        self._obs = ctk.CTkTextbox(
            self, width=384, height=80,
            fg_color=COLORES["fondo_input"],
            border_color=COLORES["borde"],
            border_width=2,
            text_color=COLORES["texto"],
            font=FUENTES["normal"],
            corner_radius=8,
        )
        self._obs.pack(**pad)

    def _rellenar(self, c):
        self._nombre.insert(0, c["nombre"] or "")
        self._telefono.insert(0, c["telefono"] or "")
        self._email.insert(0, c["email"] or "")
        if c["observaciones"]:
            self._obs.insert("1.0", c["observaciones"])

    def _guardar(self):
        nombre   = self._nombre.get().strip()
        telefono = self._telefono.get().strip()
        email    = self._email.get().strip()
        obs      = self._obs.get("1.0", "end").strip()

        if self._es_edicion:
            ok, msg = self._service.actualizar(
                self._cliente["id"], nombre, telefono, email, obs)
            cliente_id = self._cliente["id"]
        else:
            ok, msg, cliente_id = self._service.crear(nombre, telefono, email, obs)

        if not ok:
            mostrar_error("Error", msg)
            return

        mostrar_exito("Listo", msg)
        self.destroy()
        if self._al_guardar and cliente_id:
            self._al_guardar(cliente_id)