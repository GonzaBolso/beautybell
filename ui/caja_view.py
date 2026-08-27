import customtkinter as ctk
import calendar as _calendar
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

    def _construir_contenido(self):
        self.contenido = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.contenido.pack(fill="both", expand=True, padx=24, pady=(4, 16))
        self.contenido.columnconfigure(0, weight=1)
        self.contenido.rowconfigure(2, weight=1)

        boton_secundario(
            self._acciones, "💾  Backup",
            comando=self._backup, ancho=130
        ).pack(side="right", padx=(8, 0))
        boton_secundario(
            self._acciones, "⬇  Exportar Excel",
            comando=self._exportar, ancho=160
        ).pack(side="right", padx=(8, 0))
        boton_primario(
            self._acciones, "＋  Movimiento",
            comando=self._abrir_form_nuevo, ancho=160
        ).pack(side="right")

        self._construir_filtros()
        self._construir_resumen()
        self._construir_lista()
        self._cargar()

    # ------------------------------------------------------------------ #
    #  Filtros con calendarios                                             #
    # ------------------------------------------------------------------ #

    def _construir_filtros(self):
        panel = ctk.CTkFrame(self.contenido, fg_color="transparent")
        panel.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        etiqueta_suave(panel, "Desde:").pack(side="left", padx=(0, 4))
        self._btn_desde = ctk.CTkButton(
            panel, text=self._fecha_desde.strftime("%d/%m/%Y"),
            width=120, height=32,
            fg_color="transparent", hover_color=COLORES["rosa_suave"],
            text_color=COLORES["texto"], border_color=COLORES["borde"],
            border_width=1, font=FUENTES["normal"], corner_radius=8,
            command=lambda: self._abrir_calendario("desde"),
        )
        self._btn_desde.pack(side="left", padx=(0, 12))

        etiqueta_suave(panel, "Hasta:").pack(side="left", padx=(0, 4))
        self._btn_hasta = ctk.CTkButton(
            panel, text=self._fecha_hasta.strftime("%d/%m/%Y"),
            width=120, height=32,
            fg_color="transparent", hover_color=COLORES["rosa_suave"],
            text_color=COLORES["texto"], border_color=COLORES["borde"],
            border_width=1, font=FUENTES["normal"], corner_radius=8,
            command=lambda: self._abrir_calendario("hasta"),
        )
        self._btn_hasta.pack(side="left", padx=(0, 12))

        boton_primario(panel, "Buscar", comando=self._cargar, ancho=90).pack(side="left")

    def _abrir_calendario(self, cual: str):
        fecha_actual = self._fecha_desde if cual == "desde" else self._fecha_hasta
        btn = self._btn_desde if cual == "desde" else self._btn_hasta
        _CalendarioPopup(
            self,
            anchor_widget=btn,
            fecha_inicial=fecha_actual,
            al_seleccionar=lambda f: self._fecha_seleccionada(cual, f),
        )

    def _fecha_seleccionada(self, cual: str, fecha: date):
        if cual == "desde":
            self._fecha_desde = fecha
            self._btn_desde.configure(text=fecha.strftime("%d/%m/%Y"))
            # Si desde > hasta, ajustar hasta
            if self._fecha_desde > self._fecha_hasta:
                self._fecha_hasta = fecha
                self._btn_hasta.configure(text=fecha.strftime("%d/%m/%Y"))
        else:
            self._fecha_hasta = fecha
            self._btn_hasta.configure(text=fecha.strftime("%d/%m/%Y"))
            if self._fecha_hasta < self._fecha_desde:
                self._fecha_desde = fecha
                self._btn_desde.configure(text=fecha.strftime("%d/%m/%Y"))
        self._cargar()

    # ------------------------------------------------------------------ #
    #  Resumen                                                             #
    # ------------------------------------------------------------------ #

    def _construir_resumen(self):
        self._panel_resumen = ctk.CTkFrame(self.contenido, fg_color="transparent")
        self._panel_resumen.grid(row=1, column=0, sticky="ew", pady=(0, 8))
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
        ing   = resumen["total_ingresos"]
        egr   = resumen["total_egresos"]
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
        self._panel_lista = card(self.contenido)
        self._panel_lista.grid(row=2, column=0, sticky="nsew")
        self._panel_lista.columnconfigure(0, weight=1)
        self._panel_lista.rowconfigure(1, weight=1)

        # Encabezado fijo
        self._enc = ctk.CTkFrame(self._panel_lista, fg_color=COLORES["rosa_suave"], corner_radius=6)
        self._enc.pack(fill="x", padx=12, pady=(12, 0))
        self._enc.columnconfigure(0, minsize=100)
        self._enc.columnconfigure(1, minsize=110)
        self._enc.columnconfigure(2, weight=1)
        self._enc.columnconfigure(3, minsize=100)
        self._enc.columnconfigure(4, minsize=100)
        self._enc.columnconfigure(5, minsize=80)

        for col, txt in enumerate(["Fecha", "Categoria", "Descripcion", "Metodo", "Monto", ""]):
            ctk.CTkLabel(self._enc, text=txt, font=FUENTES["small"],
                         text_color=COLORES["rosa"], anchor="w",
                         ).grid(row=0, column=col, sticky="ew",
                                padx=(10 if col == 0 else 6, 4), pady=6)

        # Scrollable solo para las filas
        self._lista = ctk.CTkScrollableFrame(
            self._panel_lista, fg_color="transparent",
            scrollbar_button_color=COLORES["rosa"],
            scrollbar_button_hover_color=COLORES["rosa_hover"],
        )
        self._lista.pack(fill="both", expand=True, padx=12, pady=(0, 6))
        self._lista.columnconfigure(0, minsize=100)
        self._lista.columnconfigure(1, minsize=110)
        self._lista.columnconfigure(2, weight=1)
        self._lista.columnconfigure(3, minsize=100)
        self._lista.columnconfigure(4, minsize=100)
        self._lista.columnconfigure(5, minsize=80)

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

        for w in self._lista.winfo_children():
            w.destroy()

        if not movimientos:
            ctk.CTkLabel(self._lista, text="Sin movimientos en el periodo seleccionado",
                         font=FUENTES["normal"], text_color=COLORES["texto_suave"],
                         ).grid(row=0, column=0, columnspan=6, pady=20)
            return

        for fila_i, m in enumerate(movimientos):
            es_ingreso = m["tipo"] == "ingreso"
            fondo = "#F0FFF4" if es_ingreso else "#FFF5F5"
            color_monto = COLORES["exito"] if es_ingreso else COLORES["error"]
            monto_txt = ("+" if es_ingreso else "-") + "$" + f"{m['monto']:,.0f}"

            bg = ctk.CTkFrame(self._lista, fg_color=fondo, corner_radius=6,
                              border_width=1, border_color=COLORES["borde"])
            bg.grid(row=fila_i, column=0, columnspan=6, sticky="ew", pady=1)
            bg.columnconfigure(0, minsize=100)
            bg.columnconfigure(1, minsize=110)
            bg.columnconfigure(2, weight=1)
            bg.columnconfigure(3, minsize=100)
            bg.columnconfigure(4, minsize=100)
            bg.columnconfigure(5, minsize=80)

            ctk.CTkLabel(bg, text=m["fecha"] or "", font=FUENTES["small"],
                         text_color=COLORES["texto_suave"], anchor="w",
                         ).grid(row=0, column=0, sticky="ew", padx=(10, 4), pady=8)
            ctk.CTkLabel(bg, text=m["categoria"] or "", font=FUENTES["small"],
                         text_color=COLORES["texto"], anchor="w",
                         ).grid(row=0, column=1, sticky="ew", padx=4, pady=8)
            ctk.CTkLabel(bg, text=m["descripcion"] or "—", font=FUENTES["small"],
                         text_color=COLORES["texto_suave"], anchor="w",
                         ).grid(row=0, column=2, sticky="ew", padx=4, pady=8)
            ctk.CTkLabel(bg, text=m["metodo_pago_nombre"] or "—", font=FUENTES["small"],
                         text_color=COLORES["texto_suave"], anchor="w",
                         ).grid(row=0, column=3, sticky="ew", padx=4, pady=8)
            ctk.CTkLabel(bg, text=monto_txt, font=FUENTES["subtitulo"],
                         text_color=color_monto, anchor="e",
                         ).grid(row=0, column=4, sticky="ew", padx=4, pady=8)

            btn_frame = ctk.CTkFrame(bg, fg_color="transparent")
            btn_frame.grid(row=0, column=5, padx=4, pady=4)

            ctk.CTkButton(
                btn_frame, text="✎", width=28, height=28,
                fg_color="transparent", hover_color=COLORES["rosa_suave"],
                text_color=COLORES["rosa"], font=FUENTES["normal"],
                corner_radius=6, command=lambda mv=m: self._abrir_form_editar(mv),
            ).pack(side="left", padx=(0, 2))
            ctk.CTkButton(
                btn_frame, text="✕", width=28, height=28,
                fg_color="transparent", hover_color="#FDECEA",
                text_color=COLORES["error"], font=FUENTES["normal"],
                corner_radius=6, command=lambda mv=m: self._eliminar(mv),
            ).pack(side="left")

    def _eliminar(self, mov):
        if confirmar("Eliminar movimiento", "Eliminar este movimiento de caja?"):
            self._service.eliminar(mov["id"])
            self._cargar()

    def _abrir_form_nuevo(self):
        _FormMovimiento(
            self, service=self._service, cfg_service=self._cfg_service,
            fecha_default=self._fecha_desde, al_guardar=self._cargar,
        )

    def _abrir_form_editar(self, mov):
        _FormMovimiento(
            self, service=self._service, cfg_service=self._cfg_service,
            fecha_default=self._fecha_desde, al_guardar=self._cargar,
            movimiento=mov,
        )

    def _backup(self):
        import tkinter.filedialog as fd
        import tkinter.messagebox as mb
        from datetime import datetime
        import os
        from db.database import crear_backup

        carpeta = fd.askdirectory(title="Elegir carpeta para guardar el backup")
        if not carpeta:
            return
        try:
            nombre = "BeautyBel_Backup_" + datetime.now().strftime("%Y-%m-%d_%H%M") + ".db"
            ruta = os.path.normpath(os.path.join(carpeta, nombre))
            crear_backup(ruta)
            if mb.askyesno("Backup guardado", "Archivo guardado en: " + ruta + "\n\nAbrir carpeta?"):
                import subprocess
                if os.name == "nt":
                    subprocess.Popen(["explorer", "/select,", ruta])
                else:
                    subprocess.Popen(["open", os.path.dirname(ruta)])
        except Exception as e:
            mb.showerror("Error al hacer backup", str(e))

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
            if mb.askyesno("Exportado", "Archivo guardado en: " + ruta + "\n\nAbrir carpeta?"):
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
#  Calendario popup                                                    #
# ------------------------------------------------------------------ #

