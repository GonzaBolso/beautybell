import customtkinter as ctk
from ui.vista_base import VistaBase
from ui.tema import COLORES, FUENTES
from ui.widgets import (
    boton_primario, boton_secundario, boton_peligro,
    campo_texto, etiqueta, etiqueta_suave, card,
    separador, mostrar_error, mostrar_exito, confirmar
)
from services.proveedor_service import ProveedorService


class ProveedoresView(VistaBase):

    def __init__(self, parent, **kwargs):
        self._service = ProveedorService()
        self._proveedor_seleccionado = None
        super().__init__(parent, titulo="Proveedores", **kwargs)

    # ------------------------------------------------------------------ #
    #  Construcción                                                        #
    # ------------------------------------------------------------------ #

    def _construir_contenido(self):
        self.contenido = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.contenido.pack(fill="both", expand=True, padx=24, pady=16)

        boton_primario(
            self._acciones, "＋  Nuevo proveedor",
            comando=self._abrir_form_nuevo, ancho=180
        ).pack()

        self.contenido.columnconfigure(0, weight=2)
        self.contenido.columnconfigure(1, weight=3)
        self.contenido.rowconfigure(0, weight=1)

        self._construir_panel_lista()
        self._construir_panel_detalle()
        self._cargar_proveedores()

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
            busq, placeholder="Buscar proveedor...", ancho=0
        )
        self._campo_busqueda.configure(textvariable=self._var_busqueda)
        self._campo_busqueda.grid(row=0, column=0, sticky="ew")

        separador(panel).grid(row=1, column=0, sticky="ew", padx=12)

        self._lista_frame = ctk.CTkScrollableFrame(
            panel, fg_color="transparent",
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
        self._panel_detalle.rowconfigure(1, weight=1)
        self._mostrar_detalle_vacio()

    # ------------------------------------------------------------------ #
    #  Lista                                                               #
    # ------------------------------------------------------------------ #

    def _cargar_proveedores(self, seleccionar_id=None):
        self._proveedores = self._service.obtener_todos()
        self._renderizar_lista(self._proveedores, seleccionar_id)

    def _filtrar(self):
        texto = self._var_busqueda.get().strip()
        resultados = self._service.buscar(texto) if texto else self._proveedores
        self._renderizar_lista(resultados)

    def _renderizar_lista(self, proveedores, seleccionar_id=None):
        for w in self._lista_frame.winfo_children():
            w.destroy()
        self._items_lista.clear()

        if not proveedores:
            etiqueta_suave(self._lista_frame, "Sin resultados").pack(pady=20)
            return

        for p in proveedores:
            item = _ItemProveedor(
                self._lista_frame,
                proveedor=p,
                seleccionado=(p["id"] == seleccionar_id),
                al_seleccionar=self._al_seleccionar,
            )
            item.pack(fill="x", padx=4, pady=2)
            self._items_lista.append(item)

    def _al_seleccionar(self, proveedor):
        self._proveedor_seleccionado = proveedor
        for item in self._items_lista:
            item.set_activo(item.proveedor["id"] == proveedor["id"])
        self._mostrar_detalle(proveedor)

    # ------------------------------------------------------------------ #
    #  Detalle                                                             #
    # ------------------------------------------------------------------ #

    def _mostrar_detalle_vacio(self):
        for w in self._panel_detalle.winfo_children():
            w.destroy()
        etiqueta_suave(
            self._panel_detalle,
            "Seleccioná un proveedor para ver el detalle"
        ).place(relx=0.5, rely=0.5, anchor="center")

    def _mostrar_detalle(self, proveedor):
        for w in self._panel_detalle.winfo_children():
            w.destroy()

        # --- Cabecera ---
        cab = ctk.CTkFrame(self._panel_detalle, fg_color="transparent")
        cab.pack(fill="x", padx=20, pady=(18, 0))

        etiqueta(cab, proveedor["nombre"], fuente="subtitulo").pack(side="left")
        boton_peligro(cab, "Eliminar",
                      comando=lambda: self._eliminar(proveedor),
                      ancho=90).pack(side="right")
        boton_primario(cab, "✎  Editar",
                       comando=lambda: self._abrir_form_editar(proveedor),
                       ancho=110).pack(side="right", padx=(0, 6))

        separador(self._panel_detalle).pack(fill="x", padx=20, pady=10)

        # --- Datos de contacto ---
        datos = ctk.CTkFrame(self._panel_detalle, fg_color="transparent")
        datos.pack(fill="x", padx=20)
        datos.columnconfigure(1, weight=1)

        campos = [
            ("Teléfono",  proveedor["telefono"] or "—"),
            ("Email",     proveedor["email"] or "—"),
            ("Dirección", proveedor["direccion"] or "—"),
        ]
        for i, (lbl, val) in enumerate(campos):
            etiqueta_suave(datos, lbl).grid(row=i, column=0, sticky="w", pady=3)
            etiqueta(datos, val).grid(row=i, column=1, sticky="w", padx=16, pady=3)

        if proveedor["notas"]:
            separador(self._panel_detalle).pack(fill="x", padx=20, pady=8)
            etiqueta_suave(self._panel_detalle, "Notas").pack(anchor="w", padx=20)
            etiqueta(self._panel_detalle, proveedor["notas"]).pack(
                anchor="w", padx=20, pady=(2, 0))

        separador(self._panel_detalle).pack(fill="x", padx=20, pady=10)

        # --- Sección productos ---
        cab_prod = ctk.CTkFrame(self._panel_detalle, fg_color="transparent")
        cab_prod.pack(fill="x", padx=20, pady=(0, 8))
        etiqueta(cab_prod, "Productos", fuente="subtitulo").pack(side="left")
        boton_secundario(
            cab_prod, "＋  Producto",
            comando=lambda: self._abrir_form_producto(proveedor),
            ancho=130
        ).pack(side="right")

        # Lista de productos scrollable
        prod_frame = ctk.CTkScrollableFrame(
            self._panel_detalle,
            fg_color="transparent",
            scrollbar_button_color=COLORES["rosa"],
            scrollbar_button_hover_color=COLORES["rosa_hover"],
        )
        prod_frame.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        prod_frame.columnconfigure(0, weight=1)

        self._prod_frame = prod_frame
        self._cargar_productos(proveedor)

    def _cargar_productos(self, proveedor):
        for w in self._prod_frame.winfo_children():
            w.destroy()

        productos = self._service.obtener_productos(proveedor["id"])

        if not productos:
            etiqueta_suave(self._prod_frame,
                           "Sin productos registrados").pack(pady=12)
            return

        # Encabezado con grid — mismos pesos que _FilaProducto
        enc = ctk.CTkFrame(self._prod_frame, fg_color=COLORES["rosa_suave"],
                           corner_radius=6)
        enc.pack(fill="x", pady=(0, 4))
        enc.columnconfigure(0, weight=4)
        enc.columnconfigure(1, weight=2)
        enc.columnconfigure(2, weight=2)
        enc.columnconfigure(3, weight=1)
        enc.columnconfigure(4, weight=2)

        for col, txt in enumerate(["Producto", "Costo", "Venta", "Stock", ""]):
            ctk.CTkLabel(
                enc, text=txt,
                font=FUENTES["small"],
                text_color=COLORES["rosa"],
                anchor="w",
            ).grid(row=0, column=col, sticky="ew",
                   padx=(10 if col == 0 else 4, 4), pady=6)

        for p in productos:
            fila = _FilaProducto(
                self._prod_frame,
                producto=p,
                al_editar=lambda prod=p: self._abrir_form_producto(proveedor, prod),
                al_eliminar=lambda prod=p: self._eliminar_producto(proveedor, prod),
            )
            fila.pack(fill="x", pady=1)

    # ------------------------------------------------------------------ #
    #  ABM Proveedores                                                     #
    # ------------------------------------------------------------------ #

    def _abrir_form_nuevo(self):
        _FormProveedor(self, service=self._service, al_guardar=self._al_guardar_proveedor)

    def _abrir_form_editar(self, proveedor):
        _FormProveedor(self, service=self._service,
                       proveedor=proveedor, al_guardar=self._al_guardar_proveedor)

    def _al_guardar_proveedor(self, proveedor_id):
        self._cargar_proveedores(seleccionar_id=proveedor_id)
        for item in self._items_lista:
            if item.proveedor["id"] == proveedor_id:
                self._al_seleccionar(item.proveedor)
                break

    def _eliminar(self, proveedor):
        if confirmar("Eliminar proveedor",
                     f"¿Eliminás a {proveedor['nombre']}?\nEsta acción no se puede deshacer."):
            try:
                self._service.eliminar(proveedor["id"])
                self._proveedor_seleccionado = None
                self._mostrar_detalle_vacio()
                self._cargar_proveedores()
            except Exception as e:
                if "FOREIGN KEY" in str(e) or "foreign key" in str(e).lower():
                    mostrar_error("No se puede eliminar",
                                  f"{proveedor['nombre']} tiene productos o compras asociadas.\n"
                                  "Primero eliminá esos registros.")
                else:
                    mostrar_error("Error", str(e))

    # ------------------------------------------------------------------ #
    #  ABM Productos                                                       #
    # ------------------------------------------------------------------ #

    def _abrir_form_producto(self, proveedor, producto=None):
        _FormProducto(
            self,
            service=self._service,
            proveedor=proveedor,
            producto=producto,
            al_guardar=lambda: self._cargar_productos(proveedor),
        )

    def _eliminar_producto(self, proveedor, producto):
        if confirmar("Eliminar producto",
                     f"¿Eliminás '{producto['nombre']}'?"):
            try:
                self._service.actualizar_producto(
                    producto["id"], producto["nombre"],
                    producto["proveedor_id"], producto["categoria"],
                    producto["precio_costo"], producto["precio_venta"], 0
                )
                # Eliminación real
                self._service._prod_repo.eliminar(producto["id"])
                self._cargar_productos(proveedor)
            except Exception as e:
                mostrar_error("Error", str(e))

    def refrescar(self):
        self._cargar_proveedores()


# ------------------------------------------------------------------ #
#  Item de lista                                                       #
# ------------------------------------------------------------------ #

class _ItemProveedor(ctk.CTkFrame):

    def __init__(self, parent, proveedor, seleccionado, al_seleccionar):
        super().__init__(
            parent,
            fg_color=COLORES["rosa_suave"] if seleccionado else "transparent",
            corner_radius=8,
            cursor="hand2",
        )
        self.proveedor = proveedor
        self._al_seleccionar = al_seleccionar
        self.columnconfigure(0, weight=1)

        lbl_nombre = ctk.CTkLabel(
            self, text=proveedor["nombre"],
            font=FUENTES["normal"],
            text_color=COLORES["rosa"] if seleccionado else COLORES["texto"],
            anchor="w",
        )
        lbl_nombre.grid(row=0, column=0, sticky="w", padx=12, pady=(8, 2))

        tel = proveedor["telefono"] or "Sin teléfono"
        lbl_tel = ctk.CTkLabel(
            self, text=tel,
            font=FUENTES["small"],
            text_color=COLORES["texto_suave"],
            anchor="w",
        )
        lbl_tel.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 8))

        for w in [self, lbl_nombre, lbl_tel]:
            w.bind("<Button-1>", lambda _e: self._al_seleccionar(self.proveedor))

    def set_activo(self, activo):
        self.configure(fg_color=COLORES["rosa_suave"] if activo else "transparent")
        for w in self.winfo_children():
            if isinstance(w, ctk.CTkLabel):
                es_nombre = w.cget("font") == FUENTES["normal"]
                w.configure(
                    text_color=COLORES["rosa"] if (activo and es_nombre)
                    else COLORES["texto_suave"] if not es_nombre
                    else COLORES["texto"]
                )


