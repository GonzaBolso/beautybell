import sys
import os


def resource_path(relative: str) -> str:
    """
    Devuelve la ruta correcta tanto en desarrollo (PyCharm)
    como empaquetado con PyInstaller (--onefile).
    """
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller extrae los assets a una carpeta temporal _MEIPASS
        return os.path.join(sys._MEIPASS, relative)
    # En desarrollo, la raíz es la carpeta del proyecto
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative)