import customtkinter as ctk
from datetime import date, datetime, timedelta
import calendar
from ui.vista_base import VistaBase
from ui.tema import COLORES, FUENTES
from ui.widgets import (
    boton_primario, boton_secundario, boton_peligro,
    campo_texto, etiqueta, etiqueta_suave, card,
    separador, selector, mostrar_error, mostrar_exito, confirmar
)
from services.turno_service import TurnoService
from services.caja_service import CajaService
from services.cliente_service import ClienteService
from services.configuracion_service import ConfiguracionService


ESTADO_COLORES = {
    "pendiente":   ("#FFF3CD", "#856404"),
    "confirmado":  ("#D1ECF1", "#0C5460"),
    "completado":  ("#D4EDDA", "#155724"),
    "cancelado":   ("#F8D7DA", "#721C24"),
}

ESTADO_ETIQUETAS = {
    "pendiente":  "Pendiente",
    "confirmado": "Confirmado",
    "completado": "Completado",
    "cancelado":  "Cancelado",
}


def _hora_sugerida() -> str:
    ahora = datetime.now()
    redondeo = ((ahora.minute // 15) + 1) * 15
    if redondeo >= 60:
        sugerida = ahora.replace(minute=0, second=0) + timedelta(hours=1)
    else:
        sugerida = ahora.replace(minute=redondeo, second=0)
    return sugerida.strftime("%H:%M")


class TurnosView(VistaBase):

    def __init__(self, parent, **kwargs):
        self._turno_service = TurnoService()
        self._caja_service  = CajaService()
        self._cli_service   = ClienteService()
        self._cfg_service   = ConfiguracionService()
        self._fecha_sel     = date.today()
        self._mes_actual    = date.today().replace(day=1)
        super().__init__(parent, titulo="Turnos", **kwargs)

    def _construir_contenido(self):
        self.contenido = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.contenido.pack(fill="both", expand=True, padx=24, pady=16)
        self.contenido.columnconfigure(0, weight=1)
        self.contenido.columnconfigure(1, weight=100)
        self.contenido.rowconfigure(0, weight=1)

        boton_primario(
            self._acciones, "  Nuevo turno",
            comando=self._abrir_form_nuevo, ancho=160
        ).pack()

        self._construir_panel_izquierdo()
        self._construir_panel_derecho()
        self._renderizar_calendario()
        self._cargar_lista()

    # ------------------------------------------------------------------ #
    #  Calendario                                                          #
    # ------------------------------------------------------------------ #

    def _construir_panel_izquierdo(self):
        self._panel_izq = card(self.contenido)
        self._panel_izq.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self._panel_izq.columnconfigure(0, weight=1)

        nav = ctk.CTkFrame(self._panel_izq, fg_color="transparent")
        nav.pack(fill="x", padx=12, pady=(14, 6))
        nav.columnconfigure(1, weight=1)

        ctk.CTkButton(nav, text="<", width=32, height=32,
                      fg_color="transparent", hover_color=COLORES["rosa_suave"],
                      text_color=COLORES["rosa"], font=FUENTES["normal"],
                      corner_radius=8, command=self._mes_anterior,
                      ).grid(row=0, column=0)

        self._lbl_mes = ctk.CTkLabel(nav, text="",
                                     font=FUENTES["subtitulo"],
                                     text_color=COLORES["texto"])
        self._lbl_mes.grid(row=0, column=1)

        ctk.CTkButton(nav, text=">", width=32, height=32,
                      fg_color="transparent", hover_color=COLORES["rosa_suave"],
                      text_color=COLORES["rosa"], font=FUENTES["normal"],
                      corner_radius=8, command=self._mes_siguiente,
                      ).grid(row=0, column=2)

        cab_sem = ctk.CTkFrame(self._panel_izq, fg_color="transparent")
        cab_sem.pack(fill="x", padx=12)
        for i in range(7):
            cab_sem.columnconfigure(i, weight=1)
        for i, d in enumerate(["Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"]):
            ctk.CTkLabel(cab_sem, text=d, height=24,
                         font=FUENTES["small"],
                         text_color=COLORES["texto_suave"]).grid(row=0, column=i, sticky="ew")

        separador(self._panel_izq).pack(fill="x", padx=12, pady=4)

        self._cal_frame = ctk.CTkFrame(self._panel_izq, fg_color="transparent")
        self._cal_frame.pack(fill="x", padx=12, pady=(0, 6))

        boton_secundario(self._panel_izq, "Hoy",
                         comando=self._ir_hoy, ancho=80).pack(pady=(0, 12))

    def _renderizar_calendario(self):
        for w in self._cal_frame.winfo_children():
            w.destroy()

        meses_es = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self._lbl_mes.configure(
            text=meses_es[self._mes_actual.month - 1] + " " + str(self._mes_actual.year)
        )

        ultimo_dia = calendar.monthrange(self._mes_actual.year, self._mes_actual.month)[1]
        fecha_fin  = self._mes_actual.replace(day=ultimo_dia)
        turnos_mes = self._turno_service.obtener_por_rango(
            self._mes_actual.strftime("%Y-%m-%d"),
            fecha_fin.strftime("%Y-%m-%d")
        )
        dias_con_turnos = set()
        for t in turnos_mes:
            if t["estado"] != "cancelado":
                dias_con_turnos.add(t["fecha_hora"][:10])

        cal = calendar.monthcalendar(self._mes_actual.year, self._mes_actual.month)
        hoy = date.today()

        for i in range(7):
            self._cal_frame.columnconfigure(i, weight=1)

        for fila_i, semana in enumerate(cal):
            for col_i, num_dia in enumerate(semana):
                if num_dia == 0:
                    ctk.CTkLabel(self._cal_frame, text="", height=34,
                                 fg_color="transparent",
                                 ).grid(row=fila_i, column=col_i, sticky="ew", padx=1, pady=1)
                    continue

                fecha_dia = date(self._mes_actual.year, self._mes_actual.month, num_dia)
                fecha_str = fecha_dia.strftime("%Y-%m-%d")
                es_hoy    = fecha_dia == hoy
                es_sel    = fecha_dia == self._fecha_sel
                tiene     = fecha_str in dias_con_turnos

                if es_sel:
                    fg, tc = COLORES["rosa"], COLORES["texto_blanco"]
                elif es_hoy:
                    fg, tc = COLORES["rosa_suave"], COLORES["rosa"]
                else:
                    fg, tc = COLORES["fondo_card"], COLORES["texto"]

                txt = str(num_dia) + (" •" if tiene and not es_sel else "")
                lbl = ctk.CTkLabel(
                    self._cal_frame, text=txt, height=34,
                    fg_color=fg, text_color=tc,
                    font=FUENTES["small"], corner_radius=17,
                    cursor="hand2",
                )
                lbl.grid(row=fila_i, column=col_i, sticky="ew", padx=2, pady=2)
                lbl.bind("<Enter>",    lambda e, w=lbl, sel=es_sel: w.configure(fg_color=COLORES["rosa_suave"]) if not sel else None)
                lbl.bind("<Leave>",    lambda e, w=lbl, f=fg, sel=es_sel: w.configure(fg_color=f) if not sel else None)
                lbl.bind("<Button-1>", lambda e, fd=fecha_dia: self._seleccionar_dia(fd))

    def _seleccionar_dia(self, fecha):
        self._fecha_sel = fecha
        self._renderizar_calendario()
        self._cargar_lista()

    def _mes_anterior(self):
        if self._mes_actual.month == 1:
            self._mes_actual = self._mes_actual.replace(year=self._mes_actual.year - 1, month=12)
        else:
            self._mes_actual = self._mes_actual.replace(month=self._mes_actual.month - 1)
        self._renderizar_calendario()

    def _mes_siguiente(self):
        if self._mes_actual.month == 12:
            self._mes_actual = self._mes_actual.replace(year=self._mes_actual.year + 1, month=1)
        else:
            self._mes_actual = self._mes_actual.replace(month=self._mes_actual.month + 1)
        self._renderizar_calendario()

    def _ir_hoy(self):
        self._fecha_sel  = date.today()
        self._mes_actual = date.today().replace(day=1)
        self._renderizar_calendario()
        self._cargar_lista()

    # ------------------------------------------------------------------ #
    #  Lista del dia                                                       #
    # ------------------------------------------------------------------ #

    def _construir_panel_derecho(self):
        self._panel_der = card(self.contenido)
        self._panel_der.grid(row=0, column=1, sticky="nsew")
        self._panel_der.columnconfigure(0, weight=1)
        self._panel_der.rowconfigure(1, weight=1)

        self._lbl_fecha_lista = ctk.CTkLabel(
            self._panel_der, text="",
            font=FUENTES["subtitulo"], text_color=COLORES["texto"])
        self._lbl_fecha_lista.pack(anchor="w", padx=20, pady=(16, 0))

        separador(self._panel_der).pack(fill="x", padx=20, pady=10)

        self._lista_turnos = ctk.CTkScrollableFrame(
            self._panel_der, fg_color="transparent",
            scrollbar_button_color=COLORES["rosa"],
            scrollbar_button_hover_color=COLORES["rosa_hover"],
        )
        self._lista_turnos.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        self._lista_turnos.columnconfigure(0, weight=1)

    def _cargar_lista(self):
        fecha_str = self._fecha_sel.strftime("%Y-%m-%d")
        meses_es  = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                     "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        lbl = (str(self._fecha_sel.day) + " de "
               + meses_es[self._fecha_sel.month - 1]
               + " de " + str(self._fecha_sel.year))
        self._lbl_fecha_lista.configure(text=lbl)

        for w in self._lista_turnos.winfo_children():
            w.destroy()

        turnos = self._turno_service.obtener_por_fecha(fecha_str)
        if not turnos:
            etiqueta_suave(self._lista_turnos,
                           "Sin turnos para este dia").pack(pady=30)
            return

        for t in turnos:
            _TarjetaTurno(
                self._lista_turnos, turno=t,
                al_cambiar_estado=self._cambiar_estado,
                al_cobrar=self._cobrar_turno,
                al_editar=self._abrir_form_editar,
                al_eliminar=self._eliminar_turno,
            ).pack(fill="x", pady=2, padx=4)

    # ------------------------------------------------------------------ #
    #  Acciones                                                            #
    # ------------------------------------------------------------------ #

    def _cambiar_estado(self, turno, nuevo_estado):
        if turno["estado"] == "completado":
            mostrar_error("No permitido",
                          "Este turno ya fue completado y cobrado.\n"
                          "No se puede cambiar el estado.")
            return
        ok, msg = self._turno_service.cambiar_estado(turno["id"], nuevo_estado)
        if not ok:
            mostrar_error("Error", msg)
            return
        self._cargar_lista()
        self._renderizar_calendario()

    def _cobrar_turno(self, turno):
        _DialogCobro(
            self, turno=turno,
            turno_service=self._turno_service,
            caja_service=self._caja_service,
            cfg_service=self._cfg_service,
            al_cobrar=lambda: (self._cargar_lista(), self._renderizar_calendario()),
        )

    def _abrir_form_nuevo(self):
        _FormTurno(
            self,
            turno_service=self._turno_service,
            cli_service=self._cli_service,
            cfg_service=self._cfg_service,
            fecha_inicial=self._fecha_sel,
            al_guardar=lambda: (self._cargar_lista(), self._renderizar_calendario()),
        )

    def _abrir_form_editar(self, turno):
        _FormTurno(
            self,
            turno_service=self._turno_service,
            cli_service=self._cli_service,
            cfg_service=self._cfg_service,
            turno=turno,
            fecha_inicial=self._fecha_sel,
            al_guardar=lambda: (self._cargar_lista(), self._renderizar_calendario()),
        )

    def _eliminar_turno(self, turno):
        if turno["estado"] == "completado":
            mostrar_error("No permitido",
                          "Este turno ya fue cobrado y registrado en caja.\n"
                          "Si necesitas eliminarlo, borra primero el movimiento\n"
                          "de caja asociado.")
            return
        hora = turno["fecha_hora"][11:16]
        if confirmar("Eliminar turno",
                     "Eliminar turno de " + turno["cliente_nombre"]
                     + " a las " + hora + "?"):
            self._turno_service.eliminar(turno["id"])
            self._cargar_lista()
            self._renderizar_calendario()

    def refrescar(self):
        self._cargar_lista()
        self._renderizar_calendario()


# ------------------------------------------------------------------ #
#  Tarjeta de turno  — layout con grid                                #
# ------------------------------------------------------------------ #

class _TarjetaTurno(ctk.CTkFrame):

    def __init__(self, parent, turno, al_cambiar_estado,
                 al_cobrar, al_editar, al_eliminar):
        super().__init__(parent, fg_color=COLORES["fondo_card"],
                         corner_radius=10, border_width=1,
                         border_color=COLORES["borde"])

        estado  = turno["estado"]
        colores = ESTADO_COLORES.get(estado, ("#F8F9FA", "#495057"))

        # Agrupar servicios por empleada, preservando el orden de aparicion
        servicios = turno.get("servicios", [])
        if not servicios:
            servicios = [{
                "empleada_nombre": turno.get("empleada_nombre") or "—",
                "servicio_nombre": turno.get("servicio_nombre") or "—",
                "precio": turno.get("servicio_precio") or 0,
            }]

        grupos_por_empleada = {}
        orden_empleadas = []
        for s in servicios:
            nombre_emp = s.get("empleada_nombre") or turno.get("empleada_nombre") or "—"
            if nombre_emp not in grupos_por_empleada:
                grupos_por_empleada[nombre_emp] = []
                orden_empleadas.append(nombre_emp)
            grupos_por_empleada[nombre_emp].append(s)

        # Franja de color izquierda — cubre todas las filas de la tarjeta:
        # hora/cliente, una fila por empleada, total, notas (opcional),
        # separador y botones.
        filas_totales = 4 + len(orden_empleadas) + (1 if turno["notas"] else 0)
        franja = ctk.CTkFrame(self, width=6, fg_color=colores[1], corner_radius=0)
        franja.grid(row=0, column=0, sticky="ns", rowspan=filas_totales)
        franja.grid_propagate(False)

        # Columna de contenido
        self.columnconfigure(1, weight=1)

        # --- Fila 0: hora + cliente + badge ---
        fila0 = ctk.CTkFrame(self, fg_color="transparent")
        fila0.grid(row=0, column=1, sticky="ew", padx=(12, 12), pady=(4, 0))
        fila0.columnconfigure(1, weight=1)

        hora = turno["fecha_hora"][11:16]
        ctk.CTkLabel(fila0, text=hora, font=FUENTES["subtitulo"],
                     text_color=COLORES["rosa"]).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(fila0, text=turno["cliente_nombre"],
                     font=FUENTES["normal"],
                     text_color=COLORES["texto"]).grid(row=0, column=1, sticky="w", padx=(10, 0))
        ctk.CTkLabel(fila0,
                     text=" " + ESTADO_ETIQUETAS.get(estado, estado) + " ",
                     font=FUENTES["small"],
                     fg_color=colores[0], text_color=colores[1],
                     corner_radius=6).grid(row=0, column=2, sticky="e")

        # --- Una fila por empleada, con sus servicios ---
        fila_i = 1
        for nombre_emp in orden_empleadas:
            srv_list = grupos_por_empleada[nombre_emp]
            texto_srv = ",  ".join(
                s["servicio_nombre"] + " ($" + str(int(s["precio"])) + ")"
                for s in srv_list
            )
            fila_emp = ctk.CTkFrame(self, fg_color="transparent")
            fila_emp.grid(row=fila_i, column=1, sticky="ew", padx=(12, 12), pady=(2, 0))
            ctk.CTkLabel(fila_emp, text=nombre_emp + ":",
                         font=FUENTES["small"],
                         text_color=COLORES["texto_suave"]).pack(side="left")
            ctk.CTkLabel(fila_emp, text=" " + texto_srv,
                         font=FUENTES["small"],
                         text_color=COLORES["texto"],
                         anchor="w", wraplength=360,
                         justify="left").pack(side="left", fill="x", expand=True)
            fila_i += 1

        # --- Fila de total ---
        precio_total = turno.get("precio_total", 0)
        fila_total = ctk.CTkFrame(self, fg_color="transparent")
        fila_total.grid(row=fila_i, column=1, sticky="ew", padx=(12, 12), pady=(2, 0))
        ctk.CTkLabel(fila_total, text="Total: $" + str(int(precio_total)),
                     font=FUENTES["small"],
                     text_color=COLORES["texto"]).pack(side="right")
        fila_i += 1

        # --- Notas (opcional) ---
        if turno["notas"]:
            ctk.CTkLabel(self, text=turno["notas"],
                         font=FUENTES["small"],
                         text_color=COLORES["texto_suave"],
                         anchor="w").grid(row=fila_i, column=1, sticky="ew",
                                          padx=(12, 12), pady=(2, 0))
            fila_i += 1

        # --- Separador ---
        separador(self).grid(row=fila_i, column=1, sticky="ew",
                             padx=(12, 12), pady=(1, 0))
        fila_i += 1

        # --- Fila botones ---
        acc = ctk.CTkFrame(self, fg_color="transparent")
        acc.grid(row=fila_i, column=1, sticky="ew",
                 padx=(12, 12), pady=(4, 4))

        if estado == "pendiente":
            boton_primario(acc, "Confirmar",
                           comando=lambda: al_cambiar_estado(turno, "confirmado"),
                           ancho=110).pack(side="left", padx=(0, 6))
            boton_secundario(acc, "Cancelar",
                             comando=lambda: al_cambiar_estado(turno, "cancelado"),
                             ancho=100).pack(side="left")
        elif estado == "confirmado":
            boton_primario(acc, "Completar y cobrar",
                           comando=lambda: al_cobrar(turno),
                           ancho=160).pack(side="left", padx=(0, 6))
            boton_secundario(acc, "Solo completar",
                             comando=lambda: al_cambiar_estado(turno, "completado"),
                             ancho=120).pack(side="left", padx=(0, 6))
            boton_secundario(acc, "Cancelar",
                             comando=lambda: al_cambiar_estado(turno, "cancelado"),
                             ancho=90).pack(side="left")
        elif estado == "completado":
            ctk.CTkLabel(acc, text="Completado",
                         font=FUENTES["small"],
                         text_color=COLORES["exito"]).pack(side="left")

        boton_peligro(acc, "X", comando=lambda: al_eliminar(turno),
                      ancho=34).pack(side="right", padx=(2, 0))
        boton_secundario(acc, "✎", comando=lambda: al_editar(turno),
                         ancho=34).pack(side="right", padx=(0, 2))


# ------------------------------------------------------------------ #
#  Dialog cobro                                                        #
# ------------------------------------------------------------------ #

class _DialogCobro(ctk.CTkToplevel):

    def __init__(self, parent, turno, turno_service, caja_service,
                 cfg_service, al_cobrar):
        super().__init__(parent)
        self._turno         = turno
        self._turno_service = turno_service
        self._caja_service  = caja_service
        self._al_cobrar     = al_cobrar
        self._filas_pago    = []   # cada item: {frame, var_mp, e_monto}

        self.title("Completar y cobrar turno")
        self.geometry("440x540")
        self.minsize(420, 480)
        self.resizable(True, True)
        self.configure(fg_color=COLORES["fondo"])

        metodos = cfg_service.obtener_metodos_pago()
        self._metodos_map = {m["nombre"]: m["id"] for m in metodos if m["activo"]}
        self._construir(turno)
        self.after(100, self._forzar_foco)

    def _forzar_foco(self):
        self.lift()
        self.grab_set()
        self.focus_force()

    def _construir(self, turno):
        btns_top = ctk.CTkFrame(self, fg_color=COLORES["fondo_card"], corner_radius=0)
        btns_top.pack(fill="x")
        boton_secundario(btns_top, "Cancelar", comando=self.destroy, ancho=140).pack(
            side="left", padx=20, pady=12)
        boton_primario(btns_top, "Confirmar cobro", comando=self._confirmar, ancho=160).pack(
            side="right", padx=20, pady=12)
        separador(self).pack(fill="x")

        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORES["rosa"],
            scrollbar_button_hover_color=COLORES["rosa_hover"],
        )
        self._scroll.pack(fill="both", expand=True)
        self._scroll.columnconfigure(0, weight=1)

        hora = turno["fecha_hora"][11:16]
        etiqueta(self._scroll, turno["cliente_nombre"] + "  -  " + hora,
                 fuente="subtitulo").pack(anchor="w", padx=20, pady=(16, 2))

        # Mostrar servicios, agrupados por empleada
        servicios = turno.get("servicios", [])
        if servicios:
            grupos_por_empleada = {}
            orden_empleadas = []
            for s in servicios:
                nombre_emp = s.get("empleada_nombre") or turno.get("empleada_nombre") or "—"
                if nombre_emp not in grupos_por_empleada:
                    grupos_por_empleada[nombre_emp] = []
                    orden_empleadas.append(nombre_emp)
                grupos_por_empleada[nombre_emp].append(s)

            for nombre_emp in orden_empleadas:
                ctk.CTkLabel(
                    self._scroll, text=nombre_emp,
                    font=FUENTES["small"], text_color=COLORES["rosa"],
                ).pack(anchor="w", padx=20, pady=(4, 0))
                for s in grupos_por_empleada[nombre_emp]:
                    ctk.CTkLabel(
                        self._scroll,
                        text="• " + s["servicio_nombre"] + "  $" + str(int(s["precio"])),
                        font=FUENTES["small"],
                        text_color=COLORES["texto_suave"],
                    ).pack(anchor="w", padx=32)
        else:
            etiqueta_suave(self._scroll, turno.get("servicio_nombre", "")).pack(anchor="w", padx=20)

        self._precio_total = turno.get("precio_total") or turno.get("servicio_precio") or 0

        separador(self._scroll).pack(fill="x", padx=20, pady=12)

        # --- Metodos de pago (dinamico) ---
        etiqueta_suave(self._scroll, "Metodos de pago *").pack(anchor="w", padx=20, pady=(0, 4))

        self._frame_pagos = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._frame_pagos.pack(fill="x", padx=20)
        self._frame_pagos.columnconfigure(0, weight=1)
        self._frame_pagos.columnconfigure(1, weight=1)

        boton_secundario(
            self._scroll, "+ Agregar metodo de pago",
            comando=self._agregar_fila_pago, ancho=220,
        ).pack(anchor="w", padx=20, pady=(6, 0))

        # --- Resumen de totales ---
        self._lbl_resumen = ctk.CTkLabel(
            self._scroll, text="", justify="left", anchor="w",
            font=FUENTES["normal"], text_color=COLORES["texto"],
        )
        self._lbl_resumen.pack(anchor="w", padx=20, pady=(12, 16))

        # Primera fila con el total precargado
        self._agregar_fila_pago(monto_inicial=self._precio_total)

    def _agregar_fila_pago(self, metodo_nombre="", monto_inicial=None):
        fila = ctk.CTkFrame(self._frame_pagos, fg_color=COLORES["rosa_suave"],
                            corner_radius=8)
        fila.pack(fill="x", pady=3)
        fila.columnconfigure(0, weight=1)
        fila.columnconfigure(1, weight=1)

        nombres = list(self._metodos_map.keys())
        var_mp = ctk.StringVar(value=metodo_nombre or (nombres[0] if nombres else ""))

        combo = ctk.CTkOptionMenu(
            fila, values=nombres, variable=var_mp,
            width=0, height=36,
            fg_color=COLORES["rosa"], button_color=COLORES["rosa_hover"],
            button_hover_color=COLORES["rosa_hover"],
            text_color=COLORES["texto_blanco"],
            font=FUENTES["normal"], corner_radius=8,
        )
        combo.grid(row=0, column=0, sticky="ew", padx=(8, 4), pady=6)

        e_monto = campo_texto(fila, placeholder="Monto $", ancho=0)
        if monto_inicial is not None:
            e_monto.insert(0, str(int(monto_inicial)))
        e_monto.grid(row=0, column=1, sticky="ew", padx=(0, 4), pady=6)
        e_monto.bind("<KeyRelease>", lambda _: self._actualizar_resumen())

        btn_quitar = ctk.CTkButton(
            fila, text="✕", width=28, height=28,
            fg_color="transparent", hover_color="#FDECEA",
            text_color=COLORES["error"], font=FUENTES["normal"],
            corner_radius=6,
        )
        btn_quitar.grid(row=0, column=2, padx=(0, 6), pady=6)

        info = {"frame": fila, "var_mp": var_mp, "e_monto": e_monto}
        self._filas_pago.append(info)

        def _quitar(i=info):
            if len(self._filas_pago) <= 1:
                mostrar_error("Error", "Debe haber al menos un metodo de pago.")
                return
            i["frame"].destroy()
            self._filas_pago.remove(i)
            self._actualizar_resumen()

        btn_quitar.configure(command=_quitar)
        self._actualizar_resumen()

    def _actualizar_resumen(self):
        total_pagado = 0.0
        for info in self._filas_pago:
            try:
                total_pagado += float(info["e_monto"].get().strip() or 0)
            except ValueError:
                pass

        diferencia = total_pagado - self._precio_total
        texto = (
            "Total del turno: $" + str(int(self._precio_total)) + "\n"
            + "Total ingresado: $" + str(int(total_pagado))
        )
        if abs(diferencia) > 0.01:
            if diferencia > 0:
                texto += "\nSobran $" + str(int(diferencia))
            else:
                texto += "\nFaltan $" + str(int(abs(diferencia)))
        self._lbl_resumen.configure(text=texto)

    def _confirmar(self):
        pagos = []
        for info in self._filas_pago:
            nombre_mp = info["var_mp"].get().strip()
            if not nombre_mp or nombre_mp not in self._metodos_map:
                mostrar_error("Error", "Selecciona un metodo de pago valido en cada fila.")
                return
            try:
                monto = float(info["e_monto"].get().strip())
            except ValueError:
                mostrar_error("Error", "El monto debe ser un numero.")
                return
            if monto <= 0:
                mostrar_error("Error", "El monto debe ser mayor a cero.")
                return
            pagos.append({
                "metodo_pago_id": self._metodos_map[nombre_mp],
                "monto": monto,
            })

        if not pagos:
            mostrar_error("Error", "Agrega al menos un metodo de pago.")
            return

        total_pagado = sum(p["monto"] for p in pagos)
        if abs(total_pagado - self._precio_total) > 0.01:
            if not confirmar(
                "Monto distinto al total",
                "El total ingresado ($" + str(int(total_pagado)) + ") no coincide "
                "con el precio del turno ($" + str(int(self._precio_total)) + ").\n"
                "Deseas continuar igual?"
            ):
                return

        servicios = self._turno.get("servicios", [])
        nombres_srv = ", ".join(s["servicio_nombre"] for s in servicios) if servicios else (self._turno.get("servicio_nombre") or "")

        if servicios:
            nombres_emp = []
            for s in servicios:
                nombre_emp = s.get("empleada_nombre") or self._turno.get("empleada_nombre") or ""
                if nombre_emp and nombre_emp not in nombres_emp:
                    nombres_emp.append(nombre_emp)
            nombres_emp_txt = ", ".join(nombres_emp)
        else:
            nombres_emp_txt = self._turno.get("empleada_nombre") or ""

        from datetime import datetime
        ok, msg, ids_caja = self._caja_service.registrar_cobro_turno_multiple(
            turno_id=self._turno["id"],
            pagos=pagos,
            fecha=datetime.now().strftime("%Y-%m-%d"),
            descripcion="Cobro: " + self._turno["cliente_nombre"]
                        + " - " + nombres_srv
                        + " - " + nombres_emp_txt,
        )
        if not ok:
            mostrar_error("Error al registrar en caja", msg)
            return

        ok, msg = self._turno_service.completar(self._turno["id"])
        if not ok:
            mostrar_error("Error al completar", msg)
            return

        self.grab_release()
        self.destroy()
        mostrar_exito("Listo", "Turno completado y cobro registrado en caja.")
        if self._al_cobrar:
            self._al_cobrar()


