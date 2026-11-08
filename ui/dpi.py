"""Evita que Windows agrande una captura borrosa de la ventana (DPI virtual)."""
import sys


def activar_dpi_nativo():
    if sys.platform != 'win32':
        return False
    try:
        import ctypes
        # System DPI awareness: Tk se dibuja en pixeles nativos y los textos
        # mantienen ClearType. Compatible con Tk 8.6 en Windows 10/11.
        if ctypes.windll.shcore.SetProcessDpiAwareness(1) in (0, -2147024891):
            return True
    except (OSError, AttributeError, ValueError):
        pass
    try:
        return bool(ctypes.windll.user32.SetProcessDPIAware())
    except (OSError, AttributeError, ValueError):
        return False