# ------------------------------------------------------------------ #
#  Fila de producto en tabla                                           #
# ------------------------------------------------------------------ #

class _FilaProducto(ctk.CTkFrame):
    """
    Usa grid con pesos para que las columnas se adapten al ancho disponible.
    Columnas: Producto(4) | Costo(2) | Venta(2) | Stock(1) | Acciones(2)
    """

    def __init__(self, parent, producto, al_editar, al_eliminar):
        super().__init__(parent, fg_color=COLORES["fondo_card"],
                         corner_radius=6, border_width=1,
                         border_color=COLORES["borde"])
        self.columnconfigure(0, weight=4)
        self.columnconfigure(1, weight=2)
        self.columnconfigure(2, weight=2)
        self.columnconfigure(3, weight=1)
        self.columnconfigure(4, weight=2)

        stock_color = COLORES["error"] if producto["stock"] <= 0 else COLORES["texto"]

        ctk.CTkLabel(self, text=producto["nombre"],
                     font=FUENTES["normal"], text_color=COLORES["texto"],
                     anchor="w").grid(row=0, column=0, sticky="ew", padx=(10,4), pady=8)

        ctk.CTkLabel(self, text=f"${producto['precio_costo']:,.0f}",
                     font=FUENTES["normal"], text_color=COLORES["texto_suave"],
                     anchor="w").grid(row=0, column=1, sticky="ew", padx=4, pady=8)

        ctk.CTkLabel(self, text=f"${producto['precio_venta']:,.0f}",
                     font=FUENTES["normal"], text_color=COLORES["texto"],
                     anchor="w").grid(row=0, column=2, sticky="ew", padx=4, pady=8)

        ctk.CTkLabel(self, text=str(producto["stock"]),
                     font=FUENTES["normal"], text_color=stock_color,
                     anchor="w").grid(row=0, column=3, sticky="ew", padx=4, pady=8)

        acc = ctk.CTkFrame(self, fg_color="transparent")
        acc.grid(row=0, column=4, sticky="e", padx=(4, 8), pady=4)

        ctk.CTkButton(
            acc, text="✎", width=28, height=28,
            fg_color="transparent",
            hover_color=COLORES["rosa_suave"],
            text_color=COLORES["rosa"],
            font=FUENTES["normal"],
            corner_radius=6,
            command=al_editar,
        ).pack(side="left", padx=1)

        ctk.CTkButton(
            acc, text="✕", width=28, height=28,
            fg_color="transparent",
            hover_color="#FDECEA",
            text_color=COLORES["error"],
            font=FUENTES["normal"],
            corner_radius=6,
            command=al_eliminar,
        ).pack(side="left", padx=1)


