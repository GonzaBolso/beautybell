import customtkinter as ctk
from PIL import Image
from ui.tema import COLORES, FUENTES, TEMA, SIDEBAR_ANCHO
from db.database import inicializar_db


def resource_path(relative: str) -> str:
    import sys, os
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", relative)



class MainWindow(ctk.CTk):

    # Definición de módulos: (clave, etiqueta, icono unicode)
    MODULOS = [
        ("turnos",       "Turnos",       "📅"),
        ("clientes",     "Clientes",     "👤"),
        ("caja",         "Caja",         "💰"),
        ("proveedores",  "Proveedores",  "📦"),
        ("configuracion","Configuración","⚙️"),
        ("precios",      "Precios",      "🏷️"),  # <-- nuevo módulo
    ]

    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode(TEMA)
        ctk.set_default_color_theme("blue")

        self.title("BeautyBel")
        self.geometry("1100x680")
        try:
            import os
            ico = resource_path(os.path.join("assets", "icon.ico"))
            self.iconbitmap(ico)
        except Exception:
            pass
        self.minsize(900, 580)
        self.configure(fg_color=COLORES["fondo"])

        inicializar_db()

        self._vista_actual = None
        self._botones_nav  = {}

        self._construir_layout()
        self._navegar("turnos")

    # ------------------------------------------------------------------ #
    #  Layout general                                                      #
    # ------------------------------------------------------------------ #

    def _construir_layout(self):
        # Sidebar izquierdo
        self.sidebar = ctk.CTkFrame(
            self,
            width=SIDEBAR_ANCHO,
            fg_color=COLORES["fondo_sidebar"],
            corner_radius=0,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Área de contenido principal
        self.area_contenido = ctk.CTkFrame(
            self,
            fg_color=COLORES["fondo"],
            corner_radius=0,
        )
        self.area_contenido.pack(side="left", fill="both", expand=True)

        self._construir_sidebar()

    def _construir_sidebar(self):
        # ---- Logo / Nombre ----
        logo_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color=COLORES["fondo_sidebar"],
            corner_radius=0,
            height=175,
        )
        logo_frame.pack(fill="x")
        logo_frame.pack_propagate(False)

        try:
            import os
            ruta_logo = resource_path(os.path.join("assets", "logo_circle.png"))
            img_pil = Image.open(ruta_logo)
            self._logo_img = ctk.CTkImage(light_image=img_pil, size=(168, 168))
            ctk.CTkLabel(
                logo_frame,
                image=self._logo_img,
                text="",
            ).place(relx=0.5, rely=0.5, anchor="center")
        except Exception:
            ctk.CTkLabel(
                logo_frame,
                text="✦ BeautyBel",
                font=FUENTES["nombre_app"],
                text_color=COLORES["dorado"],
            ).place(relx=0.5, rely=0.55, anchor="center")

        # Línea separadora
        ctk.CTkFrame(
            self.sidebar,
            height=1,
            fg_color=COLORES["borde"],
        ).pack(fill="x", padx=16)

        # ---- Navegación ----
        nav_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent",
            corner_radius=0,
        )
        nav_frame.pack(fill="both", expand=True, pady=12)

        for clave, etiqueta, icono in self.MODULOS:
            btn = ctk.CTkButton(
                nav_frame,
                text=f"  {icono}  {etiqueta}",
                anchor="w",
                width=SIDEBAR_ANCHO - 24,
                height=44,
                fg_color="transparent",
                hover_color=COLORES["nav_hover"],
                text_color=COLORES["nav_texto"],
                font=FUENTES["normal"],
                corner_radius=8,
                command=lambda c=clave: self._navegar(c),
            )
            btn.pack(padx=12, pady=2)
            self._botones_nav[clave] = btn

        # ---- Pie del sidebar ----
        ctk.CTkFrame(
            self.sidebar,
            height=1,
            fg_color=COLORES["borde"],
        ).pack(fill="x", padx=16)

        ctk.CTkLabel(
            self.sidebar,
            text="v1.0.0",
            font=FUENTES["small"],
            text_color=COLORES["texto_suave"],
        ).pack(pady=10)

    # ------------------------------------------------------------------ #
    #  Navegación                                                          #
    # ------------------------------------------------------------------ #

    def _navegar(self, clave: str):
        # Resaltar botón activo y resetear los demás
        for k, btn in self._botones_nav.items():
            if k == clave:
                btn.configure(
                    fg_color=COLORES["nav_activo"],
                    text_color=COLORES["rosa"],
                    font=FUENTES["subtitulo"],
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORES["nav_texto"],
                    font=FUENTES["normal"],
                )

        # Destruir vista anterior
        if self._vista_actual:
            self._vista_actual.destroy()

        # Instanciar la vista correspondiente
        self._vista_actual = self._crear_vista(clave)
        if self._vista_actual:
            self._vista_actual.pack(fill="both", expand=True)

    def _crear_vista(self, clave: str):
        """Importa y crea la vista según la clave. Import lazy para no cargar todo al inicio."""
        try:
            if clave == "turnos":
                from ui.turnos_view import TurnosView
                return TurnosView(self.area_contenido)

            elif clave == "clientes":
                from ui.clientes_view import ClientesView
                return ClientesView(self.area_contenido)

            elif clave == "caja":
                from ui.caja_view import CajaView
                return CajaView(self.area_contenido)

            elif clave == "proveedores":
                from ui.proveedores_view import ProveedoresView
                return ProveedoresView(self.area_contenido)

            elif clave == "configuracion":
                from ui.configuracion_view import ConfiguracionView
                return ConfiguracionView(self.area_contenido)

            elif clave == "precios":
                from ui.precios_view import PreciosView
                return PreciosView(self.area_contenido)

        except Exception as e:
            # Si la vista aún no está implementada, mostrar placeholder
            return self._placeholder(clave, str(e))

    def _placeholder(self, clave: str, error: str = ""):
        frame = ctk.CTkFrame(self.area_contenido, fg_color=COLORES["fondo"], corner_radius=0)
        ctk.CTkLabel(
            frame,
            text=f"🚧  Módulo '{clave}' en construcción",
            font=FUENTES["titulo"],
            text_color=COLORES["texto_suave"],
        ).place(relx=0.5, rely=0.45, anchor="center")
        if error:
            ctk.CTkLabel(
                frame,
                text=error,
                font=FUENTES["small"],
                text_color=COLORES["error"],
            ).place(relx=0.5, rely=0.53, anchor="center")
        return frame