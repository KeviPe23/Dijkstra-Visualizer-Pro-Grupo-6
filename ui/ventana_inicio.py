"""Pantalla de bienvenida: solicita la cantidad inicial de nodos (7 a 16) antes de iniciar."""
import os
import sys
import tkinter as tk

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = ImageTk = None

from ui import estilos as E


def resource_path(relative_path: str) -> str:
    """Obtiene la ruta absoluta al recurso, compatible con ejecución local y PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class VentanaInicio(tk.Frame):
    """Pantalla de inicio con fondo oscuro (#111827) integrada con portada.png, igual que Version_0."""

    BG_INICIO = '#111827'
    CARD_BG = '#1F2937'
    CARD_BORDER = '#374151'
    INPUT_BG = '#374151'
    INPUT_BORDER = '#4B5563'
    BTN_BG = '#00E5FF'
    BTN_HOVER = '#00B8D4'

    def __init__(self, master, on_comenzar):
        super().__init__(master, bg=self.BG_INICIO)
        self.on_comenzar = on_comenzar
        self._img_original = None
        self._foto_portada = None
        self._ultimo_tam_img = (0, 0)

        self.frame_centro = tk.Frame(self, bg=self.BG_INICIO)
        self.frame_centro.place(relx=0.5, rely=0.5, anchor='center')

        # Columna izquierda: ilustración de portada
        self.frame_izquierdo = tk.Frame(self.frame_centro, bg=self.BG_INICIO)
        self.frame_izquierdo.pack(side='left', padx=(0, E.dp(34)))

        ancho_inicial = E.dp(660)
        alto_inicial = E.dp(440)
        self.frame_imagen = tk.Frame(
            self.frame_izquierdo,
            width=ancho_inicial,
            height=alto_inicial,
            bg=self.BG_INICIO,
        )
        self.frame_imagen.pack()
        self.frame_imagen.pack_propagate(False)

        self.lbl_imagen = tk.Label(
            self.frame_imagen,
            text='',
            bg=self.BG_INICIO,
            fg='#9CA3AF',
            font=(E.FONT, 12),
        )
        self.lbl_imagen.place(relx=0.5, rely=0.5, anchor='center')
        self._cargar_portada(ancho_inicial, alto_inicial)

        # Columna derecha: título, selector de nodos y botón COMENZAR
        self.frame_derecho = tk.Frame(self.frame_centro, bg=self.BG_INICIO)
        self.frame_derecho.pack(side='right', padx=(E.dp(24), 0))

        self.lbl_titulo = tk.Label(
            self.frame_derecho,
            text='Dijkstra Visualizer Pro',
            font=(E.FONT, 28, 'bold'),
            bg=self.BG_INICIO,
            fg='#FFFFFF',
        )
        self.lbl_titulo.pack(pady=(0, E.dp(6)))

        self.lbl_subtitulo = tk.Label(
            self.frame_derecho,
            text='Grafos dirigidos acíclicos (DAG) · Etiquetado [d,V](n)',
            font=(E.FONT, 10),
            bg=self.BG_INICIO,
            fg='#9CA3AF',
        )
        self.lbl_subtitulo.pack(pady=(0, E.dp(28)))

        self.frame_config = tk.Frame(
            self.frame_derecho,
            bg=self.CARD_BG,
            highlightbackground=self.CARD_BORDER,
            highlightthickness=1,
            padx=E.dp(28),
            pady=E.dp(22),
        )
        self.frame_config.pack(pady=E.dp(8), fill='x')

        self.lbl_pregunta = tk.Label(
            self.frame_config,
            text='¿Con cuántos nodos deseas empezar?',
            font=(E.FONT, 14, 'bold'),
            bg=self.CARD_BG,
            fg='#E5E7EB',
        )
        self.lbl_pregunta.pack(pady=(E.dp(4), E.dp(4)))

        self.lbl_rango = tk.Label(
            self.frame_config,
            text='Elige una cantidad entera entre 7 y 16 vértices',
            font=(E.FONT, 10),
            bg=self.CARD_BG,
            fg='#9CA3AF',
        )
        self.lbl_rango.pack(pady=(0, E.dp(14)))

        marco_entrada = tk.Frame(
            self.frame_config,
            bg=self.INPUT_BG,
            highlightbackground=self.INPUT_BORDER,
            highlightthickness=1,
            padx=E.dp(6),
            pady=E.dp(4),
        )
        marco_entrada.pack(pady=E.dp(4))

        self.entrada_nodos = tk.Entry(
            marco_entrada,
            width=8,
            justify='center',
            font=(E.FONT, 18, 'bold'),
            bg=self.INPUT_BG,
            fg='#FFFFFF',
            insertbackground='#FFFFFF',
            relief='flat',
            bd=0,
        )
        self.entrada_nodos.insert(0, '7')
        self.entrada_nodos.pack()
        self.entrada_nodos.bind('<Return>', lambda _e: self._validar_y_comenzar())

        self.lbl_error = tk.Label(
            self.frame_config,
            text='',
            bg=self.CARD_BG,
            fg='#EF4444',
            font=(E.FONT, 10, 'bold'),
        )
        self.lbl_error.pack(pady=(E.dp(10), 0))

        self.btn_comenzar = tk.Button(
            self.frame_derecho,
            text='COMENZAR',
            font=(E.FONT, 15, 'bold'),
            bg=self.BTN_BG,
            fg='#081B2B',
            activebackground=self.BTN_HOVER,
            activeforeground='#081B2B',
            relief='flat',
            bd=0,
            cursor='hand2',
            padx=E.dp(46),
            pady=E.dp(11),
            command=self._validar_y_comenzar,
        )
        self.btn_comenzar.pack(pady=(E.dp(28), 0))
        self.btn_comenzar.bind('<Enter>', lambda _e: self.btn_comenzar.configure(bg=self.BTN_HOVER))
        self.btn_comenzar.bind('<Leave>', lambda _e: self.btn_comenzar.configure(bg=self.BTN_BG))

        self.bind('<Configure>', self._ajustar_responsivo)

    def _cargar_portada(self, max_w: int, max_h: int):
        ruta_portada = resource_path('portada.png')
        if Image is not None and ImageTk is not None and os.path.exists(ruta_portada):
            try:
                if self._img_original is None:
                    self._img_original = Image.open(ruta_portada).convert('RGBA')
                iw, ih = self._img_original.size
                escala = min(max_w / max(1, iw), max_h / max(1, ih))
                nw, nh = max(120, round(iw * escala)), max(90, round(ih * escala))
                if (nw, nh) != self._ultimo_tam_img:
                    self._ultimo_tam_img = (nw, nh)
                    redim = self._img_original.resize((nw, nh), Image.Resampling.LANCZOS)
                    self._foto_portada = ImageTk.PhotoImage(redim, master=self)
                    self.lbl_imagen.configure(image=self._foto_portada, text='')
                return
            except Exception:
                pass
        self.lbl_imagen.configure(
            text='[ Imagen de Portada Aquí ]\n(portada.png)',
            image='',
        )

    def _ajustar_responsivo(self, event):
        if event.width < 400 or event.height < 300:
            return
        max_w = max(E.dp(320), min(E.dp(720), int(event.width * 0.48)))
        max_h = max(E.dp(240), min(E.dp(500), int(event.height * 0.68)))
        if abs(self.frame_imagen.winfo_reqwidth() - max_w) > 18 or abs(self.frame_imagen.winfo_reqheight() - max_h) > 18:
            self.frame_imagen.configure(width=max_w, height=max_h)
            self._cargar_portada(max_w, max_h)

    def _validar_y_comenzar(self):
        texto = self.entrada_nodos.get().strip()
        try:
            n = int(texto)
        except ValueError:
            self.lbl_error.configure(text='Ingresa un número válido.')
            return False

        if 7 <= n <= 16:
            callback = self.on_comenzar
            self.destroy()
            callback(n)
            return True

        self.lbl_error.configure(text='Elige entre 7 y 16 nodos.')
        return False