# ------------------------------------------------------------------ #
#  Formulario Proveedor                                                #
# ------------------------------------------------------------------ #

class _FormProveedor(ctk.CTkToplevel):

    def __init__(self, parent, service, proveedor=None, al_guardar=None):
        super().__init__(parent)
        self._service    = service
        self._proveedor  = proveedor
        self._al_guardar = al_guardar
        self._es_edicion = proveedor is not None

        self.title("Editar proveedor" if self._es_edicion else "Nuevo proveedor")
        self.geometry("440x520")
        self.resizable(True, True)
        self.configure(fg_color=COLORES["fondo"])
        self._construir()
        if self._es_edicion:
            self._rellenar(proveedor)
        self.after(100, self._forzar_foco)

    def _forzar_foco(self):
        self.lift()
        self.grab_set()
        self.focus_force()
        self._nombre.focus()

    def _construir(self):
        pad = {"padx": 28, "pady": 6}

        # Botones arriba
        btns = ctk.CTkFrame(self, fg_color=COLORES["fondo_card"], corner_radius=0)
        btns.pack(fill="x")
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

        etiqueta(self, "Dirección", fuente="small",
                 color=COLORES["texto_suave"]).pack(anchor="w", padx=28, pady=(8, 2))
        self._direccion = campo_texto(self, ancho=384)
        self._direccion.pack(**pad)

        etiqueta(self, "Notas", fuente="small",
                 color=COLORES["texto_suave"]).pack(anchor="w", padx=28, pady=(8, 2))
        self._notas = ctk.CTkTextbox(
            self, width=384, height=80,
            fg_color=COLORES["fondo_input"],
            border_color=COLORES["borde"],
            border_width=2,
            text_color=COLORES["texto"],
            font=FUENTES["normal"],
            corner_radius=8,
        )
        self._notas.pack(**pad)

    def _rellenar(self, p):
        self._nombre.insert(0, p["nombre"] or "")
        self._telefono.insert(0, p["telefono"] or "")
        self._email.insert(0, p["email"] or "")
        self._direccion.insert(0, p["direccion"] or "")
        if p["notas"]:
            self._notas.insert("1.0", p["notas"])

    def _guardar(self):
        nombre    = self._nombre.get().strip()
        telefono  = self._telefono.get().strip()
        email     = self._email.get().strip()
        direccion = self._direccion.get().strip()
        notas     = self._notas.get("1.0", "end").strip()

        if self._es_edicion:
            ok, msg = self._service.actualizar(
                self._proveedor["id"], nombre, telefono, email, direccion, notas)
            prov_id = self._proveedor["id"]
        else:
            ok, msg, prov_id = self._service.crear(nombre, telefono, email, direccion, notas)

        if not ok:
            mostrar_error("Error", msg)
            return

        mostrar_exito("Listo", msg)
        self.destroy()
        if self._al_guardar and prov_id:
            self._al_guardar(prov_id)