class _CalendarioPopup(ctk.CTkToplevel):

    def __init__(self, parent, anchor_widget, fecha_inicial: date, al_seleccionar):
        super().__init__(parent)
        self._al_seleccionar = al_seleccionar
        self._mes = fecha_inicial.replace(day=1)
        self._seleccionada = fecha_inicial

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=COLORES["fondo_card"])

        # Posicionar debajo del boton que lo abrió
        anchor_widget.update_idletasks()
        x = anchor_widget.winfo_rootx()
        y = anchor_widget.winfo_rooty() + anchor_widget.winfo_height() + 4

        ancho_cal = 340
        alto_cal  = 270
        pantalla_ancho = self.winfo_screenwidth()
        pantalla_alto  = self.winfo_screenheight()
        if x + ancho_cal > pantalla_ancho:
            x = pantalla_ancho - ancho_cal - 8
        if y + alto_cal > pantalla_alto:
            y = anchor_widget.winfo_rooty() - alto_cal - 4

        self.geometry(f"{ancho_cal}x{alto_cal}+{x}+{y}")
        self.resizable(False, False)

        self._construir()
        self.bind("<FocusOut>", lambda _: self._cerrar())
        self.after(50, lambda: self.focus_force())

    def _construir(self):
        for w in self.winfo_children():
            w.destroy()

        # Navegacion mes
        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.pack(fill="x", padx=8, pady=(8, 4))
        nav.columnconfigure(1, weight=1)

        ctk.CTkButton(nav, text="<", width=24, height=24,
                      fg_color="transparent", hover_color=COLORES["rosa_suave"],
                      text_color=COLORES["rosa"], font=FUENTES["normal"],
                      corner_radius=6, command=self._mes_anterior,
                      ).grid(row=0, column=0)

        meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
                 "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
        ctk.CTkLabel(nav,
                     text=meses[self._mes.month - 1] + " " + str(self._mes.year),
                     font=FUENTES["normal"], text_color=COLORES["texto"],
                     ).grid(row=0, column=1)

        ctk.CTkButton(nav, text=">", width=24, height=24,
                      fg_color="transparent", hover_color=COLORES["rosa_suave"],
                      text_color=COLORES["rosa"], font=FUENTES["normal"],
                      corner_radius=6, command=self._mes_siguiente,
                      ).grid(row=0, column=2)

        # Dias de semana
        cab = ctk.CTkFrame(self, fg_color="transparent")
        cab.pack(fill="x", padx=6, pady=(2, 0))
        for i in range(7):
            cab.columnconfigure(i, weight=1)
        for i, d in enumerate(["Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"]):
            ctk.CTkLabel(cab, text=d, height=20,
                         font=FUENTES["small"],
                         text_color=COLORES["texto_suave"]).grid(row=0, column=i, sticky="ew")

        ctk.CTkFrame(self, height=1, fg_color=COLORES["borde"]).pack(fill="x", padx=6, pady=(2, 0))

        # Grilla dias
        grilla = ctk.CTkFrame(self, fg_color="transparent")
        grilla.pack(fill="both", expand=True, padx=6, pady=(2, 6))
        for i in range(7):
            grilla.columnconfigure(i, weight=1)
        for i in range(6):
            grilla.rowconfigure(i, weight=1)

        hoy = date.today()
        cal = _calendar.monthcalendar(self._mes.year, self._mes.month)

        for fila_i, semana in enumerate(cal):
            for col_i, num in enumerate(semana):
                if num == 0:
                    lbl = ctk.CTkLabel(grilla, text="", height=28, fg_color="transparent")
                    lbl.grid(row=fila_i, column=col_i, sticky="ew", padx=1, pady=1)
                    continue
                fecha = date(self._mes.year, self._mes.month, num)
                es_sel = fecha == self._seleccionada
                es_hoy = fecha == hoy

                if es_sel:
                    fg, tc = COLORES["rosa"], COLORES["texto_blanco"]
                elif es_hoy:
                    fg, tc = COLORES["rosa_suave"], COLORES["rosa"]
                else:
                    fg, tc = COLORES["fondo_card"], COLORES["texto"]

                lbl = ctk.CTkLabel(
                    grilla, text=str(num), height=28,
                    fg_color=fg, text_color=tc,
                    font=FUENTES["small"], corner_radius=14,
                    cursor="hand2",
                )
                lbl.grid(row=fila_i, column=col_i, sticky="ew", padx=2, pady=2)

                def _hacer_hover(w, f_in=COLORES["rosa_suave"], f_sel=(es_sel)):
                    if not f_sel:
                        w.configure(fg_color=f_in)
                def _quitar_hover(w, f_out, f_sel=(es_sel)):
                    if not f_sel:
                        w.configure(fg_color=f_out)

                lbl.bind("<Enter>",  lambda e, w=lbl, sel=es_sel: w.configure(fg_color=COLORES["rosa_suave"]) if not sel else None)
                lbl.bind("<Leave>",  lambda e, w=lbl, f=fg, sel=es_sel: w.configure(fg_color=f) if not sel else None)
                lbl.bind("<Button-1>", lambda e, f=fecha: self._elegir(f))

    def _mes_anterior(self):
        if self._mes.month == 1:
            self._mes = self._mes.replace(year=self._mes.year - 1, month=12)
        else:
            self._mes = self._mes.replace(month=self._mes.month - 1)
        self._construir()

    def _mes_siguiente(self):
        if self._mes.month == 12:
            self._mes = self._mes.replace(year=self._mes.year + 1, month=1)
        else:
            self._mes = self._mes.replace(month=self._mes.month + 1)
        self._construir()

    def _elegir(self, fecha: date):
        self._seleccionada = fecha
        self._al_seleccionar(fecha)
        self._cerrar()

    def _cerrar(self):
        try:
            self.destroy()
        except Exception:
            pass


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

    def __init__(self, parent, movimiento, al_eliminar, al_editar):
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
        self.columnconfigure(5, minsize=80)

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

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=0, column=5, padx=6, pady=4)

        ctk.CTkButton(
            btn_frame, text="✎", width=28, height=28,
            fg_color="transparent", hover_color=COLORES["rosa_suave"],
            text_color=COLORES["rosa"], font=FUENTES["normal"],
            corner_radius=6, command=lambda: al_editar(m),
        ).pack(side="left", padx=(0, 2))

        ctk.CTkButton(
            btn_frame, text="✕", width=28, height=28,
            fg_color="transparent", hover_color="#FDECEA",
            text_color=COLORES["error"], font=FUENTES["normal"],
            corner_radius=6, command=lambda: al_eliminar(m),
        ).pack(side="left")