# ------------------------------------------------------------------ #
#  Widget buscador con dropdown                                        #
# ------------------------------------------------------------------ #

class _BuscadorConDropdown(ctk.CTkFrame):

    def __init__(self, parent, opciones: list[str], placeholder="", ancho=444, var_externa=None, **kwargs):
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self._opciones = opciones
        self._popup    = None
        self._ignorar_cambio = False

        self._var = var_externa if var_externa is not None else ctk.StringVar()
        self._entry = ctk.CTkEntry(
            self,
            textvariable=self._var,
            placeholder_text=placeholder,
            width=ancho, height=36,
            fg_color=COLORES["fondo_input"],
            border_color=COLORES["borde"],
            text_color=COLORES["texto"],
            placeholder_text_color=COLORES["texto_suave"],
            corner_radius=8,
            font=FUENTES["normal"],
        )
        self._entry.pack(fill="x")
        self._var.trace_add("write", self._on_cambio)
        self._entry.bind("<FocusOut>", lambda _: self.after(150, self._cerrar_popup))
        self._entry.bind("<Escape>",   lambda _: self._cerrar_popup())
        self._entry.bind("<Down>",     lambda _: self._foco_popup())

    def get(self) -> str:
        return self._var.get()

    def set(self, valor: str):
        self._ignorar_cambio = True
        self._var.set(valor)
        self._ignorar_cambio = False

    def _on_cambio(self, *_):
        if self._ignorar_cambio:
            return
        texto = self._var.get().strip().lower()
        if not texto:
            self._cerrar_popup()
            return
        coincidencias = [o for o in self._opciones if texto in o.lower()]
        if coincidencias:
            self._mostrar_popup(coincidencias)
        else:
            self._cerrar_popup()

    def _mostrar_popup(self, opciones: list[str]):
        self._cerrar_popup()

        self._entry.update_idletasks()
        x     = self._entry.winfo_rootx()
        y     = self._entry.winfo_rooty() + self._entry.winfo_height() + 2
        ancho = self._entry.winfo_width()
        alto  = min(len(opciones) * 38 + 4, 200)

        root = self._entry.winfo_toplevel()
        self._popup = ctk.CTkToplevel(root)
        self._popup.withdraw()
        self._popup.overrideredirect(True)
        self._popup.wm_attributes("-topmost", True)
        self._popup.geometry(f"{ancho}x{alto}+{x}+{y}")
        self._popup.configure(fg_color=COLORES["fondo_card"])
        self._popup.deiconify()
        self._popup.lift()

        if len(opciones) <= 6:
            contenedor_popup = ctk.CTkFrame(self._popup, fg_color="transparent")
        else:
            contenedor_popup = ctk.CTkScrollableFrame(self._popup, fg_color="transparent",
                                                      scrollbar_button_color=COLORES["rosa"])
        contenedor_popup.pack(fill="both", expand=True)

        for op in opciones:
            ctk.CTkButton(
                contenedor_popup, text=op, anchor="w", height=34,
                fg_color="transparent", hover_color=COLORES["rosa_suave"],
                text_color=COLORES["texto"], font=FUENTES["normal"],
                corner_radius=0,
                command=lambda v=op: self._seleccionar(v),
            ).pack(fill="x")

    def _seleccionar(self, valor: str):
        self.set(valor)
        self._cerrar_popup()
        self._entry.focus_set()

    def _foco_popup(self):
        if self._popup:
            try:
                self._popup.focus_set()
            except Exception:
                pass

    def _cerrar_popup(self):
        if self._popup:
            try:
                self._popup.destroy()
            except Exception:
                pass
            self._popup = None


