"""Grafo interactivo y tabla de etiquetas implementados con Tkinter estándar y Pillow HD.

Elimina dependencias de Matplotlib y NetworkX, funciona sin Internet y soporta
cambio dinámico entre Modo Claro y Modo Oscuro con ayudas '?' contextuales.
"""
import math
import random
import tkinter as tk
from tkinter import ttk
from collections import defaultdict, deque

from ui import estilos as E
from ui import render_hd
from ui.componentes import IndicadorAyuda
from ui.etiquetas import datos_etiqueta, etiqueta_plana, etiquetas_descartadas
from ui.numeros import formatear_numero
from ui.vistas_didacticas import datos_historial, datos_matriz, VentanaTabla


class PanelGrafo(tk.Frame):
    AYUDA_GRAFO = (
        'Lienzo interactivo en alta definición (HD):\n'
        '• Arrastra cualquier vértice con clic izquierdo para reorganizar el grafo.\n'
        '• Haz clic en dos vértices para seleccionar Origen y Destino rápidamente.\n'
        '• Arrastra las cajas [d,V](n) para acomodarlas y haz doble clic en ellas para restaurarlas.\n'
        '• Usa Ctrl + rueda del mouse para acercar/alejar nodos, «Vista grande ↗» o «PNG 4K».'
    )
    AYUDA_NUMERACION = (
        'Define qué representa el subíndice (n) en las etiquetas [d,V](n):\n'
        '• «Lectura (etapas por ruta)»: cuenta el número de aristas desde el origen por esa ruta.\n'
        '• «Dijkstra (ronda real)»: indica la ronda global en que Dijkstra asignó la etiqueta.\n'
        '• Las distancias mínimas y los caminos óptimos no cambian.'
    )
    AYUDA_TABLA = (
        'Tabla de resultados y vistas complementarias:\n'
        '• Muestra distancia acumulada d(v), predecesores óptimos π(v), estado y etiqueta [d,V](n).\n'
        '• «Historial de etiquetas ↗» abre la evolución por rondas con descartes (×) y empates (=).\n'
        '• «Matriz de distancias ↗» abre la matriz de adyacencia ponderada del DAG.'
    )

    def __init__(self, master, on_nodo_click=None, allow_expand=True):
        super().__init__(master, bg=E.BG)
        self.allow_expand = allow_expand
        self.on_nodo_click = on_nodo_click
        self.grafo = None
        self.posiciones = {}
        self.posiciones_etiquetas = {}  # Nodo -> desplazamiento (dx, dy) relativo al vértice.
        self.cajas_etiquetas = {}  # Cajas sobre el canvas usadas para detectar el mouse.
        self.etiqueta_pulsada = None
        self._inicio_arrastre_etiqueta = None
        self.estado = None
        self.caminos = []
        self.nodo_pulsado = None
        self.punto_pulsado = None
        self.movido = False
        self._posiciones_manuales = False
        self._modo_disposicion = 'niveles'
        self.tipo_layout_actual = 'niveles'
        self._bolsa_layouts = []
        self._pos_norm = {}
        self._size = (0, 0)
        self._foto_hd = None
        self._imagen_hd = None
        self._ultimo_suavizado = 0
        self.ventana_historial = None
        self.ventana_matriz = None
        self.vistas_ampliadas = []
        self.indicadores_ayuda = []
        self._botones_accion = []
        self._elementos_leyenda = []
        self._mensaje_tipo = 'normal'  # 'normal' | 'ok' | 'error'
        self.mostrar_etiquetas = tk.BooleanVar(value=True)
        self.modo_numeracion = tk.StringVar(value='Lectura (etapas por ruta)')
        self._crear()

    def _tarjeta(self, padre):
        return tk.Frame(padre, bg=E.PANEL, highlightbackground=E.BORDER, highlightthickness=1)

    def _crear_boton_accion(self, parent, texto, comando, fuente_tam=10, padx=10, pady=5):
        btn = tk.Button(
            parent,
            text=texto,
            command=comando,
            bg=E.BTN_SECONDARY_BG,
            fg=E.BTN_SECONDARY_FG,
            activebackground=E.BLUE,
            activeforeground='#FFFFFF',
            highlightbackground=E.BORDER,
            highlightcolor=E.BORDER,
            highlightthickness=1,
            bd=0,
            relief='flat',
            font=(E.FONT, fuente_tam, 'bold'),
            padx=padx,
            pady=pady,
            cursor='hand2',
        )
        btn.bind('<Enter>', lambda _e, b=btn: b.configure(bg=E.BTN_SECONDARY_HOVER), add='+')
        btn.bind('<Leave>', lambda _e, b=btn: b.configure(bg=E.BTN_SECONDARY_BG), add='+')
        self._botones_accion.append(btn)
        return btn

    def _crear(self):
        # Contenido central desplazable: ni la tabla ni los nodos se recortan
        # en portátiles de 1366x768. El grafo conserva un alto legible.
        self.scroll_canvas = tk.Canvas(self, bg=E.BG, highlightthickness=0, bd=0)
        self.scrollbar_vertical = ttk.Scrollbar(self, orient='vertical',
                                                command=self.scroll_canvas.yview)
        self.scroll_canvas.configure(yscrollcommand=self.scrollbar_vertical.set)
        self.scrollbar_vertical.pack(side='right', fill='y')
        self.scroll_canvas.pack(side='left', fill='both', expand=True)
        self.contenido = tk.Frame(self.scroll_canvas, bg=E.BG)
        self.item_contenido = self.scroll_canvas.create_window(
            0, 0, anchor='nw', window=self.contenido)
        self.contenido.bind('<Configure>', lambda e: self.scroll_canvas.configure(
            scrollregion=self.scroll_canvas.bbox('all')))
        self.scroll_canvas.bind('<Configure>', lambda e: self.scroll_canvas.itemconfigure(
            self.item_contenido, width=e.width))

        self.grafo_card = self._tarjeta(self.contenido)
        self.grafo_card.pack(fill='x', pady=(0, 10))
        self.header_grafo = tk.Frame(self.grafo_card, bg=E.PANEL)
        self.header_grafo.pack(fill='x', padx=14, pady=(10, 6))
        self.lbl_titulo_grafo = tk.Label(self.header_grafo, text='Visualización del grafo',
                                         bg=E.PANEL, fg=E.TEXT, font=(E.FONT, 13, 'bold'))
        self.lbl_titulo_grafo.pack(side='left')
        ind_grafo = IndicadorAyuda(self.header_grafo, self.AYUDA_GRAFO)
        ind_grafo.pack(side='left', padx=(7, 0))
        self.indicadores_ayuda.append(ind_grafo)

        if self.allow_expand:
            btn_png = self._crear_boton_accion(self.header_grafo, 'PNG 4K', self.guardar_png_hd, fuente_tam=10, padx=10, pady=5)
            btn_png.pack(side='right', padx=(8, 0))
            btn_vista = self._crear_boton_accion(self.header_grafo, 'Vista grande ↗', self.abrir_vista_ampliada, fuente_tam=10, padx=10, pady=5)
            btn_vista.pack(side='right')

        self.chk_etiquetas = tk.Checkbutton(
            self.header_grafo, text='Ver [d,V] (n)',
            variable=self.mostrar_etiquetas, command=self.dibujar_grafo,
            bg=E.PANEL, fg=E.TEXT, activebackground=E.PANEL,
            activeforeground=E.TEXT, selectcolor=E.CHECK_BG,
            font=(E.FONT, 10), cursor='hand2',
        )
        self.chk_etiquetas.pack(side='right', padx=(0, 11))

        altura = E.dp(570 if not self.allow_expand else 400)
        self.canvas = tk.Canvas(self.grafo_card, bg=E.CANVAS,
                                highlightbackground=E.BORDER, highlightthickness=1,
                                bd=0, height=altura, cursor='hand2')
        self.canvas.pack(fill='x', padx=9)
        self.canvas.bind('<Configure>', self._redimensionar)
        self.canvas.bind('<ButtonPress-1>', self._presionar)
        self.canvas.bind('<B1-Motion>', self._mover)
        self.canvas.bind('<ButtonRelease-1>', self._soltar)
        self.canvas.bind('<Button-3>', self._clic_derecho)
        self.canvas.bind('<Double-Button-1>', self._restaurar_etiqueta)
        self.canvas.bind('<MouseWheel>', self._rueda_zoom)

        self.leyenda = tk.Frame(self.grafo_card, bg=E.PANEL)
        self.leyenda.pack(fill='x', padx=14, pady=(6, 7))
        for nombre, clave_color in [
            ('No alcanzado', 'ACCENT'),
            ('Provisional', 'RED'),
            ('Definitivo', 'GREEN'),
            ('Actual', 'AMBER'),
        ]:
            elemento = tk.Frame(self.leyenda, bg=E.PANEL)
            elemento.pack(side='left', padx=(0, 14))
            punto = tk.Label(elemento, text='●', fg=getattr(E, clave_color), bg=E.PANEL,
                             font=(E.FONT, 11))
            punto.pack(side='left')
            texto_l = tk.Label(elemento, text=nombre, fg=E.MUTED, bg=E.PANEL,
                               font=(E.FONT, 10))
            texto_l.pack(side='left', padx=(3, 0))
            self._elementos_leyenda.append((elemento, punto, texto_l, clave_color))

        # Opciones separadas: la lectura usa etapas por ruta para sus ejemplos,
        # mientras que Dijkstra procesa vértices en rondas globales.
        self.panel_n = tk.Frame(self.grafo_card, bg=E.PANEL)
        self.panel_n.pack(fill='x', padx=14, pady=(0, 5))
        self.lbl_num_titulo = tk.Label(self.panel_n, text='Numeración n:', bg=E.PANEL, fg=E.TEXT,
                                       font=(E.FONT, 9, 'bold'))
        self.lbl_num_titulo.pack(side='left', padx=(0, 6))
        ind_num = IndicadorAyuda(self.panel_n, self.AYUDA_NUMERACION)
        ind_num.pack(side='left', padx=(0, 9))
        self.indicadores_ayuda.append(ind_num)

        self.combo_numeracion = ttk.Combobox(
            self.panel_n, state='readonly', textvariable=self.modo_numeracion,
            values=('Lectura (etapas por ruta)', 'Dijkstra (ronda real)'),
            width=27, style='Dijkstra.TCombobox', font=(E.FONT, 9))
        self.combo_numeracion.pack(side='left')
        self.combo_numeracion.bind('<<ComboboxSelected>>', self._cambiar_numeracion)
        self.lbl_numeracion = tk.Label(
            self.grafo_card, text='', bg=E.PANEL, fg=E.MUTED,
            font=(E.FONT, 9), anchor='w', justify='left', wraplength=720)
        self.lbl_numeracion.pack(fill='x', padx=14, pady=(0, 8))
        self._describir_numeracion()
        self.lbl_arrastre = tk.Label(
            self.grafo_card,
            text='Mover etiquetas: clic y arrastrar · Doble clic: restaurar posición',
            bg=E.PANEL, fg=E.ACCENT, font=(E.FONT, 9),
            anchor='w', justify='left', wraplength=720)
        self.lbl_arrastre.pack(fill='x', padx=14, pady=(0, 5))

        self.marco_explicacion = tk.Frame(self.grafo_card, bg=E.PANEL_ALT,
                                          highlightbackground=E.BORDER, highlightthickness=1)
        self.marco_explicacion.pack(fill='x', padx=9, pady=(0, 9))
        self.lbl_explicacion = tk.Label(
            self.marco_explicacion,
            text='Selecciona una operación para comenzar.',
            bg=E.PANEL_ALT, fg=E.TEXT, font=(E.FONT, 11), justify='left',
            anchor='w', wraplength=620, padx=12, pady=10,
        )
        self.lbl_explicacion.pack(fill='x')
        self.lbl_explicacion.bind('<Configure>', self._ajustar_wrap)

        self.tabla_card = self._tarjeta(self.contenido)
        self.tabla_card.pack(fill='x')
        self.cabecera_tabla = tk.Frame(self.tabla_card, bg=E.PANEL)
        self.cabecera_tabla.pack(fill='x', padx=14, pady=(10, 7))
        self.lbl_titulo_tabla = tk.Label(self.cabecera_tabla, text='Distancias y predecesores',
                                         bg=E.PANEL, fg=E.TEXT, font=(E.FONT, 12, 'bold'))
        self.lbl_titulo_tabla.pack(side='left')
        ind_tabla = IndicadorAyuda(self.cabecera_tabla, self.AYUDA_TABLA)
        ind_tabla.pack(side='left', padx=(7, 0))
        self.indicadores_ayuda.append(ind_tabla)

        self.lbl_paso = tk.Label(self.cabecera_tabla, text='Sin iniciar', bg=E.PANEL,
                                 fg=E.ACCENT, font=(E.FONT, 10, 'bold'))
        self.lbl_paso.pack(side='right')
        self.acciones_tabla = tk.Frame(self.tabla_card, bg=E.PANEL)
        self.acciones_tabla.pack(fill='x', padx=12, pady=(0, 7))
        for titulo, accion in [('Historial de etiquetas ↗', self.abrir_historial),
                               ('Matriz de distancias ↗', self.abrir_matriz)]:
            btn_t = self._crear_boton_accion(self.acciones_tabla, titulo, accion, fuente_tam=9, padx=9, pady=6)
            btn_t.pack(side='left', padx=(0, 8))

        self.tabla_frame = tk.Frame(self.tabla_card, bg=E.PANEL)
        self.tabla_frame.pack(fill='x', padx=10)
        columns = ('vertice', 'distancia', 'predecesores', 'estado', 'etiqueta')
        filas_tabla = 7
        self.tabla = ttk.Treeview(self.tabla_frame, columns=columns, show='headings',
                                  height=filas_tabla, selectmode='none', style='Dijkstra.Treeview')
        for clave, nombre, ancho in [
            ('vertice', 'Vértice', 60), ('distancia', 'Distancia d(v)', 125),
            ('predecesores', 'Predecesor(es) π(v)', 155), ('estado', 'Estado', 115),
            ('etiqueta', 'Etiqueta [d,V] (n)', 205)
        ]:
            self.tabla.heading(clave, text=nombre)
            self.tabla.column(clave, anchor='center', minwidth=55, width=ancho, stretch=True)
        scrollbar = ttk.Scrollbar(self.tabla_frame, orient='vertical', command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.tabla.pack(side='left', fill='x', expand=True)
        self._configurar_tags_tabla()
        self.lbl_resumen = tk.Label(
            self.tabla_card,
            text='[d,V](n): distancia, predecesor y nivel de ruta desde el origen.',
            bg=E.PANEL, fg=E.MUTED,
            font=(E.FONT, 10), anchor='w', justify='left',
            wraplength=700,
        )
        self.lbl_resumen.pack(fill='x', padx=14, pady=(7, 10))
        self.lbl_resumen.bind('<Configure>', self._ajustar_wrap)

    def _configurar_tags_tabla(self):
        self.tabla.tag_configure('normal', foreground=E.TEXT)
        self.tabla.tag_configure('actual', foreground=E.TABLE_ACTUAL)
        self.tabla.tag_configure('visitado', foreground=E.TABLE_VISITADO)
        self.tabla.tag_configure('evaluando', foreground=E.TABLE_EVALUANDO)

    def aplicar_tema(self):
        """Actualiza colores del panel, lienzo HD, tablas y ventanas emergentes abiertas."""
        self.configure(bg=E.BG)
        self.scroll_canvas.configure(bg=E.BG)
        self.contenido.configure(bg=E.BG)
        for card in (self.grafo_card, self.tabla_card):
            card.configure(bg=E.PANEL, highlightbackground=E.BORDER)
        for bloque in (self.header_grafo, self.leyenda, self.panel_n,
                       self.cabecera_tabla, self.acciones_tabla, self.tabla_frame):
            bloque.configure(bg=E.PANEL)

        self.lbl_titulo_grafo.configure(bg=E.PANEL, fg=E.TEXT)
        self.lbl_titulo_tabla.configure(bg=E.PANEL, fg=E.TEXT)
        self.lbl_num_titulo.configure(bg=E.PANEL, fg=E.TEXT)
        self.lbl_numeracion.configure(bg=E.PANEL, fg=E.MUTED)
        self.lbl_arrastre.configure(bg=E.PANEL, fg=E.ACCENT)
        self.lbl_paso.configure(bg=E.PANEL, fg=E.ACCENT)
        self.lbl_resumen.configure(bg=E.PANEL, fg=E.MUTED)

        self.chk_etiquetas.configure(
            bg=E.PANEL, fg=E.TEXT, activebackground=E.PANEL,
            activeforeground=E.TEXT, selectcolor=E.CHECK_BG,
        )
        for btn in self._botones_accion:
            btn.configure(
                bg=E.BTN_SECONDARY_BG,
                fg=E.BTN_SECONDARY_FG,
                activebackground=E.BLUE,
                activeforeground='#FFFFFF',
                highlightbackground=E.BORDER,
                highlightcolor=E.BORDER,
            )

        for elem, punto, texto_l, clave_color in self._elementos_leyenda:
            elem.configure(bg=E.PANEL)
            punto.configure(bg=E.PANEL, fg=getattr(E, clave_color))
            texto_l.configure(bg=E.PANEL, fg=E.MUTED)

        self.canvas.configure(bg=E.CANVAS, highlightbackground=E.BORDER)
        self.marco_explicacion.configure(bg=E.PANEL_ALT, highlightbackground=E.BORDER)
        color_msj = (
            E.RED if self._mensaje_tipo == 'error'
            else E.GREEN if self._mensaje_tipo == 'ok'
            else E.TEXT
        )
        self.lbl_explicacion.configure(bg=E.PANEL_ALT, fg=color_msj)
        self._configurar_tags_tabla()

        for ind in self.indicadores_ayuda:
            ind.aplicar_tema()

        for popup in (self.ventana_historial, self.ventana_matriz):
            if popup is not None and popup.winfo_exists():
                popup.aplicar_tema()

        vivas = []
        for popup, vista in self.vistas_ampliadas:
            if popup.winfo_exists():
                popup.configure(bg=E.BG)
                vista.aplicar_tema()
                vivas.append((popup, vista))
        self.vistas_ampliadas = vivas

        self.dibujar_grafo()

    def _modo(self):
        return 'ronda' if self.modo_numeracion.get() == 'Dijkstra (ronda real)' else 'lectura'

    def _describir_numeracion(self):
        if self._modo() == 'lectura':
            mensaje = ('[d,V](n): n = etapa desde el origen a lo largo de la ruta '
                       '(como los ejemplos del PDF). La ronda real aparece sobre la tabla.')
        else:
            mensaje = ('[d,V](n): n = ronda REAL en que Dijkstra asignó esa etiqueta. '
                       'Puede diferir del subíndice usado en las figuras del PDF.')
        self.lbl_numeracion.configure(text=mensaje)

    def _cambiar_numeracion(self, evento=None):
        self._describir_numeracion()
        if self.estado:
            self.actualizar_tabla_etiquetas(self.estado)
        self._actualizar_historial_abierto()
        self.dibujar_grafo()

    def abrir_historial(self):
        """Matriz por ronda sin comprimir ni desplazar el dibujo original."""
        if self.grafo is None:
            return None
        if self.ventana_historial and self.ventana_historial.winfo_exists():
            self.ventana_historial.lift()
            self.ventana_historial.focus_force()
            return self.ventana_historial
        self.ventana_historial = VentanaTabla(
            self.winfo_toplevel(), 'Historial de etiquetas por ronda',
            'Cada columna es una ronda de selección de Dijkstra. '
            'El subíndice n sigue el modo seleccionado en la ventana principal. '
            '× indica una etiqueta descartada; = indica empate válido. '
            'La tabla se actualiza mientras avanzas la simulación.', ancho_columna=195)
        self.ventana_historial.protocol('WM_DELETE_WINDOW',
                                      lambda: self._cerrar_ventana('ventana_historial'))
        self._actualizar_historial_abierto()
        return self.ventana_historial

    def abrir_matriz(self):
        """Visualiza la matriz ponderada del DAG: fila=origen, columna=destino."""
        if self.grafo is None:
            return None
        if self.ventana_matriz and self.ventana_matriz.winfo_exists():
            self.ventana_matriz.lift()
            self.ventana_matriz.focus_force()
            return self.ventana_matriz
        self.ventana_matriz = VentanaTabla(
            self.winfo_toplevel(), 'Matriz de distancias (DAG)',
            'Filas: vértice de salida. Columnas: vértice de llegada. '
            'Un número indica una arista dirigida y su peso; — significa '
            'que no hay arista directa. La diagonal 0 no es un bucle. '
            'Esta es una matriz de pesos, no de distancias mínimas.', ancho_columna=78)
        self.ventana_matriz.protocol('WM_DELETE_WINDOW',
                                   lambda: self._cerrar_ventana('ventana_matriz'))
        self._actualizar_matriz_abierta()
        return self.ventana_matriz

    def _cerrar_ventana(self, atributo):
        popup = getattr(self, atributo, None)
        setattr(self, atributo, None)
        if popup and popup.winfo_exists():
            popup.destroy()

    def _actualizar_historial_abierto(self):
        v = self.ventana_historial
        if v is not None and v.winfo_exists() and self.grafo:
            cols, filas = datos_historial(self.grafo, self.estado, modo=self._modo())
            v.descripcion.configure(text=(
                'Cada columna es una ronda real de Dijkstra. El subíndice n '
                + ('indica etapas de ruta, como el ejemplo PDF.' if self._modo() == 'lectura'
                   else 'indica la ronda real cuando fue asignada cada etiqueta.')
                + ' × = etiqueta descartada; = = empate válido.'))
            v.actualizar(cols, filas)

    def _actualizar_matriz_abierta(self):
        v = self.ventana_matriz
        if v is not None and v.winfo_exists() and self.grafo:
            cols, filas = datos_matriz(self.grafo)
            v.actualizar(cols, filas)

    def guardar_png_hd(self):
        """Exporta solo el grafo, nítido, a resolución 4K (3840 px de ancho)."""
        if self.grafo is None:
            return
        if not render_hd.disponible():
            from tkinter import messagebox
            messagebox.showinfo('Exportación HD',
                                'Para guardar en HD instala Pillow: python -m pip install Pillow',
                                parent=self)
            return
        from tkinter import filedialog, messagebox
        destino = filedialog.asksaveasfilename(parent=self, title='Guardar grafo en 4K',
                     defaultextension='.png', filetypes=[('Imagen PNG', '*.png')],
                     initialfile='Dijkstra_Grafo_4K.png')
        if not destino:
            return
        try:
            im = self._crear_imagen_hd(escala_salida=3840/max(1, self.canvas.winfo_width()),
                                       suavizado=2)
            im.save(destino, format='PNG', optimize=True)
            self.mostrar_mensaje(f'Grafo exportado en alta resolución: {destino}')
        except Exception as error:
            messagebox.showerror('No se pudo guardar', str(error), parent=self)

    def _crear_imagen_hd(self, escala_salida=1.0, suavizado=3):
        aristas = [(u, a.destino.id_nodo, getattr(a, 'peso_exacto', a.peso))
                   for u in sorted(self.grafo.nodos)
                   for a in self.grafo.obtener_sucesores(u)]
        evaluada = None
        nodo_actual = None
        visitados = set()
        if self.estado:
            nodo_actual = self.estado.get('nodo_actual')
            visitados = self.estado.get('visitados', set())
            if self.estado.get('estado') == 'EVALUANDO':
                evaluada = (self.estado.get('nodo_actual'), self.estado.get('vecino'))
        return render_hd.renderizar(self.canvas.winfo_width(), self.canvas.winfo_height(),
             self.posiciones, aristas, visitados, nodo_actual,
             evaluada, self.caminos, escala_salida=escala_salida, suavizado=suavizado,
             estado=self.estado if self.mostrar_etiquetas.get() else None,
             modo_etiquetas=self._modo(),
             posiciones_etiquetas=self.posiciones_etiquetas)

    def _rueda_zoom(self, event):
        """Rueda = desplazamiento vertical; Ctrl+rueda = zoom de nodos."""
        if not (event.state & 0x0004):
            if event.delta:
                self.scroll_canvas.yview_scroll(-int(event.delta/120), 'units')
            return 'break'
        if not self.posiciones:
            return
        factor = 1.10 if event.delta > 0 else 1/1.10
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        cx, cy = w/2, h/2
        self.posiciones = {n:(max(28, min(w-28, cx+(x-cx)*factor)),
                             max(28, min(h-28, cy+(y-cy)*factor)))
                           for n, (x,y) in self.posiciones.items()}
        self.dibujar_grafo()
        return 'break'

    def abrir_vista_ampliada(self):
        """Permite inspeccionar grafos densos sin deformar los textos del panel."""
        if self.grafo is None:
            return
        popup = tk.Toplevel(self)
        popup.title('Dijkstra Visualizer Pro · Vista ampliada')
        popup.configure(bg=E.BG)
        width = max(960, min(1480, popup.winfo_screenwidth() - 70))
        height = max(650, min(920, popup.winfo_screenheight() - 90))
        popup.geometry(f'{width}x{height}')
        vista = PanelGrafo(popup, on_nodo_click=None, allow_expand=False)
        vista.pack(fill='both', expand=True, padx=12, pady=12)
        vista.set_grafo(self.grafo, disposicion=self._modo_disposicion)
        vista._modo_disposicion = self._modo_disposicion
        vista.tipo_layout_actual = self.tipo_layout_actual
        vista._pos_norm = dict(self._pos_norm)
        if self.posiciones and self._size[0] > 0 and self._size[1] > 0:
            ox, oy = self._size
            vw = max(350, vista.canvas.winfo_width())
            vh = max(180, vista.canvas.winfo_height())
            vista.posiciones = {n: (x * vw / ox, y * vh / oy) for n, (x, y) in self.posiciones.items()}
            vista._size = (vw, vh)
            vista._posiciones_manuales = self._posiciones_manuales
        vista.mostrar_etiquetas.set(self.mostrar_etiquetas.get())
        vista.modo_numeracion.set(self.modo_numeracion.get())
        vista._describir_numeracion()
        vista.posiciones_etiquetas = self.posiciones_etiquetas.copy()
        if self.estado is not None:
            vista.actualizar_tabla_etiquetas(self.estado)
        vista.caminos = [list(ruta) for ruta in self.caminos]
        vista._mensaje_tipo = self._mensaje_tipo
        color_msj = (E.RED if self._mensaje_tipo == 'error'
                     else E.GREEN if self._mensaje_tipo == 'ok'
                     else None)
        vista.mostrar_mensaje(self.lbl_explicacion.cget('text'), color_msj)
        vista.mostrar_resumen(self.lbl_resumen.cget('text'))
        self.vistas_ampliadas.append((popup, vista))
        vista.after(80, vista.dibujar_grafo)
        return popup

    @staticmethod
    def _ajustar_wrap(event):
        if event.width > 50:
            event.widget.configure(wraplength=max(120, event.width - 25))

    @staticmethod
    def _letra(n):
        return chr(64 + n) if isinstance(n, int) and 1 <= n <= 26 else str(n)

    @staticmethod
    def _distancia(n):
        if n is None:
            return '—'
        if math.isinf(n):
            return '∞'
        return formatear_numero(n)

    def _elegir_tipo_variado(self) -> str:
        """Alterna aleatoriamente entre las tres distribuciones de Version_0 sin repetir seguida."""
        if not self._bolsa_layouts:
            bolsa = ['circular', 'cuadrado', 'aleatorio']
            random.shuffle(bolsa)
            if self.tipo_layout_actual in bolsa and bolsa[0] == self.tipo_layout_actual:
                bolsa[0], bolsa[-1] = bolsa[-1], bolsa[0]
            self._bolsa_layouts = bolsa
        elegido = self._bolsa_layouts.pop(0)
        self.tipo_layout_actual = elegido
        return elegido

    @staticmethod
    def _generar_pos_norm_variadas(nodos, tipo: str):
        """Genera coordenadas normalizadas [0, 1] x [0, 1] al estilo de Dijkstra_Visualizer_Version_0."""
        n = max(1, len(nodos))
        pos_norm = {}
        if tipo == 'circular':
            ang0 = random.uniform(0.0, 2.0 * math.pi)
            sentido = random.choice((1.0, -1.0))
            for i, nodo in enumerate(nodos):
                ang = ang0 + sentido * (2.0 * math.pi * i / n)
                pos_norm[nodo] = (0.5 + 0.45 * math.cos(ang), 0.5 + 0.45 * math.sin(ang))
        elif tipo == 'cuadrado':
            desfase = random.uniform(0.0, 8.0)
            sentido = random.choice((1.0, -1.0))
            for i, nodo in enumerate(nodos):
                t = (desfase + sentido * (i / n) * 8.0) % 8.0
                if t < 2.0:
                    xu, yu = -1.0 + t, -1.0
                elif t < 4.0:
                    xu, yu = 1.0, -1.0 + (t - 2.0)
                elif t < 6.0:
                    xu, yu = 1.0 - (t - 4.0), 1.0
                else:
                    xu, yu = -1.0, 1.0 - (t - 6.0)
                pos_norm[nodo] = (0.5 + 0.45 * xu, 0.5 + 0.44 * yu)
        else:
            # Dispersión aleatoria uniforme con muestreo del mejor candidato (evita nodos encimados)
            colocados = []
            for nodo in nodos:
                if not colocados:
                    mejor_pto = (random.uniform(0.06, 0.94), random.uniform(0.08, 0.92))
                else:
                    mejor_pto = None
                    mejor_dist = -1.0
                    for _ in range(32):
                        cx = random.uniform(0.05, 0.95)
                        cy = random.uniform(0.07, 0.93)
                        # Ponderar relación de aspecto típica (~2.1:1) del lienzo
                        d_min = min(((cx - px) * 2.1) ** 2 + (cy - py) ** 2 for px, py in colocados)
                        if d_min > mejor_dist:
                            mejor_dist = d_min
                            mejor_pto = (cx, cy)
                colocados.append(mejor_pto)
                pos_norm[nodo] = mejor_pto
        return pos_norm

    def _proyectar_pos_norm(self, ancho: float, alto: float):
        """Proyecta las coordenadas normalizadas sobre los píxeles reales del lienzo sin solapamientos."""
        mx = max(52.0, min(90.0, ancho * 0.085))
        my = max(46.0, min(66.0, alto * 0.145))
        w_util = max(80.0, ancho - 2.0 * mx)
        h_util = max(60.0, alto - 2.0 * my)
        pos = {n: [mx + ux * w_util, my + uy * h_util] for n, (ux, uy) in self._pos_norm.items()}

        # Separación mínima suave para que dos círculos de radio 22 px nunca se pisen en ventanas chicas
        ids = sorted(pos)
        min_d = 56.0
        lim_x1, lim_x2 = 34.0, max(35.0, ancho - 34.0)
        lim_y1, lim_y2 = 34.0, max(35.0, alto - 34.0)
        for _ in range(8):
            movio = False
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    u, v = ids[i], ids[j]
                    dx = pos[v][0] - pos[u][0]
                    dy = pos[v][1] - pos[u][1]
                    dist = math.hypot(dx, dy)
                    if dist < min_d:
                        movio = True
                        if dist < 1e-4:
                            ang = (i + 1) * 1.7 + j
                            dx, dy, dist = math.cos(ang), math.sin(ang), 1.0
                        empuje = (min_d - dist) * 0.52
                        ux, uy = (dx / dist) * empuje, (dy / dist) * empuje
                        pos[u][0] = min(lim_x2, max(lim_x1, pos[u][0] - ux))
                        pos[u][1] = min(lim_y2, max(lim_y1, pos[u][1] - uy))
                        pos[v][0] = min(lim_x2, max(lim_x1, pos[v][0] + ux))
                        pos[v][1] = min(lim_y2, max(lim_y1, pos[v][1] + uy))
            if not movio:
                break
        return {n: (xy[0], xy[1]) for n, xy in pos.items()}

    def set_grafo(self, grafo, conservar_posiciones=False, disposicion='niveles'):
        mismos_nodos = (conservar_posiciones
                        and grafo is not None
                        and bool(self.posiciones)
                        and set(self.posiciones) == set(grafo.nodos))
        self.grafo = grafo
        if not mismos_nodos:
            self.posiciones = {}
            self._size = (0, 0)
            self._posiciones_manuales = False
            self._modo_disposicion = disposicion
            if grafo is not None and disposicion == 'variada':
                tipo = self._elegir_tipo_variado()
                self._pos_norm = self._generar_pos_norm_variadas(sorted(grafo.nodos), tipo)
            else:
                self._pos_norm = {}
                self.tipo_layout_actual = 'niveles'
        self.posiciones_etiquetas.clear()
        self.cajas_etiquetas.clear()
        self.estado = None
        self.caminos = []
        self.limpiar_tabla_etiquetas(grafo)
        self._actualizar_matriz_abierta()
        self._actualizar_historial_abierto()
        self.scroll_canvas.yview_moveto(0)
        self.dibujar_grafo()

    def limpiar_tabla_etiquetas(self, grafo=None):
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        if grafo is not None:
            for n in sorted(grafo.nodos):
                self.tabla.insert('', 'end', iid=str(n), values=(self._letra(n), '—', '—', 'Sin calcular', '—'))
        self.lbl_paso.configure(text='Sin iniciar')
        self.lbl_resumen.configure(text='[d,V](n): distancia, predecesor y etapa; usa el selector «Numeración n» para comparar la lectura con Dijkstra.')

    def actualizar_tabla_etiquetas(self, estado, paso=None, total=None):
        self.estado = estado
        if estado is None:
            return
        etapa = estado['estado']
        titulos = {'INICIO': 'Inicialización', 'VISITADO': 'Selección del mínimo',
                   'EVALUANDO': 'Relajación de arista', 'FIN': 'Resultado final',
                   'SIN_INICIAR': 'Sin iniciar'}
        texto_paso = f"Iteración {estado.get('iteracion', 0)} · {titulos.get(etapa, etapa)}"
        if paso is not None and total:
            texto_paso = f'Paso {paso}/{total} · ' + texto_paso
        self.lbl_paso.configure(text=texto_paso)
        visitados = estado.get('visitados', set())
        actual = estado.get('nodo_actual')
        vecino = estado.get('vecino') if etapa == 'EVALUANDO' else None
        for n in sorted(estado['distancias']):
            dist = estado.get('distancias_exactas', estado['distancias'])[n]
            preds = estado.get('predecesores', {}).get(n, [])
            if etapa == 'SIN_INICIAR':
                situacion = 'Sin calcular'
                tag = 'normal'
            elif n == vecino:
                situacion = 'Evaluando'
                tag = 'evaluando'
            elif n == actual:
                situacion = 'Actual'
                tag = 'actual'
            elif n in visitados:
                situacion = 'Definitivo'
                tag = 'visitado'
            elif dist is None or math.isinf(dist):
                situacion = 'No alcanzado'
                tag = 'normal'
            else:
                situacion = 'Provisional'
                tag = 'normal'
            valores = (self._letra(n), self._distancia(dist),
                       ', '.join(self._letra(p) for p in preds) or '—', situacion,
                       etiqueta_plana(estado, n, modo=self._modo()))
            item = str(n)
            if not self.tabla.exists(item):
                self.tabla.insert('', 'end', iid=item, values=valores, tags=(tag,))
            else:
                self.tabla.item(item, values=valores, tags=(tag,))
        self._actualizar_historial_abierto()
        if vecino is not None and self.tabla.exists(str(vecino)):
            self.tabla.see(str(vecino))
        elif actual is not None and self.tabla.exists(str(actual)):
            self.tabla.see(str(actual))

    def mostrar_mensaje(self, texto, color=None):
        if color == E.RED:
            self._mensaje_tipo = 'error'
        elif color == E.GREEN:
            self._mensaje_tipo = 'ok'
        else:
            self._mensaje_tipo = 'normal'
        self.lbl_explicacion.configure(text=texto, fg=color or E.TEXT)

    def mostrar_resumen(self, texto):
        self.lbl_resumen.configure(text=texto)

    def _redimensionar(self, event):
        if self.grafo is None:
            return
        ancho, alto = max(event.width, 250), max(event.height, 200)
        if self._size != (ancho, alto):
            if self._size[0] > 0 and self.posiciones and self._posiciones_manuales:
                ox, oy = self._size
                self.posiciones = {
                    n: (max(26, min(ancho - 26, x * ancho / ox)),
                        max(26, min(alto - 26, y * alto / oy)))
                    for n, (x, y) in self.posiciones.items()
                }
            elif self._modo_disposicion == 'variada' and self._pos_norm:
                self.posiciones = self._proyectar_pos_norm(ancho, alto)
            else:
                self.posiciones = {}
            self._size = (ancho, alto)
            self.dibujar_grafo()

    def _calcular_posiciones(self):
        """Calcula posiciones variadas (circular/cuadrado/aleatorio) o niveles topológicos según el modo."""
        if self.grafo is None:
            return
        ancho = max(350, self.canvas.winfo_width())
        alto = max(180, self.canvas.winfo_height())
        self._size = (ancho, alto)
        if self._modo_disposicion == 'variada':
            if not self._pos_norm or set(self._pos_norm) != set(self.grafo.nodos):
                tipo = self._elegir_tipo_variado()
                self._pos_norm = self._generar_pos_norm_variadas(sorted(self.grafo.nodos), tipo)
            self.posiciones = self._proyectar_pos_norm(ancho, alto)
            return
        arcos = [(u, a.destino.id_nodo) for u in self.grafo.nodos
                 for a in self.grafo.obtener_sucesores(u)]
        activos = set()
        for u,v in arcos:
            activos.update((u,v))
        aislados = sorted(set(self.grafo.nodos) - activos)
        if not activos:
            nodos = sorted(self.grafo.nodos)
            cx, cy = ancho / 2, alto / 2
            rx, ry = max(65, min(190, ancho*.38)), max(58, min(135, alto*.36))
            self.posiciones = {n: (cx + rx * math.cos(2*math.pi*i/len(nodos)),
                                    cy + ry * math.sin(2*math.pi*i/len(nodos)))
                                for i,n in enumerate(nodos)}
            return
        indeg = {n: 0 for n in activos}
        sucesores = defaultdict(list)
        for u,v in arcos:
            sucesores[u].append(v)
            indeg[v] += 1
        cola = deque(sorted(n for n in activos if not indeg[n]))
        niveles = {n:0 for n in activos}
        visitados = 0
        while cola:
            u = cola.popleft()
            visitados += 1
            for v in sucesores[u]:
                niveles[v] = max(niveles[v], niveles[u]+1)
                indeg[v]-=1
                if indeg[v] == 0:
                    cola.append(v)
        if visitados != len(activos):
            nodos = sorted(self.grafo.nodos)
            self.posiciones = {n: (ancho/2 + ancho*.36 * math.cos(2*math.pi*i/len(nodos)),
                                    alto/2 + alto*.36 * math.sin(2*math.pi*i/len(nodos)))
                                for i,n in enumerate(nodos)}
            return
        grupos = defaultdict(list)
        for n,nivel in niveles.items():
            grupos[nivel].append(n)
        max_nivel = max(grupos)
        altura_activa = alto - (62 if aislados else 12)
        margen_x = max(55, min(85, ancho*.13))
        pos = {}
        for nivel, nodos in grupos.items():
            nodos.sort()
            x = ancho/2 if max_nivel == 0 else margen_x + (ancho-2*margen_x)*nivel/max_nivel
            cuenta = len(nodos)
            for i,n in enumerate(nodos):
                y = 30 + (altura_activa-60)*(i+1)/(cuenta+1)
                if cuenta > 8:
                    x2 = x + (12 if i%2 else -12)
                else:
                    x2 = x
                pos[n] = (x2,y)
        for j,n in enumerate(aislados):
            pos[n] = (max(26, (j+1)*ancho/(len(aislados)+1)), alto-28)
        self.posiciones = pos

    def dibujar_grafo(self, grafo=None, caminos_minimos=None, nodo_actual=None,
                     nodos_visitados=None, arista_evaluada=None, recalcular_pos=False):
        """Permite invocaciones desde controladores antiguos y el nuevo controlador."""
        if grafo is not None and grafo is not self.grafo:
            self.grafo = grafo
            self.posiciones = {}
            self.posiciones_etiquetas.clear()
            self.cajas_etiquetas.clear()
        if caminos_minimos is not None:
            self.caminos = caminos_minimos
        if self.grafo is None:
            self.canvas.delete('all')
            return
        if recalcular_pos or not self.posiciones or set(self.posiciones) != set(self.grafo.nodos):
            self._calcular_posiciones()
        if self.estado:
            nodo_actual = nodo_actual if nodo_actual is not None else self.estado.get('nodo_actual')
            nodos_visitados = nodos_visitados if nodos_visitados is not None else self.estado.get('visitados', set())
            if arista_evaluada is None and self.estado.get('estado') == 'EVALUANDO':
                arista_evaluada = (self.estado.get('nodo_actual'), self.estado.get('vecino'))
        nodos_visitados = nodos_visitados or set()
        ruta_arcos = set()
        for ruta in self.caminos:
            ruta_arcos.update(zip(ruta, ruta[1:]))
        self.canvas.delete('all')
        self.cajas_etiquetas.clear()
        if render_hd.disponible():
            try:
                calidad = 2 if self.movido else 3
                aristas_hd = [(u, a.destino.id_nodo, getattr(a, 'peso_exacto', a.peso))
                             for u in sorted(self.grafo.nodos)
                             for a in self.grafo.obtener_sucesores(u)]
                imagen = render_hd.renderizar(self.canvas.winfo_width(), self.canvas.winfo_height(),
                    self.posiciones, aristas_hd, nodos_visitados, nodo_actual,
                    arista_evaluada, self.caminos, suavizado=calidad,
                    estado=self.estado if self.mostrar_etiquetas.get() else None,
                    modo_etiquetas=self._modo(),
                    posiciones_etiquetas=self.posiciones_etiquetas,
                    cajas_etiquetas=self.cajas_etiquetas)
                self._imagen_hd = imagen
                self._foto_hd = render_hd.ImageTk.PhotoImage(imagen, master=self.canvas)
                self.canvas.create_image(0, 0, anchor='nw', image=self._foto_hd, tags='grafo_hd')
                return
            except (OSError, ValueError, MemoryError, RuntimeError) as error:
                self._ultimo_error_hd = str(error)
        for u in sorted(self.grafo.nodos):
            for a in self.grafo.obtener_sucesores(u):
                v = a.destino.id_nodo
                if u not in self.posiciones or v not in self.posiciones:
                    continue
                x1,y1 = self.posiciones[u]
                x2,y2 = self.posiciones[v]
                dx,dy = x2-x1,y2-y1
                dist = max(math.hypot(dx,dy), 0.01)
                ux,uy = dx/dist,dy/dist
                r = 22
                sx,sy = x1 + ux*r, y1+uy*r
                ex,ey = x2-ux*(r+2), y2-uy*(r+2)
                importante = (u,v) in ruta_arcos
                evaluado = arista_evaluada == (u,v)
                color = E.AMBER if evaluado else E.RED if importante else E.EDGE_DEFAULT
                self.canvas.create_line(sx, sy, ex, ey, fill=color, width=3 if evaluado or importante else 1.8,
                                        arrow='last', arrowshape=(12,14,5))
                px,py = (sx+ex)/2 - uy*12, (sy+ey)/2 + ux*12
                peso = formatear_numero(getattr(a, 'peso_exacto', a.peso))
                tam = max(18, 10 + len(peso)*7)
                self.canvas.create_rectangle(px-tam/2, py-10, px+tam/2, py+10,
                                             fill=E.WEIGHT_BG, outline=E.WEIGHT_BORDER)
                self.canvas.create_text(px, py, text=peso, fill=E.TEXT, font=(E.FONT, 10, 'bold'))
        for n in sorted(self.grafo.nodos):
            x,y = self.posiciones[n]
            alcanzado = bool(self.estado and not math.isinf(self.estado['distancias'].get(n, math.inf)))
            color = (E.NODE_AMBER if n == nodo_actual else E.NODE_GREEN if n in nodos_visitados
                     else E.NODE_RED if alcanzado else E.NODE_ACCENT)
            self.canvas.create_oval(x-22,y-22,x+22,y+22,fill=color,
                                    outline=E.NODE_OUTLINE,width=2,tags=(f'nodo_{n}','nodo'))
            self.canvas.create_text(x,y,text=self._letra(n), fill=E.NODE_TEXT,
                                     font=(E.FONT, 13, 'bold'),tags=(f'nodo_{n}','nodo'))
        if self.mostrar_etiquetas.get() and self.estado:
            self._dibujar_etiquetas_tk(nodos_visitados, nodo_actual)

    def _dibujar_etiquetas_tk(self, visitados, actual):
        """Modo de compatibilidad: etiquetas legibles incluso sin Pillow."""
        ancho, alto = self.canvas.winfo_width(), self.canvas.winfo_height()
        ocupados = [(x-28, y-28, x+28, y+28) for x,y in self.posiciones.values()]
        for n in sorted(self.posiciones):
            lineas = [f'{t}({i if i is not None else "–"})' for t,i in datos_etiqueta(self.estado, n, self._modo())]
            tachadas = etiquetas_descartadas(self.estado, n, self._modo())
            if not lineas:
                continue
            x,y = self.posiciones[n]
            h = max(32, (len(lineas)+len(tachadas))*20+12)
            w = max(90, max(len(t) for t in lineas+tachadas)*9+20)
            opciones = [(x+52,y-h-19), (x-52-w,y-h-19), (x+52,y+8),
                        (x-52-w,y+8), (x-w/2,y-60-h/2), (x-w/2,y+36)]
            mejor = None
            if n in self.posiciones_etiquetas:
                dx,dy = self.posiciones_etiquetas[n]
                xx = max(5, min(max(5, ancho-w-5), x+dx))
                yy = max(5, min(max(5, alto-h-5), y+dy))
                mejor = (xx, yy, xx+w, yy+h)
            else:
                mejor_p = float('inf')
                for xx,yy in opciones:
                    xx = max(5, min(max(5, ancho-w-5), xx))
                    yy = max(5, min(max(5, alto-h-5), yy))
                    rect = (xx, yy, xx+w, yy+h)
                    penal = sum(1 for a,b,c,d in ocupados if xx<c and xx+w>a and yy<d and yy+h>b)
                    if penal < mejor_p:
                        mejor, mejor_p = rect, penal
            if mejor is None:
                continue
            x1,y1,x2,y2 = mejor
            self.cajas_etiquetas[n] = mejor
            color = E.AMBER if n==actual else E.GREEN if n in visitados else E.RED if self.estado['distancias'][n] != float('inf') else E.MUTED
            self.canvas.create_rectangle(x1,y1,x2,y2, fill=E.TAG_BG, outline=color, width=1.5,
                                         tags=('etiqueta',))
            for indice, texto in enumerate(lineas):
                self.canvas.create_text((x1+x2)/2, y1+14+indice*20,
                                        text=texto, fill=E.TAG_TEXT, font=(E.FONT,12,'bold'),
                                        justify='center', tags=('etiqueta',))
            for indice, texto in enumerate(tachadas):
                yp = y1+14+(len(lineas)+indice)*20
                self.canvas.create_text((x1+x2)/2, yp, text=texto, fill=E.RED,
                                        font=(E.FONT,10), tags=('etiqueta',))
                self.canvas.create_line((x1+x2)/2-len(texto)*3.5, yp,
                                        (x1+x2)/2+len(texto)*3.5, yp,
                                        fill=E.RED, width=1.5, tags=('etiqueta',))
            ocupados.append(mejor)

    def _nodo_cercano(self, x,y):
        for n,(px,py) in self.posiciones.items():
            if (px-x)**2+(py-y)**2 <= 25**2:
                return n
        return None

    def _etiqueta_en(self, x, y):
        """Devuelve el nodo dueño de la etiqueta dibujada bajo el mouse."""
        if not self.mostrar_etiquetas.get():
            return None
        for nodo, (x1,y1,x2,y2) in reversed(list(self.cajas_etiquetas.items())):
            if x1 <= x <= x2 and y1 <= y <= y2:
                return nodo
        return None

    def _presionar(self, event):
        self.nodo_pulsado = self._nodo_cercano(event.x, event.y)
        self.etiqueta_pulsada = None
        self._inicio_arrastre_etiqueta = None
        if self.nodo_pulsado is None:
            self.etiqueta_pulsada = self._etiqueta_en(event.x, event.y)
            if self.etiqueta_pulsada is not None:
                nodo = self.etiqueta_pulsada
                x1,y1,_,_ = self.cajas_etiquetas[nodo]
                self._inicio_arrastre_etiqueta = (event.x-x1, event.y-y1)
        self.punto_pulsado = (event.x,event.y)
        self.movido = False

    def _mover(self, event):
        if (self.nodo_pulsado is None and self.etiqueta_pulsada is None) or not self.punto_pulsado:
            return
        if (event.x-self.punto_pulsado[0])**2 + (event.y-self.punto_pulsado[1])**2 > 20:
            self.movido = True
        if not self.movido:
            return
        if self.etiqueta_pulsada is not None:
            n = self.etiqueta_pulsada
            inicio_x, inicio_y = self._inicio_arrastre_etiqueta
            px, py = self.posiciones[n]
            self.posiciones_etiquetas[n] = (event.x-inicio_x-px, event.y-inicio_y-py)
        elif self.nodo_pulsado is not None:
            self._posiciones_manuales = True
            self.posiciones[self.nodo_pulsado] = (
                max(25,min(self.canvas.winfo_width()-25,event.x)),
                max(25,min(self.canvas.winfo_height()-25,event.y)))
        self.dibujar_grafo()

    def _soltar(self, event):
        seleccionado = self.nodo_pulsado
        fue_clic = seleccionado is not None and not self.movido
        self.nodo_pulsado = None
        self.etiqueta_pulsada = None
        self._inicio_arrastre_etiqueta = None
        self.punto_pulsado = None
        self.movido = False
        self.dibujar_grafo()
        if fue_clic and self.on_nodo_click:
            self.on_nodo_click(seleccionado)

    def _restaurar_etiqueta(self, event):
        """Doble clic: vuelve a la posición automática de esa etiqueta."""
        n = self._etiqueta_en(event.x, event.y)
        if n is not None and n in self.posiciones_etiquetas:
            self.posiciones_etiquetas.pop(n)
            self.etiqueta_pulsada = None
            self.nodo_pulsado = None
            self.punto_pulsado = None
            self.dibujar_grafo()
            return 'break'

    def _clic_derecho(self, event):
        seleccionado = self._nodo_cercano(event.x, event.y)
        if seleccionado is not None and self.on_nodo_click:
            self.on_nodo_click(seleccionado)
