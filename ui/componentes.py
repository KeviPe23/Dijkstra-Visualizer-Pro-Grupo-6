"""Componentes reutilizables: indicador '?' informativo (no clickeable), ToolTip e interruptor de tema."""
import tkinter as tk

try:
    from PIL import Image, ImageDraw, ImageTk
except ImportError:
    Image = ImageDraw = ImageTk = None

from ui import estilos as E


class ToolTip:
    """Cuadro emergente informativo al pasar el cursor por encima de un indicador."""

    def __init__(self, widget, texto: str):
        self.widget = widget
        self.texto = texto
        self.tw = None
        self.widget.bind('<Enter>', self.mostrar, add='+')
        self.widget.bind('<Leave>', self.ocultar, add='+')
        self.widget.bind('<Unmap>', self.ocultar, add='+')
        self.widget.bind('<Destroy>', self.ocultar, add='+')

    def mostrar(self, event=None):
        if self.tw is not None or not self.widget.winfo_exists():
            return
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        try:
            self.tw.wm_attributes('-topmost', True)
        except tk.TclError:
            pass
        marco = tk.Frame(
            self.tw,
            bg=E.TOOLTIP_BG,
            highlightbackground=E.TOOLTIP_BORDER,
            highlightthickness=1,
            padx=E.dp(11),
            pady=E.dp(8),
        )
        marco.pack()
        lbl = tk.Label(
            marco,
            text=self.texto,
            bg=E.TOOLTIP_BG,
            fg=E.TOOLTIP_FG,
            font=(E.FONT, 9),
            justify='left',
            anchor='w',
            wraplength=E.dp(330),
        )
        lbl.pack()
        self.tw.update_idletasks()
        ancho_tip = self.tw.winfo_reqwidth()
        alto_tip = self.tw.winfo_reqheight()
        ancho_scr = self.widget.winfo_screenwidth()
        alto_scr = self.widget.winfo_screenheight()

        x = self.widget.winfo_rootx() + self.widget.winfo_width() + E.dp(8)
        y = self.widget.winfo_rooty() - E.dp(2)
        if x + ancho_tip > ancho_scr - 12:
            x = max(10, self.widget.winfo_rootx() - ancho_tip - E.dp(8))
        if y + alto_tip > alto_scr - 16:
            y = max(10, alto_scr - alto_tip - 16)
        self.tw.wm_geometry(f'+{int(x)}+{int(y)}')

    def ocultar(self, event=None):
        if self.tw is not None:
            try:
                self.tw.destroy()
            except tk.TclError:
                pass
            self.tw = None


class IndicadorAyuda(tk.Canvas):
    """Ícono circular '?' NO clickeable que muestra ayuda contextual al pasar el mouse."""

    def __init__(self, parent, texto_ayuda: str, bg_padre=None):
        self._diametro = E.dp(20)
        self._bg_padre = bg_padre
        fondo = bg_padre if bg_padre is not None else E.PANEL
        super().__init__(
            parent,
            width=self._diametro,
            height=self._diametro,
            bg=fondo,
            bd=0,
            highlightthickness=0,
            takefocus=0,
            cursor='arrow',
        )
        self._foto = None
        self.texto_ayuda = texto_ayuda
        self.tooltip = ToolTip(self, texto_ayuda)

        # Bloquear explícitamente cualquier acción de clic del ratón.
        for secuencia in ('<Button-1>', '<Button-2>', '<Button-3>',
                          '<ButtonRelease-1>', '<Double-Button-1>'):
            self.bind(secuencia, self._ignorar_clic)

        self._dibujar()

    @staticmethod
    def _ignorar_clic(_event=None):
        return 'break'

    def _color_fondo(self):
        return self._bg_padre if self._bg_padre is not None else E.PANEL

    def _dibujar(self):
        d = self._diametro
        fondo = self._color_fondo()
        self.configure(bg=fondo)
        self.delete('all')
        if Image is not None and ImageDraw is not None and ImageTk is not None:
            try:
                escala = 4
                D = d * escala
                im = Image.new('RGBA', (D, D), fondo)
                draw = ImageDraw.Draw(im)
                margen = 2 * escala
                draw.ellipse((margen, margen, D - margen, D - margen), fill=E.HELP_BG)
                im = im.resize((d, d), Image.Resampling.LANCZOS)
                self._foto = ImageTk.PhotoImage(im, master=self)
                self.create_image(0, 0, anchor='nw', image=self._foto)
                self.create_text(
                    d / 2,
                    d / 2 - 0.5,
                    text='?',
                    fill=E.HELP_FG,
                    font=(E.FONT, 9, 'bold'),
                )
                return
            except Exception:
                pass
        self.create_oval(1, 1, d - 1, d - 1, fill=E.HELP_BG, outline=E.HELP_BG)
        self.create_text(d / 2, d / 2, text='?', fill=E.HELP_FG, font=(E.FONT, 9, 'bold'))

    def aplicar_tema(self, bg_padre=None):
        if bg_padre is not None:
            self._bg_padre = bg_padre
        self._dibujar()