# ------------------------------------------------------------------ #
#  Selector de fecha (calendario emergente) y de hora (dropdowns)      #
# ------------------------------------------------------------------ #

_MESES_ES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


class _SelectorFecha(ctk.CTkFrame):
    """Botón que muestra la fecha elegida y abre un mini calendario emergente
    para seleccionarla con el mouse, en vez de escribirla a mano."""

    def __init__(self, parent, fecha_inicial: date, ancho=170, **kwargs):
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self._fecha = fecha_inicial
        self._mes_actual = fecha_inicial.replace(day=1)
        self._popup = None

        self._boton = ctk.CTkButton(
            self, text=self._texto(), anchor="w",
            width=ancho, height=36,
            fg_color=COLORES["fondo_input"],
            hover_color=COLORES["rosa_suave"],
            text_color=COLORES["texto"],
            border_color=COLORES["borde"], border_width=1,
            font=FUENTES["normal"], corner_radius=8,
            command=self._abrir_popup,
        )
        self._boton.pack()

    def _texto(self) -> str:
        return "📅  " + self._fecha.strftime("%Y-%m-%d")

    def get(self) -> str:
        return self._fecha.strftime("%Y-%m-%d")

    def set_date(self, fecha: date):
        self._fecha = fecha
        self._mes_actual = fecha.replace(day=1)
        self._boton.configure(text=self._texto())

    def _abrir_popup(self):
        self._cerrar_popup()
        root = self._boton.winfo_toplevel()
        self._boton.update_idletasks()
        x = self._boton.winfo_rootx()
        y = self._boton.winfo_rooty() + self._boton.winfo_height() + 2

        self._popup = ctk.CTkToplevel(root)
        self._popup.withdraw()
        self._popup.overrideredirect(True)
        self._popup.wm_attributes("-topmost", True)
        self._popup.configure(fg_color=COLORES["fondo_card"])
        self._popup.geometry(f"250x290+{x}+{y}")

        self._cal_container = ctk.CTkFrame(
            self._popup, fg_color="transparent",
            border_width=1, border_color=COLORES["borde"],
        )
        self._cal_container.pack(fill="both", expand=True)
        self._render_calendario()

        self._popup.deiconify()
        self._popup.lift()
        self._popup.bind("<FocusOut>", lambda _: self.after(150, self._cerrar_popup))
        self._popup.focus_force()

    def _render_calendario(self):
        for w in self._cal_container.winfo_children():
            w.destroy()

        nav = ctk.CTkFrame(self._cal_container, fg_color="transparent")
        nav.pack(fill="x", padx=8, pady=(8, 4))
        nav.columnconfigure(1, weight=1)

        ctk.CTkButton(nav, text="<", width=28, height=28,
                      fg_color="transparent", hover_color=COLORES["rosa_suave"],
                      text_color=COLORES["rosa"], corner_radius=8,
                      command=self._mes_anterior).grid(row=0, column=0)

        ctk.CTkLabel(
            nav, text=_MESES_ES[self._mes_actual.month - 1] + " " + str(self._mes_actual.year),
            font=FUENTES["subtitulo"], text_color=COLORES["texto"],
        ).grid(row=0, column=1)

        ctk.CTkButton(nav, text=">", width=28, height=28,
                      fg_color="transparent", hover_color=COLORES["rosa_suave"],
                      text_color=COLORES["rosa"], corner_radius=8,
                      command=self._mes_siguiente).grid(row=0, column=2)

        cab = ctk.CTkFrame(self._cal_container, fg_color="transparent")
        cab.pack(fill="x", padx=8)
        for i in range(7):
            cab.columnconfigure(i, weight=1)
        for i, d in enumerate(["Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"]):
            ctk.CTkLabel(cab, text=d, height=20, font=FUENTES["small"],
                         text_color=COLORES["texto_suave"]).grid(row=0, column=i)

        grid = ctk.CTkFrame(self._cal_container, fg_color="transparent")
        grid.pack(fill="x", padx=8, pady=(0, 8))
        for i in range(7):
            grid.columnconfigure(i, weight=1)

        cal = calendar.monthcalendar(self._mes_actual.year, self._mes_actual.month)
        hoy = date.today()
        for fi, semana in enumerate(cal):
            for ci, num_dia in enumerate(semana):
                if num_dia == 0:
                    ctk.CTkLabel(grid, text="", height=28).grid(
                        row=fi, column=ci, padx=1, pady=1)
                    continue

                fecha_dia = date(self._mes_actual.year, self._mes_actual.month, num_dia)
                es_sel = fecha_dia == self._fecha
                es_hoy = fecha_dia == hoy

                if es_sel:
                    fg, tc = COLORES["rosa"], COLORES["texto_blanco"]
                elif es_hoy:
                    fg, tc = COLORES["rosa_suave"], COLORES["rosa"]
                else:
                    fg, tc = "transparent", COLORES["texto"]

                lbl = ctk.CTkLabel(
                    grid, text=str(num_dia), height=28, fg_color=fg, text_color=tc,
                    corner_radius=14, font=FUENTES["small"], cursor="hand2",
                )
                lbl.grid(row=fi, column=ci, sticky="ew", padx=1, pady=1)
                lbl.bind("<Button-1>", lambda _e, fd=fecha_dia: self._elegir(fd))

        ctk.CTkButton(
            self._cal_container, text="Hoy", height=28,
            fg_color="transparent", hover_color=COLORES["rosa_suave"],
            text_color=COLORES["rosa"], border_width=1, border_color=COLORES["rosa"],
            corner_radius=8, command=lambda: self._elegir(date.today()),
        ).pack(pady=(0, 8))

    def _elegir(self, fecha_dia: date):
        self.set_date(fecha_dia)
        self._cerrar_popup()

    def _mes_anterior(self):
        if self._mes_actual.month == 1:
            self._mes_actual = self._mes_actual.replace(year=self._mes_actual.year - 1, month=12)
        else:
            self._mes_actual = self._mes_actual.replace(month=self._mes_actual.month - 1)
        self._render_calendario()

    def _mes_siguiente(self):
        if self._mes_actual.month == 12:
            self._mes_actual = self._mes_actual.replace(year=self._mes_actual.year + 1, month=1)
        else:
            self._mes_actual = self._mes_actual.replace(month=self._mes_actual.month + 1)
        self._render_calendario()

    def _cerrar_popup(self):
        if self._popup:
            try:
                self._popup.destroy()
            except Exception:
                pass
            self._popup = None


