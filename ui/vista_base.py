import customtkinter as ctk
from ui.tema import COLORES, FUENTES
from ui.widgets import etiqueta, separador


class VistaBase(ctk.CTkFrame):
    """
    Frame base del que heredan todas las vistas.
    Provee cabecera con título y zona de contenido.
    """

    def __init__(self, parent, titulo: str, **kwargs):
        super().__init__(
            parent,
            fg_color=COLORES["fondo"],
            corner_radius=0,
            **kwargs
        )
        self._titulo = titulo
        self._construir_cabecera()
        self._construir_contenido()

    def _construir_cabecera(self):
        cab = ctk.CTkFrame(self, fg_color=COLORES["fondo"], corner_radius=0)
        cab.pack(fill="x", padx=24, pady=(10, 0))

        etiqueta(cab, self._titulo, fuente="titulo").pack(side="left")

        # Zona para botones de acción en la cabecera (subclases pueden usarla)
        self._acciones = ctk.CTkFrame(cab, fg_color="transparent")
        self._acciones.pack(side="right")

        separador(self, orientacion="horizontal").pack(fill="x", padx=24, pady=(8, 0))

    def _construir_contenido(self):
        """Subclases sobreescriben este método para agregar su contenido."""
        self.contenido = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.contenido.pack(fill="both", expand=True, padx=24, pady=16)

    def refrescar(self):
        """Subclases sobreescriben para recargar datos."""
        pass