class InterruptorTema(tk.Frame):
    """Switch moderno tipo píldora para alternar entre Modo Claro y Modo Oscuro."""

    def __init__(self, parent, command=None, activo_inicial: bool = False, texto: str = 'Modo Oscuro'):
        super().__init__(parent, bg=E.BG)
        self._activo = bool(activo_inicial)
        self._command = command
        self._ancho_sw = E.dp(44)
        self._alto_sw = E.dp(24)
        self._foto = None

        self.canvas = tk.Canvas(
            self,
            width=self._ancho_sw,
            height=self._alto_sw,
            bg=E.BG,
            bd=0,
            highlightthickness=0,
            cursor='hand2',
        )
        self.canvas.pack(side='left', padx=(0, E.dp(7)))

        self.lbl_texto = tk.Label(
            self,
            text=texto,
            bg=E.BG,
            fg=E.TEXT,
            font=(E.FONT, 10, 'bold'),
            cursor='hand2',
        )
        self.lbl_texto.pack(side='left')

        self.canvas.bind('<Button-1>', self._on_click)
        self.lbl_texto.bind('<Button-1>', self._on_click)
        self._dibujar()

    def _on_click(self, _event=None):
        self.toggle()
        return 'break'

    def get(self) -> bool:
        return self._activo

    def set(self, valor: bool, notificar: bool = False):
        self._activo = bool(valor)
        self._dibujar()
        if notificar and self._command:
            self._command(self._activo)

    def toggle(self):
        self.set(not self._activo, notificar=True)

    def _dibujar(self):
        w, h = self._ancho_sw, self._alto_sw
        fondo_ventana = E.BG
        pista = E.SWITCH_ON_BG if self._activo else E.SWITCH_OFF_BG
        borde_pista = E.ACCENT_ACTIVE if self._activo else E.BORDER
        self.configure(bg=fondo_ventana)
        self.canvas.configure(bg=fondo_ventana)
        self.lbl_texto.configure(bg=fondo_ventana, fg=E.TEXT)
        self.canvas.delete('all')

        if Image is not None and ImageDraw is not None and ImageTk is not None:
            try:
                s = 4
                W, H = w * s, h * s
                im = Image.new('RGBA', (W, H), fondo_ventana)
                draw = ImageDraw.Draw(im)
                pad = 2 * s
                radio = (H - 2 * pad) // 2
                draw.rounded_rectangle(
                    (pad, pad, W - pad, H - pad),
                    radius=radio,
                    fill=pista,
                    outline=borde_pista,
                    width=max(1, s),
                )
                margen_knob = 4 * s
                diam_knob = H - 2 * margen_knob
                kx1 = (W - margen_knob - diam_knob) if self._activo else margen_knob
                ky1 = margen_knob
                draw.ellipse(
                    (kx1, ky1, kx1 + diam_knob, ky1 + diam_knob),
                    fill=E.SWITCH_KNOB,
                )
                im = im.resize((w, h), Image.Resampling.LANCZOS)
                self._foto = ImageTk.PhotoImage(im, master=self.canvas)
                self.canvas.create_image(0, 0, anchor='nw', image=self._foto)
                return
            except Exception:
                pass

        # Respaldo vectorial sin Pillow
        r = h // 2 - 2
        self.canvas.create_oval(2, 2, 2 + 2 * r, h - 2, fill=pista, outline=pista)
        self.canvas.create_oval(w - 2 - 2 * r, 2, w - 2, h - 2, fill=pista, outline=pista)
        self.canvas.create_rectangle(2 + r, 2, w - 2 - r, h - 2, fill=pista, outline=pista)
        kr = r - 2
        cx = (w - 2 - r) if self._activo else (2 + r)
        cy = h / 2
        self.canvas.create_oval(cx - kr, cy - kr, cx + kr, cy + kr, fill=E.SWITCH_KNOB, outline=borde_pista)

    def aplicar_tema(self):
        self._dibujar()