# ------------------------------------------------------------------ #
#  Formulario nuevo / editar movimiento                                #
# ------------------------------------------------------------------ #

class _FormMovimiento(ctk.CTkToplevel):

    def __init__(self, parent, service, cfg_service,
                 fecha_default=None, al_guardar=None, movimiento=None):
        super().__init__(parent)
        self._service       = service
        self._al_guardar    = al_guardar
        self._fecha_default = fecha_default or date.today()
        self._movimiento    = movimiento
        self._es_edicion    = movimiento is not None

        metodos = cfg_service.obtener_metodos_pago()
        self._metodos_map = {m["nombre"]: m["id"] for m in metodos if m["activo"]}
        self._metodos_id_nombre = {v: k for k, v in self._metodos_map.items()}

        self.title("Editar movimiento" if self._es_edicion else "Nuevo movimiento")
        self.geometry("440x560")
        self.minsize(400, 520)
        self.resizable(True, True)
        self.configure(fg_color=COLORES["fondo"])
        self._construir()
        if self._es_edicion:
            self._rellenar()
        self.after(100, self._forzar_foco)

    def _forzar_foco(self):
        self.lift()
        self.grab_set()
        self.focus_force()

    def _construir(self):
        btns = ctk.CTkFrame(self, fg_color=COLORES["fondo_card"], corner_radius=0)
        btns.pack(fill="x")
        boton_secundario(btns, "Cancelar", comando=self.destroy, ancho=160).pack(
            side="left", padx=28, pady=12)
        boton_primario(btns, "Guardar", comando=self._guardar, ancho=160).pack(
            side="right", padx=28, pady=12)
        separador(self).pack(fill="x")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                        scrollbar_button_color=COLORES["rosa"],
                                        scrollbar_button_hover_color=COLORES["rosa_hover"])
        scroll.pack(fill="both", expand=True)
        pad = {"padx": 28, "pady": 5}

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

        etiqueta_suave(scroll, "Categoria *").pack(anchor="w", padx=28, pady=(10, 2))
        self._var_cat = ctk.StringVar(value=CATEGORIAS_INGRESO[0])
        self._combo_cat = ctk.CTkComboBox(
            scroll, values=CATEGORIAS_INGRESO, variable=self._var_cat,
            width=384, height=36,
            fg_color=COLORES["fondo_input"], border_color=COLORES["borde"],
            button_color=COLORES["rosa"], button_hover_color=COLORES["rosa_hover"],
            text_color=COLORES["texto"], font=FUENTES["normal"], corner_radius=8,
        )
        self._combo_cat.pack(**pad)

        etiqueta_suave(scroll, "Monto ($) *").pack(anchor="w", padx=28, pady=(10, 2))
        self._monto = campo_texto(scroll, placeholder="0", ancho=384)
        self._monto.pack(**pad)

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

        etiqueta_suave(scroll, "Fecha").pack(anchor="w", padx=28, pady=(10, 2))
        self._fecha = campo_texto(scroll, ancho=384)
        self._fecha.insert(0, self._fecha_default.strftime("%Y-%m-%d"))
        self._fecha.pack(**pad)

        etiqueta_suave(scroll, "Descripcion / comentario").pack(anchor="w", padx=28, pady=(10, 2))
        self._desc = ctk.CTkTextbox(
            scroll, width=384, height=80,
            fg_color=COLORES["fondo_input"], border_color=COLORES["borde"],
            border_width=2, text_color=COLORES["texto"],
            font=FUENTES["normal"], corner_radius=8,
        )
        self._desc.pack(padx=28, pady=(0, 20))

    def _rellenar(self):
        m = self._movimiento
        tipo = m["tipo"]
        self._set_tipo(tipo)
        cat = m["categoria"] or ""
        cats = CATEGORIAS_INGRESO if tipo == "ingreso" else CATEGORIAS_EGRESO
        if cat not in cats:
            self._combo_cat.configure(values=[cat] + cats)
        self._var_cat.set(cat)
        self._monto.delete(0, "end")
        self._monto.insert(0, str(int(m["monto"])))
        mp_nombre = self._metodos_id_nombre.get(m["metodo_pago_id"], "")
        if mp_nombre:
            self._var_mp.set(mp_nombre)
        self._fecha.delete(0, "end")
        self._fecha.insert(0, m["fecha"] or "")
        self._desc.delete("1.0", "end")
        self._desc.insert("1.0", m["descripcion"] or "")

    def _set_tipo(self, tipo: str):
        self._var_tipo.set(tipo)
        if tipo == "ingreso":
            self._btn_ingreso.configure(
                fg_color=COLORES["rosa"], text_color=COLORES["texto_blanco"], border_width=0)
            self._btn_egreso.configure(
                fg_color="transparent", text_color=COLORES["rosa"],
                border_color=COLORES["rosa"], border_width=1)
            self._combo_cat.configure(values=CATEGORIAS_INGRESO)
            self._var_cat.set(CATEGORIAS_INGRESO[0])
        else:
            self._btn_egreso.configure(
                fg_color=COLORES["rosa"], text_color=COLORES["texto_blanco"], border_width=0)
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

        if self._es_edicion:
            ok, msg = self._service.actualizar(
                self._movimiento["id"], tipo, cat, monto, mp_id, desc, fecha)
        else:
            if tipo == "ingreso":
                ok, msg, _ = self._service.registrar_ingreso(
                    categoria=cat, monto=monto, metodo_pago_id=mp_id,
                    descripcion=desc, fecha=fecha)
            else:
                ok, msg, _ = self._service.registrar_egreso(
                    categoria=cat, monto=monto, metodo_pago_id=mp_id,
                    descripcion=desc, fecha=fecha)

        if not ok:
            mostrar_error("Error", msg)
            return

        mostrar_exito("Listo", msg)
        self.destroy()
        if self._al_guardar:
            self._al_guardar()