import sys
import os

# Asegura que el directorio raíz esté en el path (necesario con PyInstaller)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()