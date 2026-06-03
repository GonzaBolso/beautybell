import customtkinter as ctk
from datetime import date, timedelta
from ui.vista_base import VistaBase
from ui.tema import COLORES, FUENTES
from ui.widgets import (
    boton_primario, boton_secundario, boton_peligro,
    campo_texto, etiqueta, etiqueta_suave, card,
    separador, mostrar_error, mostrar_exito, confirmar
)
from services.caja_service import CajaService, CATEGORIAS_INGRESO, CATEGORIAS_EGRESO
from services.configuracion_service import ConfiguracionService
from services.excel_export import exportar_movimientos


class CajaView(VistaBase):

    def __init__(self, parent, **kwargs):
        self._service     = CajaService()
        self._cfg_service = ConfiguracionService()
        self._fecha_desde = date.today()
        self._fecha_hasta = date.today()
        super().__init__(parent, titulo="Caja", **kwargs)

    # ------------------------------------------------------------------ #
    #  Layout                                                              #
    # ------------------------------------------------------------------ #

    def _construir_contenido(self):
        self.contenido = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.contenido.pack(fill="both", expand=True, padx=24, pady=(4, 16))
        self.contenido.columnconfigure(0, weight=1)
        self.contenido.rowconfigure(3, weight=1)

        boton_secundario(
            self._acciones, "⬇  Exportar Excel Prueba",
            comando=self._exportar, ancho=160
        ).pack(side="right", padx=(8, 0))
        boton_primario(
            self._acciones, "＋  Movimiento",
            comando=self._abrir_form_nuevo, ancho=160
        ).pack(side="right")

        self._construir_filtros()
        self._construir_empleadas()
        self._construir_resumen()
        self._construir_lista()
        self._aplicar_filtro_rapido("hoy")

    # ------------------------------------------------------------------ #
    #  Filtros                                                             #
    # ------------------------------------------------------------------ #

    def _construir_filtros(self):
        panel = ctk.CTkFrame(self.contenido, fg_color="transparent")
        panel.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        # Filtros rapidos
        for texto, clave in [("Hoy", "hoy"), ("Semana", "semana"), ("Mes", "mes")]:
            btn = ctk.CTkButton(
                panel, text=texto, width=80, height=32,
                fg_color="transparent",
                hover_color=COLORES["rosa_suave"],
                text_color=COLORES["rosa"],
                border_color=COLORES["rosa"],
                border_width=1,
                font=FUENTES["normal"],
                corner_radius=8,
                command=lambda c=clave: self._aplicar_filtro_rapido(c),
            )
            btn.pack(side="left", padx=(0, 6))

        separador(panel, orientacion="vertical").pack(side="left", padx=12, fill="y")

        # Rango personalizado
        etiqueta_suave(panel, "Desde:").pack(side="left", padx=(0, 4))
        self._campo_desde = campo_texto(panel, placeholder="YYYY-MM-DD", ancho=120)
        self._campo_desde.insert(0, date.today().strftime("%Y-%m-%d"))
        self._campo_desde.pack(side="left", padx=(0, 8))

        etiqueta_suave(panel, "Hasta:").pack(side="left", padx=(0, 4))
        self._campo_hasta = campo_texto(panel, placeholder="YYYY-MM-DD", ancho=120)
        self._campo_hasta.insert(0, date.today().strftime("%Y-%m-%d"))
        self._campo_hasta.pack(side="left", padx=(0, 8))

        boton_secundario(panel, "Buscar", comando=self._aplicar_rango, ancho=80).pack(side="left")

    def _aplicar_filtro_rapido(self, clave: str):
        hoy = date.today()
        if clave == "hoy":
            self._fecha_desde = hoy
            self._fecha_hasta = hoy
        elif clave == "semana":
            self._fecha_desde = hoy - timedelta(days=hoy.weekday())
            self._fecha_hasta = hoy
        elif clave == "mes":
            self._fecha_desde = hoy.replace(day=1)
            self._fecha_hasta = hoy

        self._campo_desde.delete(0, "end")
        self._campo_desde.insert(0, self._fecha_desde.strftime("%Y-%m-%d"))
        self._campo_hasta.delete(0, "end")
        self._campo_hasta.insert(0, self._fecha_hasta.strftime("%Y-%m-%d"))
        self._cargar()

    def _aplicar_rango(self):
        try:
            self._fecha_desde = date.fromisoformat(self._campo_desde.get().strip())
            self._fecha_hasta = date.fromisoformat(self._campo_hasta.get().strip())
        except ValueError:
            mostrar_error("Error", "Formato de fecha invalido. Usar YYYY-MM-DD.")
            return
        self._cargar()

    # ------------------------------------------------------------------ #
    #  Ingresos por empleada                                               #
    # ------------------------------------------------------------------ #

    def _construir_empleadas(self):
        self._panel_empleadas = ctk.CTkFrame(self.contenido, fg_color="transparent")
        self._panel_empleadas.grid(row=1, column=0, sticky="ew", pady=(0, 6))

    def _actualizar_empleadas(self, movimientos: list):
        for w in self._panel_empleadas.winfo_children():
            w.destroy()

        # Agrupar ingresos de servicios por empleada
        from repository.turno_repo import TurnoRepo
        repo = TurnoRepo()
        por_empleada = {}

        for m in movimientos:
            if m["tipo"] == "ingreso" and m["turno_id"]:
                turno = repo.obtener_por_id(m["turno_id"])
                if turno:
                    nombre = turno["empleada_nombre"]
                    por_empleada[nombre] = por_empleada.get(nombre, 0) + m["monto"]

        if not por_empleada:
            return

        frame = ctk.CTkFrame(self._panel_empleadas, fg_color="transparent")
        frame.pack(fill="x")

        etiqueta_suave(frame, "Ingresos por empleada:").pack(side="left", padx=(0, 12))

        for nombre, total in por_empleada.items():
            pill = ctk.CTkFrame(frame, fg_color=COLORES["rosa_suave"],
                                corner_radius=8)
            pill.pack(side="left", padx=(0, 8))
            ctk.CTkLabel(
                pill,
                text=nombre + "  $" + f"{total:,.0f}",
                font=FUENTES["small"],
                text_color=COLORES["rosa"],
            ).pack(padx=12, pady=6)

    # ------------------------------------------------------------------ #
    #  Tarjetas resumen                                                    #
    # ------------------------------------------------------------------ #

    def _construir_resumen(self):
        self._panel_resumen = ctk.CTkFrame(self.contenido, fg_color="transparent")
        self._panel_resumen.grid(row=2, column=0, sticky="ew", pady=(0, 6))
        for i in range(3):
            self._panel_resumen.columnconfigure(i, weight=1)

        self._card_ingresos = _CardResumen(self._panel_resumen, "Total ingresos", "$0",
                                           COLORES["exito"], "#D4EDDA")
        self._card_ingresos.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self._card_egresos = _CardResumen(self._panel_resumen, "Total egresos", "$0",
                                          COLORES["error"], "#F8D7DA")
        self._card_egresos.grid(row=0, column=1, sticky="ew", padx=(0, 8))

        self._card_saldo = _CardResumen(self._panel_resumen, "Saldo del periodo", "$0",
                                        COLORES["rosa"], COLORES["rosa_suave"])
        self._card_saldo.grid(row=0, column=2, sticky="ew")

    def _actualizar_resumen(self, resumen: dict):
        ing  = resumen["total_ingresos"]
        egr  = resumen["total_egresos"]
        saldo = resumen["saldo"]

        self._card_ingresos.set_valor("$" + f"{ing:,.0f}")
        self._card_egresos.set_valor("$" + f"{egr:,.0f}")

        color_saldo = COLORES["exito"] if saldo >= 0 else COLORES["error"]
        fondo_saldo = "#D4EDDA" if saldo >= 0 else "#F8D7DA"
        self._card_saldo.set_valor("$" + f"{saldo:,.0f}", color_saldo, fondo_saldo)

    # ------------------------------------------------------------------ #
    #  Lista de movimientos                                                #
    # ------------------------------------------------------------------ #

    def _construir_lista(self):
        panel = card(self.contenido)
        panel.grid(row=3, column=0, sticky="nsew")
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)

        # Encabezado tabla
        enc = ctk.CTkFrame(panel, fg_color=COLORES["rosa_suave"], corner_radius=6)
        enc.pack(fill="x", padx=12, pady=(12, 4))
        enc.columnconfigure(0, weight=1)
        enc.columnconfigure(1, weight=2)
        enc.columnconfigure(2, weight=2)
        enc.columnconfigure(3, weight=1)
        enc.columnconfigure(4, weight=2)
        enc.columnconfigure(5, minsize=60)

        for col, txt in enumerate(["Fecha", "Categoria", "Descripcion",
                                   "Metodo", "Monto", ""]):
            ctk.CTkLabel(enc, text=txt, font=FUENTES["small"],
                         text_color=COLORES["rosa"], anchor="w",
                         ).grid(row=0, column=col, sticky="ew",
                                padx=(10 if col == 0 else 6, 4), pady=6)

        self._lista = ctk.CTkScrollableFrame(
            panel, fg_color="transparent",
            scrollbar_button_color=COLORES["rosa"],
            scrollbar_button_hover_color=COLORES["rosa_hover"],
        )
        self._lista.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        self._lista.columnconfigure(0, weight=1)

    def _cargar(self):
        resumen = self._service.resumen_por_rango(
            self._fecha_desde.strftime("%Y-%m-%d"),
            self._fecha_hasta.strftime("%Y-%m-%d"),
        )
        self._actualizar_resumen(resumen)

        movimientos = self._service.obtener_por_rango(
            self._fecha_desde.strftime("%Y-%m-%d"),
            self._fecha_hasta.strftime("%Y-%m-%d"),
        )

        self._actualizar_empleadas(movimientos)

        for w in self._lista.winfo_children():
            w.destroy()

        if not movimientos:
            etiqueta_suave(self._lista,
                           "Sin movimientos en el periodo seleccionado").pack(pady=20)
            return

        for m in movimientos:
            _FilaMovimiento(
                self._lista,
                movimiento=m,
                al_eliminar=self._eliminar,
            ).pack(fill="x", pady=1)

    def _eliminar(self, mov):
        if confirmar("Eliminar movimiento",
                     "Eliminar este movimiento de caja?"):
            self._service.eliminar(mov["id"])
            self._cargar()

    def _abrir_form_nuevo(self):
        _FormMovimiento(
            self,
            service=self._service,
            cfg_service=self._cfg_service,
            fecha_default=self._fecha_desde,
            al_guardar=self._cargar,
        )

    def _exportar(self):
        import tkinter.filedialog as fd
        import tkinter.messagebox as mb
        movimientos = self._service.obtener_por_rango(
            self._fecha_desde.strftime("%Y-%m-%d"),
            self._fecha_hasta.strftime("%Y-%m-%d"),
        )
        if not movimientos:
            mb.showinfo("Sin datos", "No hay movimientos en el periodo seleccionado.")
            return
        carpeta = fd.askdirectory(title="Elegir carpeta para guardar el Excel")
        if not carpeta:
            return
        try:
            ruta = exportar_movimientos(
                movimientos=movimientos,
                fecha_desde=self._fecha_desde.strftime("%Y-%m-%d"),
                fecha_hasta=self._fecha_hasta.strftime("%Y-%m-%d"),
                carpeta=carpeta,
            )
            linea1 = "Archivo guardado en: " + ruta
            if mb.askyesno("Exportado", linea1 + "  Abrir carpeta?"):
                import subprocess, os
                ruta_norm = os.path.normpath(ruta)
                if os.name == "nt":
                    subprocess.Popen(["explorer", "/select,", ruta_norm])
                else:
                    subprocess.Popen(["open", os.path.dirname(ruta_norm)])
        except Exception as e:
            mb.showerror("Error al exportar", str(e))

    def refrescar(self):
        self._cargar()


# ------------------------------------------------------------------ #
#  Card resumen                                                        #
# ------------------------------------------------------------------ #

class _CardResumen(ctk.CTkFrame):

    def __init__(self, parent, titulo, valor, color_texto, color_fondo):
        super().__init__(parent, fg_color=color_fondo,
                         corner_radius=10, border_width=1,
                         border_color=COLORES["borde"])
        self._color_texto = color_texto
        self._color_fondo = color_fondo

        ctk.CTkLabel(self, text=titulo, font=FUENTES["small"],
                     text_color=color_texto).pack(anchor="w", padx=16, pady=(12, 2))
        self._lbl_valor = ctk.CTkLabel(self, text=valor,
                                       font=FUENTES["titulo"],
                                       text_color=color_texto)
        self._lbl_valor.pack(anchor="w", padx=16, pady=(0, 12))

    def set_valor(self, valor, color_texto=None, color_fondo=None):
        ct = color_texto or self._color_texto
        cf = color_fondo or self._color_fondo
        self.configure(fg_color=cf)
        self._lbl_valor.configure(text=valor, text_color=ct)
        for w in self.winfo_children():
            if isinstance(w, ctk.CTkLabel) and w != self._lbl_valor:
                w.configure(text_color=ct)


# ------------------------------------------------------------------ #
#  Fila de movimiento                                                  #
# ------------------------------------------------------------------ #

class _FilaMovimiento(ctk.CTkFrame):

    def __init__(self, parent, movimiento, al_eliminar):
        m = movimiento
        es_ingreso = m["tipo"] == "ingreso"
        fondo = "#F0FFF4" if es_ingreso else "#FFF5F5"
        super().__init__(parent, fg_color=fondo,
                         corner_radius=6, border_width=1,
                         border_color=COLORES["borde"])
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.columnconfigure(2, weight=2)
        self.columnconfigure(3, weight=1)
        self.columnconfigure(4, weight=2)
        self.columnconfigure(5, minsize=60)

        fecha = m["fecha"] or ""
        cat   = m["categoria"] or ""
        desc  = m["descripcion"] or "—"
        mp    = m["metodo_pago_nombre"] or "—"
        monto = ("+" if es_ingreso else "-") + "$" + f"{m['monto']:,.0f}"
        color_monto = COLORES["exito"] if es_ingreso else COLORES["error"]

        ctk.CTkLabel(self, text=fecha, font=FUENTES["small"],
                     text_color=COLORES["texto_suave"], anchor="w",
                     ).grid(row=0, column=0, sticky="ew", padx=(10, 4), pady=8)
        ctk.CTkLabel(self, text=cat, font=FUENTES["small"],
                     text_color=COLORES["texto"], anchor="w",
                     ).grid(row=0, column=1, sticky="ew", padx=4, pady=8)
        ctk.CTkLabel(self, text=desc, font=FUENTES["small"],
                     text_color=COLORES["texto_suave"], anchor="w",
                     ).grid(row=0, column=2, sticky="ew", padx=4, pady=8)
        ctk.CTkLabel(self, text=mp, font=FUENTES["small"],
                     text_color=COLORES["texto_suave"], anchor="w",
                     ).grid(row=0, column=3, sticky="ew", padx=4, pady=8)
        ctk.CTkLabel(self, text=monto, font=FUENTES["subtitulo"],
                     text_color=color_monto, anchor="e",
                     ).grid(row=0, column=4, sticky="ew", padx=4, pady=8)

        ctk.CTkButton(
            self, text="✕", width=28, height=28,
            fg_color="transparent", hover_color="#FDECEA",
            text_color=COLORES["error"], font=FUENTES["normal"],
            corner_radius=6,
            command=lambda: al_eliminar(m),
        ).grid(row=0, column=5, padx=6, pady=4)