class _SelectorHora(ctk.CTkFrame):
    """Hora y minuto elegibles con dos desplegables, en vez de un campo de texto libre."""

    def __init__(self, parent, hora_inicial="10:30", **kwargs):
        super().__init__(parent, fg_color="transparent", corner_radius=0)

        h_str, m_str = hora_inicial.split(":")

        horas = [f"{h:02d}" for h in range(24)]
        if h_str not in horas:
            horas = sorted(set(horas) | {h_str})

        minutos = [f"{m:02d}" for m in range(0, 60, 5)]
        if m_str not in minutos:
            minutos = sorted(set(minutos) | {m_str})

        sel_h, self._var_h = selector(self, valores=horas, ancho=64)
        self._var_h.set(h_str)
        sel_h.pack(side="left")

        ctk.CTkLabel(self, text=":", font=FUENTES["subtitulo"],
                     text_color=COLORES["texto"]).pack(side="left", padx=4)

        sel_m, self._var_m = selector(self, valores=minutos, ancho=64)
        self._var_m.set(m_str)
        sel_m.pack(side="left")

    def get(self) -> str:
        return self._var_h.get() + ":" + self._var_m.get()

    def set(self, hhmm: str):
        h, m = hhmm.split(":")
        self._var_h.set(h)
        self._var_m.set(m)


