import customtkinter as ctk
from ui.tema import COLORES, FUENTES


def boton_primario(parent, texto, comando=None, ancho=160, **kwargs):
    return ctk.CTkButton(
        parent,
        text=texto,
        command=comando,
        width=ancho,
        height=36,
        fg_color=COLORES["rosa"],
        hover_color=COLORES["rosa_hover"],
        text_color=COLORES["texto_blanco"],
        font=FUENTES["boton"],
        corner_radius=8,
        **kwargs
    )


def boton_secundario(parent, texto, comando=None, ancho=160, **kwargs):
    return ctk.CTkButton(
        parent,
        text=texto,
        command=comando,
        width=ancho,
        height=36,
        fg_color="transparent",
        hover_color=COLORES["rosa_suave"],
        text_color=COLORES["rosa"],
        border_color=COLORES["rosa"],
        border_width=1,
        font=FUENTES["boton"],
        corner_radius=8,
        **kwargs
    )


def boton_peligro(parent, texto, comando=None, ancho=160, **kwargs):
    return ctk.CTkButton(
        parent,
        text=texto,
        command=comando,
        width=ancho,
        height=36,
        fg_color=COLORES["error"],
        hover_color="#A93226",
        text_color=COLORES["texto_blanco"],
        font=FUENTES["boton"],
        corner_radius=8,
        **kwargs
    )


def campo_texto(parent, placeholder="", ancho=200, alto=36, **kwargs):
    return ctk.CTkEntry(
        parent,
        placeholder_text=placeholder,
        width=ancho,
        height=alto,
        fg_color=COLORES["fondo_input"],
        border_color=COLORES["borde"],
        text_color=COLORES["texto"],
        placeholder_text_color=COLORES["texto_suave"],
        corner_radius=8,
        font=FUENTES["normal"],
        **kwargs
    )


def etiqueta(parent, texto, fuente="normal", color=None, **kwargs):
    return ctk.CTkLabel(
        parent,
        text=texto,
        font=FUENTES.get(fuente, FUENTES["normal"]),
        text_color=color or COLORES["texto"],
        **kwargs
    )


def etiqueta_suave(parent, texto, **kwargs):
    return ctk.CTkLabel(
        parent,
        text=texto,
        font=FUENTES["small"],
        text_color=COLORES["texto_suave"],
        **kwargs
    )


def card(parent, **kwargs):
    return ctk.CTkFrame(
        parent,
        fg_color=COLORES["fondo_card"],
        corner_radius=12,
        border_width=1,
        border_color=COLORES["borde"],
        **kwargs
    )


def separador(parent, orientacion="horizontal", **kwargs):
    if orientacion == "horizontal":
        return ctk.CTkFrame(parent, height=1, fg_color=COLORES["borde"], **kwargs)
    return ctk.CTkFrame(parent, width=1, fg_color=COLORES["borde"], **kwargs)


def combo(parent, valores, ancho=200, **kwargs):
    return ctk.CTkComboBox(
        parent,
        values=valores,
        width=ancho,
        height=36,
        fg_color=COLORES["fondo_input"],
        border_color=COLORES["borde"],
        button_color=COLORES["rosa"],
        button_hover_color=COLORES["rosa_hover"],
        text_color=COLORES["texto"],
        font=FUENTES["normal"],
        corner_radius=8,
        **kwargs
    )


def selector(parent, valores, ancho=200, **kwargs):
    """OptionMenu simple."""
    var = ctk.StringVar(value=valores[0] if valores else "")
    widget = ctk.CTkOptionMenu(
        parent,
        values=valores,
        variable=var,
        width=ancho,
        height=36,
        fg_color=COLORES["rosa"],
        button_color=COLORES["rosa_hover"],
        button_hover_color=COLORES["rosa_hover"],
        text_color=COLORES["texto_blanco"],
        font=FUENTES["normal"],
        corner_radius=8,
        **kwargs
    )
    return widget, var


def mostrar_error(titulo, mensaje):
    import tkinter.messagebox as mb
    mb.showerror(titulo, mensaje)


def mostrar_exito(titulo, mensaje):
    import tkinter.messagebox as mb
    mb.showinfo(titulo, mensaje)


def confirmar(titulo, mensaje) -> bool:
    import tkinter.messagebox as mb
    return mb.askyesno(titulo, mensaje)