# ------------------------------------------------------------------ #
#  Formulario Producto                                                 #
# ------------------------------------------------------------------ #

class _FormProducto(ctk.CTkToplevel):

    def __init__(self, parent, service, proveedor, producto=None, al_guardar=None):
        super().__init__(parent)
        self._service    = service
        self._proveedor  = proveedor
        self._producto   = producto
        self._al_guardar = al_guardar
        self._es_edicion = producto is not None

        self.title("Editar producto" if self._es_edicion else "Nuevo producto")
        self.geometry("440x480")
        self.resizable(True, True)
        self.configure(fg_color=COLORES["fondo"])
        self._construir()
        if self._es_edicion:
            self._rellenar(producto)
        self.after(100, self._forzar_foco)

    def _forzar_foco(self):
        self.lift()
        self.grab_set()
        self.focus_force()
        self._nombre.focus()

    def _construir(self):
        pad = {"padx": 28, "pady": 6}

        btns = ctk.CTkFrame(self, fg_color=COLORES["fondo_card"], corner_radius=0)
        btns.pack(fill="x")
        boton_secundario(btns, "Cancelar", comando=self.destroy, ancho=160).pack(
            side="left", padx=28, pady=12)
        boton_primario(btns, "✔  Guardar", comando=self._guardar, ancho=160).pack(
            side="right", padx=28, pady=12)
        separador(self).pack(fill="x")

        etiqueta_suave(self, f"Proveedor: {self._proveedor['nombre']}").pack(
            anchor="w", padx=28, pady=(12, 0))

        etiqueta(self, "Nombre del producto *", fuente="small",
                 color=COLORES["texto_suave"]).pack(anchor="w", padx=28, pady=(10, 2))
        self._nombre = campo_texto(self, ancho=384)
        self._nombre.pack(**pad)

        etiqueta(self, "Categoría", fuente="small",
                 color=COLORES["texto_suave"]).pack(anchor="w", padx=28, pady=(8, 2))
        self._categoria = campo_texto(self, placeholder="Ej: Tinturas, Tratamientos...", ancho=384)
        self._categoria.pack(**pad)

        # Fila precios
        fila = ctk.CTkFrame(self, fg_color="transparent")
        fila.pack(fill="x", padx=28, pady=6)
        fila.columnconfigure(0, weight=1)
        fila.columnconfigure(1, weight=1)

        etiqueta(fila, "Precio costo *", fuente="small",
                 color=COLORES["texto_suave"]).grid(row=0, column=0, sticky="w", pady=(0, 2))
        self._costo = campo_texto(fila, placeholder="0", ancho=0)
        self._costo.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        etiqueta(fila, "Precio venta *", fuente="small",
                 color=COLORES["texto_suave"]).grid(row=0, column=1, sticky="w", pady=(0, 2))
        self._venta = campo_texto(fila, placeholder="0", ancho=0)
        self._venta.grid(row=1, column=1, sticky="ew", padx=(8, 0))

        etiqueta(self, "Stock inicial", fuente="small",
                 color=COLORES["texto_suave"]).pack(anchor="w", padx=28, pady=(8, 2))
        self._stock = campo_texto(self, placeholder="0", ancho=384)
        self._stock.pack(**pad)

    def _rellenar(self, p):
        self._nombre.insert(0, p["nombre"] or "")
        self._categoria.insert(0, p["categoria"] or "")
        self._costo.insert(0, str(p["precio_costo"]))
        self._venta.insert(0, str(p["precio_venta"]))
        self._stock.insert(0, str(p["stock"]))

    def _guardar(self):
        nombre    = self._nombre.get().strip()
        categoria = self._categoria.get().strip()

        try:
            costo = float(self._costo.get().strip() or 0)
            venta = float(self._venta.get().strip() or 0)
            stock = int(self._stock.get().strip() or 0)
        except ValueError:
            mostrar_error("Error", "Precio y stock deben ser números.")
            return

        if self._es_edicion:
            ok, msg = self._service.actualizar_producto(
                self._producto["id"], nombre, self._proveedor["id"],
                categoria, costo, venta, stock)
        else:
            ok, msg, _ = self._service.crear_producto(
                nombre, self._proveedor["id"], categoria, costo, venta, stock)

        if not ok:
            mostrar_error("Error", msg)
            return

        mostrar_exito("Listo", msg)
        self.destroy()
        if self._al_guardar:
            self._al_guardar()