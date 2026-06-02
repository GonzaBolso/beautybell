import customtkinter as ctk
from datetime import date, datetime, timedelta
import calendar
from ui.vista_base import VistaBase
from ui.tema import COLORES, FUENTES
from ui.widgets import (
    boton_primario, boton_secundario, boton_peligro,
    campo_texto, etiqueta, etiqueta_suave, card,
    separador, mostrar_error, mostrar_exito, confirmar
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
        self.contenido.columnconfigure(1, weight=2)
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
        for d in ["Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"]:
            ctk.CTkLabel(cab_sem, text=d, width=36, height=24,
                         font=FUENTES["small"],
                         text_color=COLORES["texto_suave"]).pack(side="left", expand=True)

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

        for semana in cal:
            fila = ctk.CTkFrame(self._cal_frame, fg_color="transparent")
            fila.pack(fill="x", pady=1)
            for num_dia in semana:
                if num_dia == 0:
                    ctk.CTkFrame(fila, width=36, height=36,
                                 fg_color="transparent").pack(side="left", expand=True)
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
                    fg, tc = "transparent", COLORES["texto"]

                txt = str(num_dia) + (" •" if tiene and not es_sel else "")
                ctk.CTkButton(
                    fila, text=txt, width=36, height=36,
                    fg_color=fg, hover_color=COLORES["rosa_suave"],
                    text_color=tc, font=FUENTES["small"],
                    corner_radius=18,
                    command=lambda fd=fecha_dia: self._seleccionar_dia(fd),
                ).pack(side="left", expand=True, padx=1)

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
        self._lista_turnos.pack(fill="both", expand=True, padx=12, pady=(0, 12))
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
            ).pack(fill="x", pady=4)

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
#  Tarjeta de turno                                                    #
# ------------------------------------------------------------------ #

class _TarjetaTurno(ctk.CTkFrame):

    def __init__(self, parent, turno, al_cambiar_estado,
                 al_cobrar, al_editar, al_eliminar):
        super().__init__(parent, fg_color=COLORES["fondo_card"],
                         corner_radius=10, border_width=1,
                         border_color=COLORES["borde"])

        estado  = turno["estado"]
        colores = ESTADO_COLORES.get(estado, ("#F8F9FA", "#495057"))

        franja = ctk.CTkFrame(self, width=6, fg_color=colores[1], corner_radius=0)
        franja.pack(side="left", fill="y")
        franja.pack_propagate(False)

        cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        cuerpo.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        # Fila 1: hora + cliente + badge
        fila1 = ctk.CTkFrame(cuerpo, fg_color="transparent")
        fila1.pack(fill="x")
        hora = turno["fecha_hora"][11:16]
        ctk.CTkLabel(fila1, text=hora, font=FUENTES["subtitulo"],
                     text_color=COLORES["rosa"]).pack(side="left")
        ctk.CTkLabel(fila1, text=turno["cliente_nombre"],
                     font=FUENTES["normal"],
                     text_color=COLORES["texto"]).pack(side="left", padx=(10, 0))
        ctk.CTkLabel(fila1,
                     text=" " + ESTADO_ETIQUETAS.get(estado, estado) + " ",
                     font=FUENTES["small"],
                     fg_color=colores[0], text_color=colores[1],
                     corner_radius=6).pack(side="right")

        # Fila 2: servicio + empleada + precio
        fila2 = ctk.CTkFrame(cuerpo, fg_color="transparent")
        fila2.pack(fill="x", pady=(4, 0))
        ctk.CTkLabel(fila2, text=turno["servicio_nombre"],
                     font=FUENTES["small"],
                     text_color=COLORES["texto_suave"]).pack(side="left")
        ctk.CTkLabel(fila2, text="·  " + turno["empleada_nombre"],
                     font=FUENTES["small"],
                     text_color=COLORES["texto_suave"]).pack(side="left", padx=(8, 0))
        ctk.CTkLabel(fila2, text="$" + str(int(turno["servicio_precio"])),
                     font=FUENTES["small"],
                     text_color=COLORES["texto"]).pack(side="right")

        if turno["notas"]:
            ctk.CTkLabel(cuerpo, text=turno["notas"],
                         font=FUENTES["small"],
                         text_color=COLORES["texto_suave"],
                         anchor="w").pack(fill="x", pady=(4, 0))

        separador(cuerpo).pack(fill="x", pady=(8, 6))

        # Botones de accion
        acc = ctk.CTkFrame(cuerpo, fg_color="transparent")
        acc.pack(fill="x")

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

        self.title("Completar y cobrar turno")
        self.geometry("400x330")
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

        hora = turno["fecha_hora"][11:16]
        etiqueta(self, turno["cliente_nombre"] + "  -  " + hora,
                 fuente="subtitulo").pack(anchor="w", padx=20, pady=(16, 2))
        etiqueta_suave(self, turno["servicio_nombre"]).pack(anchor="w", padx=20)
        separador(self).pack(fill="x", padx=20, pady=12)

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=20)
        form.columnconfigure(1, weight=1)

        etiqueta_suave(form, "Monto ($)").grid(row=0, column=0, sticky="w", pady=8)
        self._monto = campo_texto(form, ancho=0)
        self._monto.insert(0, str(int(turno["servicio_precio"])))
        self._monto.grid(row=0, column=1, sticky="ew", padx=(12, 0), pady=8)

        etiqueta_suave(form, "Metodo de pago").grid(row=1, column=0, sticky="w", pady=8)
        nombres = list(self._metodos_map.keys())
        self._var_mp = ctk.StringVar(value=nombres[0] if nombres else "")
        ctk.CTkOptionMenu(
            form, values=nombres, variable=self._var_mp,
            width=0, height=36,
            fg_color=COLORES["rosa"], button_color=COLORES["rosa_hover"],
            button_hover_color=COLORES["rosa_hover"],
            text_color=COLORES["texto_blanco"],
            font=FUENTES["normal"], corner_radius=8,
        ).grid(row=1, column=1, sticky="ew", padx=(12, 0), pady=8)

    def _confirmar(self):
        try:
            monto = float(self._monto.get().strip())
        except ValueError:
            mostrar_error("Error", "El monto debe ser un numero.")
            return

        mp_id = self._metodos_map.get(self._var_mp.get())
        self._turno_service.completar(self._turno["id"])
        self._caja_service.registrar_cobro_turno(
            turno_id=self._turno["id"],
            monto=monto,
            metodo_pago_id=mp_id,
            descripcion="Cobro: " + self._turno["cliente_nombre"]
                        + " - " + self._turno["servicio_nombre"]
                        + " - " + self._turno["empleada_nombre"],
        )
        mostrar_exito("Listo", "Turno completado y cobro registrado en caja.")
        self.destroy()
        if self._al_cobrar:
            self._al_cobrar()


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

        self.title("Editar turno" if self._es_edicion else "Nuevo turno")
        self.geometry("460x620")
        self.minsize(400, 560)
        self.resizable(True, True)
        self.configure(fg_color=COLORES["fondo"])
        self._cargar_datos()
        self._construir()
        if self._es_edicion:
            self._rellenar()
        self.after(100, self._forzar_foco)

    def _forzar_foco(self):
        self.lift()
        self.grab_set()
        self.focus_force()

    def _cargar_datos(self):
        clientes  = self._cli_service.obtener_todos()
        empleadas = self._cfg_service.obtener_empleadas()
        servicios = self._cfg_service.obtener_servicios()
        self._clientes_map  = {c["nombre"]: c["id"] for c in clientes}
        self._empleadas_map = {e["nombre"]: e["id"] for e in empleadas if e["activa"]}
        self._servicios_map = {s["nombre"]: s["id"] for s in servicios if s["activo"]}
        self._servicios_precio = {s["nombre"]: s["precio"] for s in servicios if s["activo"]}

    def _construir(self):
        pad = {"padx": 28, "pady": 5}

        # Botones arriba
        btns = ctk.CTkFrame(self, fg_color=COLORES["fondo_card"], corner_radius=0)
        btns.pack(fill="x")
        boton_secundario(btns, "Cancelar", comando=self.destroy, ancho=160).pack(
            side="left", padx=28, pady=12)
        boton_primario(btns, "Guardar", comando=self._guardar, ancho=160).pack(
            side="right", padx=28, pady=12)
        separador(self).pack(fill="x")

        # Scroll para el contenido
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORES["rosa"],
            scrollbar_button_hover_color=COLORES["rosa_hover"],
        )
        scroll.pack(fill="both", expand=True)
        scroll.columnconfigure(0, weight=1)

        # Cliente
        etiqueta_suave(scroll, "Cliente *").pack(anchor="w", padx=28, pady=(14, 2))
        self._var_cli = ctk.StringVar()
        self._combo_cli = ctk.CTkComboBox(
            scroll, values=list(self._clientes_map.keys()),
            variable=self._var_cli, width=404, height=36,
            fg_color=COLORES["fondo_input"], border_color=COLORES["borde"],
            button_color=COLORES["rosa"], button_hover_color=COLORES["rosa_hover"],
            text_color=COLORES["texto"], font=FUENTES["normal"], corner_radius=8,
        )
        self._combo_cli.pack(**pad)

        # Empleada
        etiqueta_suave(scroll, "Empleada *").pack(anchor="w", padx=28, pady=(8, 2))
        self._var_emp = ctk.StringVar()
        self._combo_emp = ctk.CTkComboBox(
            scroll, values=list(self._empleadas_map.keys()),
            variable=self._var_emp, width=404, height=36,
            fg_color=COLORES["fondo_input"], border_color=COLORES["borde"],
            button_color=COLORES["rosa"], button_hover_color=COLORES["rosa_hover"],
            text_color=COLORES["texto"], font=FUENTES["normal"], corner_radius=8,
        )
        self._combo_emp.pack(**pad)

        # Servicio — al cambiar autocompleta precio
        etiqueta_suave(scroll, "Servicio *").pack(anchor="w", padx=28, pady=(8, 2))
        self._var_srv = ctk.StringVar()
        self._var_srv.trace_add("write", self._al_cambiar_servicio)
        self._combo_srv = ctk.CTkComboBox(
            scroll, values=list(self._servicios_map.keys()),
            variable=self._var_srv, width=404, height=36,
            fg_color=COLORES["fondo_input"], border_color=COLORES["borde"],
            button_color=COLORES["rosa"], button_hover_color=COLORES["rosa_hover"],
            text_color=COLORES["texto"], font=FUENTES["normal"], corner_radius=8,
        )
        self._combo_srv.pack(**pad)

        # Precio editable
        etiqueta_suave(scroll, "Precio ($)  — editable si hubo descuento").pack(
            anchor="w", padx=28, pady=(8, 2))
        self._precio = campo_texto(scroll, placeholder="0", ancho=404)
        self._precio.pack(**pad)

        # Fecha y hora precargadas
        etiqueta_suave(scroll, "Fecha (YYYY-MM-DD)").pack(anchor="w", padx=28, pady=(8, 2))
        fila_dt = ctk.CTkFrame(scroll, fg_color="transparent")
        fila_dt.pack(**pad)

        self._fecha = campo_texto(fila_dt, ancho=230)
        self._fecha.insert(0, self._fecha_inicial.strftime("%Y-%m-%d"))
        self._fecha.pack(side="left")

        etiqueta_suave(fila_dt, "Hora (HH:MM)").pack(side="left", padx=(16, 6))
        self._hora = campo_texto(fila_dt, ancho=100)
        self._hora.insert(0, "10:30")
        self._hora.pack(side="left")

        # Estado (solo edicion)
        self._var_estado = ctk.StringVar(value="pendiente")
        if self._es_edicion:
            etiqueta_suave(scroll, "Estado").pack(anchor="w", padx=28, pady=(8, 2))
            ctk.CTkOptionMenu(
                scroll, values=TurnoService.ESTADOS,
                variable=self._var_estado,
                width=404, height=36,
                fg_color=COLORES["rosa"], button_color=COLORES["rosa_hover"],
                button_hover_color=COLORES["rosa_hover"],
                text_color=COLORES["texto_blanco"],
                font=FUENTES["normal"], corner_radius=8,
            ).pack(**pad)

        # Notas
        etiqueta_suave(scroll, "Notas").pack(anchor="w", padx=28, pady=(8, 2))
        self._notas = ctk.CTkTextbox(
            scroll, width=404, height=80,
            fg_color=COLORES["fondo_input"], border_color=COLORES["borde"],
            border_width=2, text_color=COLORES["texto"],
            font=FUENTES["normal"], corner_radius=8,
        )
        self._notas.pack(padx=28, pady=(0, 20))

    def _al_cambiar_servicio(self, *_):
        nombre = self._var_srv.get()
        if nombre in self._servicios_precio:
            precio = self._servicios_precio[nombre]
            self._precio.delete(0, "end")
            self._precio.insert(0, str(int(precio)))

    def _rellenar(self):
        t = self._turno
        for nombre, id_ in self._clientes_map.items():
            if id_ == t["cliente_id"]:
                self._var_cli.set(nombre)
                break
        for nombre, id_ in self._empleadas_map.items():
            if id_ == t["empleada_id"]:
                self._var_emp.set(nombre)
                break
        for nombre, id_ in self._servicios_map.items():
            if id_ == t["servicio_id"]:
                self._var_srv.set(nombre)
                break
        # Precio del turno (del servicio actual)
        self._precio.delete(0, "end")
        self._precio.insert(0, str(int(t["servicio_precio"])))

        fh = t["fecha_hora"]
        self._fecha.delete(0, "end")
        self._fecha.insert(0, fh[:10])
        self._hora.delete(0, "end")
        self._hora.insert(0, fh[11:16])
        self._var_estado.set(t["estado"])
        if t["notas"]:
            self._notas.delete("1.0", "end")
            self._notas.insert("1.0", t["notas"])

    def _guardar(self):
        nombre_cli = self._var_cli.get().strip()
        nombre_emp = self._var_emp.get().strip()
        nombre_srv = self._var_srv.get().strip()
        fecha_txt  = self._fecha.get().strip()
        hora_txt   = self._hora.get().strip()
        notas      = self._notas.get("1.0", "end").strip()

        if not nombre_cli or nombre_cli not in self._clientes_map:
            mostrar_error("Error", "Selecciona un cliente valido.")
            return
        if not nombre_emp or nombre_emp not in self._empleadas_map:
            mostrar_error("Error", "Selecciona una empleada valida.")
            return
        if not nombre_srv or nombre_srv not in self._servicios_map:
            mostrar_error("Error", "Selecciona un servicio valido.")
            return
        if not hora_txt:
            mostrar_error("Error", "Ingresa la hora (HH:MM).")
            return

        fecha_hora = fecha_txt + " " + hora_txt
        cli_id = self._clientes_map[nombre_cli]
        emp_id = self._empleadas_map[nombre_emp]
        srv_id = self._servicios_map[nombre_srv]

        if self._es_edicion:
            ok, msg = self._turno_service.actualizar(
                self._turno["id"], cli_id, emp_id, srv_id,
                fecha_hora, self._var_estado.get(), notas)
            resultado = ok
        else:
            ok, msg, resultado = self._turno_service.crear(
                cli_id, emp_id, srv_id, fecha_hora, notas)

        if not ok and resultado == -1:
            if confirmar("Turno solapado", msg):
                ok, msg, resultado = self._turno_service.crear(
                    cli_id, emp_id, srv_id, fecha_hora, notas, forzar=True)
            else:
                return

        if not ok:
            mostrar_error("Error", msg)
            return

        mostrar_exito("Listo", "Turno guardado correctamente.")
        self.destroy()
        if self._al_guardar:
            self._al_guardar()