# ------------------------------------------------------------------ #
#  Formulario nuevo movimiento                                         #
# ------------------------------------------------------------------ #

class _FormMovimiento(ctk.CTkToplevel):

    def __init__(self, parent, service, cfg_service,
                 fecha_default=None, al_guardar=None):
        super().__init__(parent)
        self._service      = service
        self._al_guardar   = al_guardar
        self._fecha_default = fecha_default or date.today()

        metodos = cfg_service.obtener_metodos_pago()
        self._metodos_map = {m["nombre"]: m["id"] for m in metodos if m["activo"]}

        self.title("Nuevo movimiento de caja")
        self.geometry("440x540")
        self.minsize(400, 500)
        self.resizable(True, True)
        self.configure(fg_color=COLORES["fondo"])
        self._construir()
        self.after(100, self._forzar_foco)

    def _forzar_foco(self):
        self.lift()
        self.grab_set()
        self.focus_force()

    def _construir(self):
        # Botones arriba
        btns = ctk.CTkFrame(self, fg_color=COLORES["fondo_card"], corner_radius=0)
        btns.pack(fill="x")
        boton_secundario(btns, "Cancelar", comando=self.destroy, ancho=160).pack(
            side="left", padx=28, pady=12)
        boton_primario(btns, "Guardar", comando=self._guardar, ancho=160).pack(
            side="right", padx=28, pady=12)
        separador(self).pack(fill="x")

        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORES["rosa"],
            scrollbar_button_hover_color=COLORES["rosa_hover"],
        )
        scroll.pack(fill="both", expand=True)

        pad = {"padx": 28, "pady": 5}

        # Tipo ingreso/egreso
        etiqueta_suave(scroll, "Tipo *").pack(anchor="w", padx=28, pady=(14, 2))
        self._var_tipo = ctk.StringVar(value="ingreso")
        tipo_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        tipo_frame.pack(**pad)

        self._btn_ingreso = ctk.CTkButton(
            tipo_frame, text="Ingreso", width=180, height=36,
            fg_color=COLORES["rosa"], hover_color=COLORES["rosa_hover"],
            text_color=COLORES["texto_blanco"], font=FUENTES["boton"],
            corner_radius=8, command=lambda: self._set_tipo("ingreso"),
        )
        self._btn_ingreso.pack(side="left", padx=(0, 8))

        self._btn_egreso = ctk.CTkButton(
            tipo_frame, text="Egreso", width=180, height=36,
            fg_color="transparent", hover_color=COLORES["rosa_suave"],
            text_color=COLORES["rosa"], border_color=COLORES["rosa"],
            border_width=1, font=FUENTES["boton"],
            corner_radius=8, command=lambda: self._set_tipo("egreso"),
        )
        self._btn_egreso.pack(side="left")

        # Categoria
        etiqueta_suave(scroll, "Categoria *").pack(anchor="w", padx=28, pady=(10, 2))
        self._var_cat = ctk.StringVar(value=CATEGORIAS_INGRESO[0])
        self._combo_cat = ctk.CTkComboBox(
            scroll, values=CATEGORIAS_INGRESO,
            variable=self._var_cat, width=384, height=36,
            fg_color=COLORES["fondo_input"], border_color=COLORES["borde"],
            button_color=COLORES["rosa"], button_hover_color=COLORES["rosa_hover"],
            text_color=COLORES["texto"], font=FUENTES["normal"], corner_radius=8,
        )
        self._combo_cat.pack(**pad)

        # Monto
        etiqueta_suave(scroll, "Monto ($) *").pack(anchor="w", padx=28, pady=(10, 2))
        self._monto = campo_texto(scroll, placeholder="0", ancho=384)
        self._monto.pack(**pad)

        # Metodo de pago
        etiqueta_suave(scroll, "Metodo de pago").pack(anchor="w", padx=28, pady=(10, 2))
        nombres_mp = list(self._metodos_map.keys())
        self._var_mp = ctk.StringVar(value=nombres_mp[0] if nombres_mp else "")
        ctk.CTkOptionMenu(
            scroll, values=nombres_mp, variable=self._var_mp,
            width=384, height=36,
            fg_color=COLORES["rosa"], button_color=COLORES["rosa_hover"],
            button_hover_color=COLORES["rosa_hover"],
            text_color=COLORES["texto_blanco"],
            font=FUENTES["normal"], corner_radius=8,
        ).pack(**pad)

        # Fecha
        etiqueta_suave(scroll, "Fecha  — editable para cargar movimientos de dias anteriores").pack(
            anchor="w", padx=28, pady=(10, 2))
        self._fecha = campo_texto(scroll, ancho=384)
        self._fecha.insert(0, self._fecha_default.strftime("%Y-%m-%d"))
        self._fecha.pack(**pad)

        # Descripcion / comentario
        etiqueta_suave(scroll, "Descripcion / comentario").pack(
            anchor="w", padx=28, pady=(10, 2))
        self._desc = ctk.CTkTextbox(
            scroll, width=384, height=80,
            fg_color=COLORES["fondo_input"], border_color=COLORES["borde"],
            border_width=2, text_color=COLORES["texto"],
            font=FUENTES["normal"], corner_radius=8,
        )
        self._desc.pack(padx=28, pady=(0, 20))

    def _set_tipo(self, tipo: str):
        self._var_tipo.set(tipo)
        if tipo == "ingreso":
            self._btn_ingreso.configure(
                fg_color=COLORES["rosa"], text_color=COLORES["texto_blanco"],
                border_width=0)
            self._btn_egreso.configure(
                fg_color="transparent", text_color=COLORES["rosa"],
                border_color=COLORES["rosa"], border_width=1)
            self._combo_cat.configure(values=CATEGORIAS_INGRESO)
            self._var_cat.set(CATEGORIAS_INGRESO[0])
        else:
            self._btn_egreso.configure(
                fg_color=COLORES["rosa"], text_color=COLORES["texto_blanco"],
                border_width=0)
            self._btn_ingreso.configure(
                fg_color="transparent", text_color=COLORES["rosa"],
                border_color=COLORES["rosa"], border_width=1)
            self._combo_cat.configure(values=CATEGORIAS_EGRESO)
            self._var_cat.set(CATEGORIAS_EGRESO[0])

    def _guardar(self):
        tipo  = self._var_tipo.get()
        cat   = self._var_cat.get().strip()
        desc  = self._desc.get("1.0", "end").strip()
        fecha = self._fecha.get().strip()
        mp_id = self._metodos_map.get(self._var_mp.get())

        try:
            monto = float(self._monto.get().strip())
        except ValueError:
            mostrar_error("Error", "El monto debe ser un numero.")
            return

        try:
            date.fromisoformat(fecha)
        except ValueError:
            mostrar_error("Error", "Fecha invalida. Usar YYYY-MM-DD.")
            return

        if tipo == "ingreso":
            ok, msg, _ = self._service.registrar_ingreso(
                categoria=cat, monto=monto,
                metodo_pago_id=mp_id, descripcion=desc, fecha=fecha)
        else:
            ok, msg, _ = self._service.registrar_egreso(
                categoria=cat, monto=monto,
                metodo_pago_id=mp_id, descripcion=desc, fecha=fecha)

        if not ok:
            mostrar_error("Error", msg)
            return

        mostrar_exito("Listo", msg)
        self.destroy()
        if self._al_guardar:
            self._al_guardar()