# ------------------------------------------------------------------ #
#  Formulario turno                                                    #
# ------------------------------------------------------------------ #

class _FormTurno(ctk.CTkToplevel):

    def __init__(self, parent, turno_service, cli_service, cfg_service,
                 fecha_inicial=None, turno=None, al_guardar=None):
        super().__init__(parent)
        self._turno_service = turno_service
        self._cli_service   = cli_service
        self._cfg_service   = cfg_service
        self._turno         = turno
        self._fecha_inicial = fecha_inicial or date.today()
        self._al_guardar    = al_guardar
        self._es_edicion    = turno is not None
        self._grupos_empleados = []

        self.title("Editar turno" if self._es_edicion else "Nuevo turno")
        self.geometry("500x680")
        self.minsize(460, 600)
        self.resizable(True, True)
        self.configure(fg_color=COLORES["fondo"])
        self._cargar_datos()
        self._construir()
        if self._es_edicion:
            self._rellenar()
        else:
            self._agregar_grupo_empleado()
        self.after(100, self._forzar_foco)

    def _forzar_foco(self):
        self.lift()
        self.grab_set()
        self.focus_force()

    def _cargar_datos(self):
        clientes  = self._cli_service.obtener_todos()
        empleadas = self._cfg_service.obtener_empleadas()
        servicios = self._cfg_service.obtener_servicios()
        self._clientes_map    = {c["nombre"]: c["id"] for c in clientes}
        self._empleadas_map   = {e["nombre"]: e["id"] for e in empleadas if e["activa"]}
        self._servicios_map   = {s["nombre"]: s["id"] for s in servicios if s["activo"]}
        self._servicios_precio = {s["nombre"]: s["precio"] for s in servicios if s["activo"]}
        self._servicios_nombres = list(self._servicios_map.keys())

    def _construir(self):
        pad = {"padx": 28, "pady": 5}

        btns = ctk.CTkFrame(self, fg_color=COLORES["fondo_card"], corner_radius=0)
        btns.pack(fill="x")
        boton_secundario(btns, "Cancelar", comando=self.destroy, ancho=160).pack(
            side="left", padx=28, pady=12)
        boton_primario(btns, "Guardar", comando=self._guardar, ancho=160).pack(
            side="right", padx=28, pady=12)
        separador(self).pack(fill="x")

        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORES["rosa"],
            scrollbar_button_hover_color=COLORES["rosa_hover"],
        )
        self._scroll.pack(fill="both", expand=True)
        self._scroll.columnconfigure(0, weight=1)

        etiqueta_suave(self._scroll, "Cliente *").pack(anchor="w", padx=28, pady=(14, 2))
        self._buscador_cli = _BuscadorConDropdown(
            self._scroll,
            opciones=list(self._clientes_map.keys()),
            placeholder="Buscar cliente...",
            ancho=444,
        )
        self._buscador_cli.pack(padx=28, pady=5)

        etiqueta_suave(self._scroll, "Empleados y servicios *").pack(anchor="w", padx=28, pady=(8, 2))

        self._frame_grupos = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._frame_grupos.pack(fill="x", padx=28)
        self._frame_grupos.columnconfigure(0, weight=1)

        boton_secundario(
            self._scroll, "+ Agregar empleado",
            comando=self._agregar_grupo_empleado, ancho=200,
        ).pack(anchor="w", padx=28, pady=(4, 0))

        self._lbl_total = ctk.CTkLabel(
            self._scroll, text="Total: $0",
            font=FUENTES["subtitulo"], text_color=COLORES["rosa"], anchor="w",
        )
        self._lbl_total.pack(anchor="w", padx=28, pady=(4, 0))

        etiqueta_suave(self._scroll, "Fecha y hora").pack(anchor="w", padx=28, pady=(8, 2))
        fila_dt = ctk.CTkFrame(self._scroll, fg_color="transparent")
        fila_dt.pack(**pad)

        self._fecha = _SelectorFecha(fila_dt, fecha_inicial=self._fecha_inicial)
        self._fecha.pack(side="left")

        self._hora = _SelectorHora(fila_dt, hora_inicial="10:30")
        self._hora.pack(side="left", padx=(16, 0))

        self._var_estado = ctk.StringVar(value="pendiente")
        if self._es_edicion:
            etiqueta_suave(self._scroll, "Estado").pack(anchor="w", padx=28, pady=(8, 2))
            ctk.CTkOptionMenu(
                self._scroll, values=TurnoService.ESTADOS,
                variable=self._var_estado,
                width=444, height=36,
                fg_color=COLORES["rosa"], button_color=COLORES["rosa_hover"],
                button_hover_color=COLORES["rosa_hover"],
                text_color=COLORES["texto_blanco"],
                font=FUENTES["normal"], corner_radius=8,
            ).pack(**pad)

        etiqueta_suave(self._scroll, "Notas").pack(anchor="w", padx=28, pady=(8, 2))
        self._notas = ctk.CTkTextbox(
            self._scroll, width=444, height=80,
            fg_color=COLORES["fondo_input"], border_color=COLORES["borde"],
            border_width=2, text_color=COLORES["texto"],
            font=FUENTES["normal"], corner_radius=8,
        )
        self._notas.pack(padx=28, pady=(0, 20))

    def _agregar_grupo_empleado(self, empleada_nombre=""):
        grupo_frame = ctk.CTkFrame(self._frame_grupos, fg_color=COLORES["fondo_card"],
                                   corner_radius=10, border_width=1,
                                   border_color=COLORES["borde"])
        grupo_frame.pack(fill="x", pady=5)
        grupo_frame.columnconfigure(0, weight=1)

        cab = ctk.CTkFrame(grupo_frame, fg_color="transparent")
        cab.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
        cab.columnconfigure(0, weight=1)

        var_emp = ctk.StringVar(value=empleada_nombre)
        combo_emp = ctk.CTkComboBox(
            cab, values=list(self._empleadas_map.keys()),
            variable=var_emp, width=0, height=36,
            fg_color=COLORES["fondo_input"], border_color=COLORES["borde"],
            button_color=COLORES["rosa"], button_hover_color=COLORES["rosa_hover"],
            text_color=COLORES["texto"], font=FUENTES["normal"], corner_radius=8,
        )
        combo_emp.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        btn_quitar_grupo = ctk.CTkButton(
            cab, text="✕ Quitar empleado", width=0, height=32,
            fg_color="transparent", hover_color="#FDECEA",
            text_color=COLORES["error"], font=FUENTES["small"],
            corner_radius=6,
        )
        btn_quitar_grupo.grid(row=0, column=1)

        frame_servicios = ctk.CTkFrame(grupo_frame, fg_color="transparent")
        frame_servicios.grid(row=1, column=0, sticky="ew", padx=10)
        frame_servicios.columnconfigure(0, weight=1)

        lbl_subtotal = ctk.CTkLabel(
            grupo_frame, text="Subtotal: $0",
            font=FUENTES["small"], text_color=COLORES["texto_suave"], anchor="w",
        )
        lbl_subtotal.grid(row=3, column=0, sticky="w", padx=10, pady=(0, 10))

        grupo = {
            "frame": grupo_frame, "var_emp": var_emp, "combo_emp": combo_emp,
            "frame_servicios": frame_servicios, "filas_servicios": [],
            "lbl_subtotal": lbl_subtotal, "btn_quitar_grupo": btn_quitar_grupo,
        }
        self._grupos_empleados.append(grupo)

        btn_agregar_srv = boton_secundario(
            grupo_frame, "+ Agregar servicio",
            comando=lambda: self._agregar_fila_servicio(grupo), ancho=180,
        )
        btn_agregar_srv.grid(row=2, column=0, sticky="w", padx=10, pady=(2, 6))

        def _quitar_grupo(g=grupo):
            if len(self._grupos_empleados) <= 1:
                mostrar_error("Error", "Debe haber al menos un empleado.")
                return
            g["frame"].destroy()
            self._grupos_empleados.remove(g)
            self._actualizar_total()

        btn_quitar_grupo.configure(command=_quitar_grupo)

        self._agregar_fila_servicio(grupo)
        return grupo

    def _agregar_fila_servicio(self, grupo, servicio_nombre="", precio_val=""):
        fila = ctk.CTkFrame(grupo["frame_servicios"], fg_color=COLORES["rosa_suave"],
                            corner_radius=8)
        fila.pack(fill="x", pady=3)
        fila.columnconfigure(0, weight=2)
        fila.columnconfigure(1, weight=1)

        var_srv = ctk.StringVar(value=servicio_nombre)

        buscador = _BuscadorConDropdown(
            fila,
            opciones=self._servicios_nombres,
            placeholder="Buscar servicio...",
            ancho=0,
            var_externa=var_srv,
        )
        buscador.grid(row=0, column=0, sticky="ew", padx=(8, 4), pady=6)

        e_precio = campo_texto(fila, placeholder="$", ancho=0)
        e_precio.grid(row=0, column=1, sticky="ew", padx=(0, 4), pady=6)
        e_precio.bind("<KeyRelease>", lambda _: self._actualizar_total())

        def _al_cambiar_srv(*_):
            nombre = var_srv.get()
            if nombre in self._servicios_precio:
                p = self._servicios_precio[nombre]
                e_precio.delete(0, "end")
                e_precio.insert(0, str(int(p)))
            self._actualizar_total()

        var_srv.trace_add("write", _al_cambiar_srv)

        if servicio_nombre:
            buscador.set(servicio_nombre)
        if precio_val:
            e_precio.delete(0, "end")
            e_precio.insert(0, str(precio_val))

        btn_quitar = ctk.CTkButton(
            fila, text="✕", width=28, height=28,
            fg_color="transparent", hover_color="#FDECEA",
            text_color=COLORES["error"], font=FUENTES["normal"],
            corner_radius=6,
        )
        btn_quitar.grid(row=0, column=2, padx=(0, 6), pady=6)

        info = {"frame": fila, "var_srv": var_srv, "e_precio": e_precio}
        grupo["filas_servicios"].append(info)

        def _quitar(i=info, g=grupo):
            if len(g["filas_servicios"]) <= 1:
                mostrar_error("Error", "Cada empleado debe tener al menos un servicio.")
                return
            i["frame"].destroy()
            g["filas_servicios"].remove(i)
            self._actualizar_total()

        btn_quitar.configure(command=_quitar)
        self._actualizar_total()

    def _actualizar_total(self):
        total = 0.0
        for grupo in self._grupos_empleados:
            subtotal = 0.0
            for info in grupo["filas_servicios"]:
                try:
                    subtotal += float(info["e_precio"].get().strip() or 0)
                except ValueError:
                    pass
            grupo["lbl_subtotal"].configure(text="Subtotal: $" + str(int(subtotal)))
            total += subtotal
        self._lbl_total.configure(text="Total: $" + str(int(total)))

    def _rellenar(self):
        t = self._turno
        for nombre, id_ in self._clientes_map.items():
            if id_ == t["cliente_id"]:
                self._buscador_cli.set(nombre)
                break

        nombres_emp_por_id = {id_: nombre for nombre, id_ in self._empleadas_map.items()}

        def _nombre_servicio(servicio_id):
            for n, sid in self._servicios_map.items():
                if sid == servicio_id:
                    return n
            return ""

        servicios = t.get("servicios", [])
        if not servicios:
            servicios = [{
                "servicio_id": t.get("servicio_id"),
                "empleada_id": t.get("empleada_id"),
                "precio": t.get("servicio_precio", 0),
            }]

        # Agrupar servicios por empleada, preservando el orden de aparicion
        grupos_por_empleada = {}
        orden_empleadas = []
        for s in servicios:
            emp_id = s.get("empleada_id")
            if emp_id not in grupos_por_empleada:
                grupos_por_empleada[emp_id] = []
                orden_empleadas.append(emp_id)
            grupos_por_empleada[emp_id].append(s)

        for emp_id in orden_empleadas:
            nombre_emp = nombres_emp_por_id.get(emp_id, "")
            grupo = self._agregar_grupo_empleado(nombre_emp)
            primer_fila = grupo["filas_servicios"][0]
            primer_fila["frame"].destroy()
            grupo["filas_servicios"].clear()
            for s in grupos_por_empleada[emp_id]:
                nombre_srv = _nombre_servicio(s["servicio_id"])
                self._agregar_fila_servicio(grupo, nombre_srv, int(s["precio"]))

        fh = t["fecha_hora"]
        self._fecha.set_date(datetime.strptime(fh[:10], "%Y-%m-%d").date())
        self._hora.set(fh[11:16])
        self._var_estado.set(t["estado"])
        if t["notas"]:
            self._notas.delete("1.0", "end")
            self._notas.insert("1.0", t["notas"])

    def _guardar(self):
        nombre_cli = self._buscador_cli.get().strip()
        fecha_txt  = self._fecha.get()
        hora_txt   = self._hora.get()
        notas      = self._notas.get("1.0", "end").strip()

        if not nombre_cli or nombre_cli not in self._clientes_map:
            mostrar_error("Error", "Selecciona un cliente valido.")
            return
        if not self._grupos_empleados:
            mostrar_error("Error", "Agrega al menos un empleado con sus servicios.")
            return

        servicios = []
        empleadas_usadas = set()
        for grupo in self._grupos_empleados:
            nombre_emp = grupo["var_emp"].get().strip()
            if not nombre_emp or nombre_emp not in self._empleadas_map:
                mostrar_error("Error", "Selecciona una empleada valida en cada tarjeta.")
                return
            emp_id = self._empleadas_map[nombre_emp]
            if emp_id in empleadas_usadas:
                mostrar_error(
                    "Error",
                    "Ya agregaste a " + nombre_emp + ". "
                    "Agregá sus servicios en su misma tarjeta."
                )
                return
            empleadas_usadas.add(emp_id)

            if not grupo["filas_servicios"]:
                mostrar_error("Error", "Cada empleado debe tener al menos un servicio.")
                return

            for info in grupo["filas_servicios"]:
                nombre_srv = info["var_srv"].get().strip()
                if not nombre_srv or nombre_srv not in self._servicios_map:
                    mostrar_error("Error", "Selecciona un servicio valido en cada fila.")
                    return
                try:
                    precio = float(info["e_precio"].get().strip() or 0)
                except ValueError:
                    mostrar_error("Error", "El precio debe ser un numero.")
                    return
                servicios.append({
                    "servicio_id": self._servicios_map[nombre_srv],
                    "empleada_id": emp_id,
                    "precio": precio,
                })

        if not servicios:
            mostrar_error("Error", "Agrega al menos un servicio.")
            return

        fecha_hora = fecha_txt + " " + hora_txt
        cli_id = self._clientes_map[nombre_cli]

        if self._es_edicion:
            ok, msg = self._turno_service.actualizar(
                self._turno["id"], cli_id, servicios,
                fecha_hora, self._var_estado.get(), notas)
            resultado = ok
        else:
            ok, msg, resultado = self._turno_service.crear(
                cli_id, servicios, fecha_hora, notas)

        if not ok and resultado == -1:
            if confirmar("Turno solapado", msg):
                ok, msg, resultado = self._turno_service.crear(
                    cli_id, servicios, fecha_hora, notas, forzar=True)
            else:
                return

        if not ok:
            mostrar_error("Error", msg)
            return

        mostrar_exito("Listo", "Turno guardado correctamente.")
        self.destroy()
        if self._al_guardar:
            self._al_guardar()