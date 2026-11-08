"""Panel lateral: controles accesibles, ayudas contextuales '?' y soporte Claro/Oscuro."""
import tkinter as tk
from tkinter import ttk
from ui import estilos as E
from ui.componentes import IndicadorAyuda
from ui.numeros import formatear_numero


def _colores_boton(tipo: str):
    mapa = {
        'primary': (E.BTN_PRIMARY_BG, E.BTN_PRIMARY_FG, E.BTN_PRIMARY_HOVER),
        'secondary': (E.BTN_SECONDARY_BG, E.BTN_SECONDARY_FG, E.BTN_SECONDARY_HOVER),
        'blue': (E.BTN_BLUE_BG, E.BTN_BLUE_FG, E.BTN_BLUE_HOVER),
        'warning': (E.BTN_WARNING_BG, E.BTN_WARNING_FG, E.BTN_WARNING_HOVER),
    }
    return mapa[tipo]


def aplicar_estilo_boton(btn: tk.Button, habilitado=None):
    """Sincroniza fondo, texto, borde y cursor según el tema activo y el estado habilitado/deshabilitado."""
    tipo = getattr(btn, '_tipo_estilo', 'secondary')
    if habilitado is None:
        habilitado = str(btn.cget('state')) != 'disabled'
    if habilitado:
        fondo, texto_color, hover = _colores_boton(tipo)
        con_borde = (tipo == 'secondary')
        btn.configure(
            state='normal',
            bg=fondo,
            fg=texto_color,
            activebackground=hover,
            activeforeground=texto_color,
            disabledforeground=E.BTN_DISABLED_FG,
            highlightbackground=E.BORDER if con_borde else fondo,
            highlightcolor=E.BORDER if con_borde else fondo,
            highlightthickness=1 if con_borde else 0,
            cursor='hand2',
        )
    else:
        btn.configure(
            state='disabled',
            bg=E.BTN_DISABLED_BG,
            fg=E.BTN_DISABLED_FG,
            activebackground=E.BTN_DISABLED_BG,
            activeforeground=E.BTN_DISABLED_FG,
            disabledforeground=E.BTN_DISABLED_FG,
            highlightbackground=E.BTN_DISABLED_BORDER,
            highlightcolor=E.BTN_DISABLED_BORDER,
            highlightthickness=1,
            cursor='arrow',
        )


def _hover_boton(btn: tk.Button, entrando: bool):
    if str(btn.cget('state')) == 'disabled':
        return
    tipo = getattr(btn, '_tipo_estilo', 'secondary')
    fondo, _, hover = _colores_boton(tipo)
    color = hover if entrando else fondo
    btn.configure(bg=color)
    if tipo != 'secondary':
        btn.configure(highlightbackground=color, highlightcolor=color)


def boton(parent, texto, comando, tipo='primary', **kwargs):
    fondo, texto_color, hover = _colores_boton(tipo)
    btn = tk.Button(
        parent,
        text=texto,
        command=comando,
        bg=fondo,
        fg=texto_color,
        activebackground=hover,
        activeforeground=texto_color,
        disabledforeground=E.BTN_DISABLED_FG,
        relief='flat',
        bd=0,
        cursor='hand2',
        font=(E.FONT, 11, 'bold'),
        padx=E.dp(10),
        pady=E.dp(8),
        **kwargs,
    )
    btn._tipo_estilo = tipo
    aplicar_estilo_boton(btn, True)
    btn.bind('<Enter>', lambda _e, b=btn: _hover_boton(b, True), add='+')
    btn.bind('<Leave>', lambda _e, b=btn: _hover_boton(b, False), add='+')
    return btn


class PanelConfiguracion(tk.Frame):
    """Barra lateral desplazable con indicadores '?' no clickeables por sección."""

    AYUDAS_SECCION = {
        '01': (
            'Define la cantidad de vértices (entre 7 y 16) y crea tu grafo:\n'
            '• Cargar ejemplo de 1 ruta: DAG con siete vértices alcanzables (A → G).\n'
            '• Ejemplo de la lectura (A → H): red DAG de 8 vértices.\n'
            '• Grafo aleatorio: genera un nuevo DAG conexo sin ciclos.\n'
            '• Nuevo manual: crea los vértices vacíos para conectarlos tú mismo.'
        ),
        '02': (
            'Ejecuta el algoritmo de Dijkstra entre dos vértices:\n'
            '• Elige Origen y Destino en las listas (o haz clic sobre los nodos del dibujo).\n'
            '• «Resolver ahora» calcula y resalta al instante todas las rutas óptimas.\n'
            '• «Iniciar simulación paso a paso» permite avanzar (Siguiente →) y retroceder (← Anterior).'
        ),
        '03': (
            'Edita las conexiones dirigidas del grafo actual:\n'
            '• Selecciona Origen, Destino y un Peso no negativo, luego pulsa «Agregar arista».\n'
            '• Haz clic en una fila de la tabla y pulsa «Eliminar» para quitar esa arista.\n'
            '• Se rechazan automáticamente lazos, duplicados y ciclos para preservar un DAG.'
        ),
        '04': (
            'Muestra avisos en tiempo real sobre tus operaciones:\n'
            '• Confirma carga de grafos, cambios de aristas y avance de la simulación.\n'
            '• Explica el motivo exacto si una acción es rechazada (ciclos, duplicados o rango inválido).'
        ),
    }

    def __init__(self, master, callbacks):
        super().__init__(master, bg=E.PANEL, width=E.dp(356))
        self.callbacks = callbacks
        self._secciones = []
        self._frames_internos = []
        self._titulos = []
        self._etiquetas = []
        self._botones = []
        self.indicadores_ayuda = []
        self._estado_tipo = 'muted'  # 'muted' | 'ok' | 'error'

        self.pack_propagate(False)
        self.canvas_scroll = tk.Canvas(self, bg=E.PANEL, bd=0, highlightthickness=0,
                                       width=E.dp(337))
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas_scroll.yview)
        self.canvas_scroll.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.canvas_scroll.pack(side='left', fill='both', expand=True)
        self.interior = tk.Frame(self.canvas_scroll, bg=E.PANEL)
        self.window_id = self.canvas_scroll.create_window(0, 0, anchor='nw', window=self.interior)
        self.interior.bind('<Configure>', lambda e: self.canvas_scroll.configure(scrollregion=self.canvas_scroll.bbox('all')))
        self.canvas_scroll.bind('<Configure>', self._resize_inner)
        self.canvas_scroll.bind('<MouseWheel>', self._rueda)
        self.interior.bind('<MouseWheel>', self._rueda)
        self._construir()

    def _resize_inner(self, event):
        self.canvas_scroll.itemconfigure(self.window_id, width=event.width)

    def _rueda(self, event):
        if event.delta:
            self.canvas_scroll.yview_scroll(-int(event.delta / 120), 'units')
        return 'break'

    def _frame(self, parent, **kwargs):
        f = tk.Frame(parent, bg=E.PANEL, **kwargs)
        self._frames_internos.append(f)
        return f

    def _etiqueta(self, parent, texto):
        lbl = tk.Label(parent, text=texto, bg=E.PANEL, fg=E.MUTED,
                       font=(E.FONT, 10), anchor='w', wraplength=E.dp(295), justify='left')
        self._etiquetas.append(lbl)
        return lbl

    def _boton(self, parent, texto, comando, tipo='primary', **kwargs):
        b = boton(parent, texto, comando, tipo=tipo, **kwargs)
        self._botones.append(b)
        return b

    def _seccion(self, numero, nombre):
        envoltura = tk.Frame(self.interior, bg=E.PANEL, padx=E.dp(14), pady=E.dp(13),
                             highlightbackground=E.BORDER, highlightthickness=1)
        envoltura.pack(fill='x', padx=10, pady=(10, 2))
        self._secciones.append(envoltura)

        cabecera = self._frame(envoltura)
        cabecera.pack(fill='x', pady=(0, 8))
        lbl_t = tk.Label(cabecera, text=f'{numero}.  {nombre}', bg=E.PANEL, fg=E.TEXT,
                         font=(E.FONT, 11, 'bold'), anchor='w')
        lbl_t.pack(side='left', fill='x', expand=True)
        self._titulos.append(lbl_t)

        texto_ayuda = self.AYUDAS_SECCION.get(numero, '')
        if texto_ayuda:
            indicador = IndicadorAyuda(cabecera, texto_ayuda)
            indicador.pack(side='right', padx=(6, 0))
            self.indicadores_ayuda.append(indicador)

        return envoltura

    def _combo(self, parent, opciones, valor, ancho=6):
        combo = ttk.Combobox(parent, state='readonly', values=opciones, width=ancho,
                             font=(E.FONT, 10), style='Dijkstra.TCombobox')
        combo.set(valor)
        return combo

    def _construir(self):
        graf = self._seccion('01', 'Preparar el grafo')
        fila = self._frame(graf)
        fila.pack(fill='x', pady=(1, 10))
        self._etiqueta(fila, 'Cantidad de vértices (7 a 16)').pack(side='left', fill='x', expand=True)
        self.entrada_nodos = tk.Spinbox(
            fila, from_=7, to=16, width=4,
            bg=E.INPUT, fg=E.TEXT, bd=0,
            buttonbackground=E.BTN_SECONDARY_BG,
            insertbackground=E.TEXT,
            selectbackground=E.BLUE,
            selectforeground='#FFFFFF',
            highlightbackground=E.BORDER,
            highlightcolor=E.ACCENT,
            highlightthickness=1,
            font=(E.FONT, 12), justify='center',
        )
        self.entrada_nodos.delete(0, 'end')
        self.entrada_nodos.insert(0, '7')
        self.entrada_nodos.pack(side='right')
        self._boton(graf, 'Cargar ejemplo de 1 ruta', lambda: self.callbacks['ejemplo']()).pack(fill='x', pady=(0, 6))
        self._boton(graf, 'Ejemplo de la lectura (A → H)',
                    lambda: self.callbacks['ejemplo_lectura'](),
                    tipo='secondary').pack(fill='x', pady=(0, 7))
        row = self._frame(graf)
        row.pack(fill='x')
        row.columnconfigure((0, 1), weight=1)
        self._boton(row, 'Grafo aleatorio', self._generar, tipo='secondary').grid(row=0, column=0, sticky='ew', padx=(0, 3))
        self._boton(row, 'Nuevo manual', self._manual, tipo='secondary').grid(row=0, column=1, sticky='ew', padx=(3, 0))
        self.lbl_modo = tk.Label(graf, text='Ejemplo inicial cargado', bg=E.PANEL, fg=E.MUTED,
                                 font=(E.FONT, 10), anchor='w', wraplength=E.dp(295), justify='left')
        self.lbl_modo.pack(fill='x', pady=(9, 0))
        self._etiquetas.append(self.lbl_modo)

        aris = self._seccion('03', 'Aristas dirigidas')
        self.seccion_aristas = aris
        self._etiqueta(aris, 'Elige origen, destino y peso').pack(fill='x')
        fila = self._frame(aris)
        fila.pack(fill='x', pady=(5, 8))
        fila.columnconfigure((0, 1, 2), weight=1)
        for c, nombre in enumerate(('Origen', 'Destino', 'Peso')):
            self._etiqueta(fila, nombre).grid(row=0, column=c, sticky='w', padx=(0, 4))
        self.ent_origen = self._combo(fila, [], 'A')
        self.ent_origen.grid(row=1, column=0, sticky='ew', padx=(0, 4))
        self.ent_destino = self._combo(fila, [], 'B')
        self.ent_destino.grid(row=1, column=1, sticky='ew', padx=(0, 4))
        self.ent_peso = tk.Entry(
            fila, bg=E.INPUT, fg=E.TEXT, insertbackground=E.TEXT,
            selectbackground=E.BLUE, selectforeground='#FFFFFF',
            highlightbackground=E.BORDER, highlightcolor=E.ACCENT,
            highlightthickness=1, relief='flat', justify='center',
            font=(E.FONT, 10), width=6,
        )
        self.ent_peso.insert(0, '2')
        self.ent_peso.grid(row=1, column=2, sticky='ew')
        row = self._frame(aris)
        row.pack(fill='x', pady=(0, 8))
        row.columnconfigure((0, 1), weight=1)
        self._boton(row, 'Agregar arista', self._agregar, tipo='primary').grid(row=0, column=0, sticky='ew', padx=(0, 3))
        self._boton(row, 'Eliminar', self._eliminar, tipo='secondary').grid(row=0, column=1, sticky='ew', padx=(3, 0))
        self.tabla_aristas = ttk.Treeview(aris, columns=('origen', 'destino', 'peso'),
                                          show='headings', height=5, selectmode='browse',
                                          style='Dijkstra.Treeview')
        for col, titulo_col, ancho in [('origen', 'Origen', 65), ('destino', 'Destino', 65), ('peso', 'Peso', 65)]:
            self.tabla_aristas.heading(col, text=titulo_col)
            self.tabla_aristas.column(col, width=ancho, minwidth=45, anchor='center', stretch=True)
        self.tabla_aristas.pack(fill='x')
        self._etiqueta(aris, 'Se rechazan duplicados y ciclos.').pack(fill='x', pady=(7, 0))

        dijk = self._seccion('02', 'Camino más corto')
        self.seccion_busqueda = dijk
        selectors = self._frame(dijk)
        selectors.pack(fill='x', pady=(0, 8))
        selectors.columnconfigure((0, 1), weight=1)
        self._etiqueta(selectors, 'Origen').grid(row=0, column=0, sticky='w')
        self._etiqueta(selectors, 'Destino').grid(row=0, column=1, sticky='w')
        self.ent_origen_d = self._combo(selectors, [], 'A', ancho=10)
        self.ent_origen_d.grid(row=1, column=0, sticky='ew', padx=(0, 4))
        self.ent_destino_d = self._combo(selectors, [], 'G', ancho=10)
        self.ent_destino_d.grid(row=1, column=1, sticky='ew', padx=(4, 0))
        self._boton(dijk, 'Resolver ahora', self._resolver, tipo='primary').pack(fill='x', pady=(0, 7))
        self._boton(dijk, 'Iniciar simulación paso a paso', self._iniciar, tipo='blue').pack(fill='x', pady=(0, 7))
        row = self._frame(dijk)
        row.pack(fill='x')
        row.columnconfigure((0, 1), weight=1)
        self.btn_anterior = self._boton(row, '← Anterior', self._anterior, tipo='secondary')
        self.btn_anterior.grid(row=0, column=0, sticky='ew', padx=(0, 3))
        self.btn_siguiente = self._boton(row, 'Siguiente →', self._siguiente, tipo='warning')
        self.btn_siguiente.grid(row=0, column=1, sticky='ew', padx=(3, 0))
        self.estado_botones(False, False)
        self._etiqueta(dijk, 'También puedes elegir nodos haciendo clic sobre el dibujo.').pack(fill='x', pady=(8, 0))

        # Búsqueda inmediatamente debajo de la creación: acciones a la vista.
        aris.pack_forget()
        aris.pack(fill='x', padx=10, pady=(10, 2), after=dijk)
        avisos = self._seccion('04', 'Estado')
        self.lbl_estado = tk.Label(avisos, text='Listo para comenzar.', bg=E.PANEL,
                                    fg=E.MUTED, font=(E.FONT, 10), anchor='w',
                                    justify='left', wraplength=E.dp(295))
        self.lbl_estado.pack(fill='x')

    def aplicar_tema(self):
        """Reaplica colores de Modo Claro o Modo Oscuro sin perder valores ni selección."""
        self.configure(bg=E.PANEL)
        self.canvas_scroll.configure(bg=E.PANEL)
        self.interior.configure(bg=E.PANEL)
        for sec in self._secciones:
            sec.configure(bg=E.PANEL, highlightbackground=E.BORDER)
        for frm in self._frames_internos:
            frm.configure(bg=E.PANEL)
        for lbl in self._titulos:
            lbl.configure(bg=E.PANEL, fg=E.TEXT)
        for lbl in self._etiquetas:
            lbl.configure(bg=E.PANEL, fg=E.MUTED)
        for btn in self._botones:
            aplicar_estilo_boton(btn)
        self.entrada_nodos.configure(
            bg=E.INPUT,
            fg=E.TEXT,
            buttonbackground=E.BTN_SECONDARY_BG,
            insertbackground=E.TEXT,
            selectbackground=E.BLUE,
            selectforeground='#FFFFFF',
            highlightbackground=E.BORDER,
            highlightcolor=E.ACCENT,
        )
        self.ent_peso.configure(
            bg=E.INPUT,
            fg=E.TEXT,
            insertbackground=E.TEXT,
            selectbackground=E.BLUE,
            selectforeground='#FFFFFF',
            highlightbackground=E.BORDER,
            highlightcolor=E.ACCENT,
        )
        color_estado = (
            E.RED if self._estado_tipo == 'error'
            else E.GREEN if self._estado_tipo == 'ok'
            else E.MUTED
        )
        self.lbl_estado.configure(bg=E.PANEL, fg=color_estado)
        for ind in self.indicadores_ayuda:
            ind.aplicar_tema()

    def _cantidad(self):
        try:
            cantidad = int(self.entrada_nodos.get().strip())
        except ValueError as exc:
            raise ValueError('Ingresa una cantidad válida entre 7 y 16.') from exc
        if not (7 <= cantidad <= 16):
            raise ValueError('La cantidad de nodos debe estar entre 7 y 16.')
        return cantidad

    def _manejar(self, fn):
        try:
            fn()
        except (ValueError, RuntimeError) as exc:
            self.mostrar_alerta(str(exc), error=True)

    def _generar(self):
        self._manejar(lambda: self.callbacks['aleatorio'](self._cantidad()))

    def _manual(self):
        self._manejar(lambda: self.callbacks['manual'](self._cantidad()))

    def _agregar(self):
        self._manejar(lambda: self.callbacks['agregar'](
            self.ent_origen.get(), self.ent_destino.get(), self.ent_peso.get()))

    def _eliminar(self):
        seleccion = self.tabla_aristas.selection()
        if not seleccion:
            self.mostrar_alerta('Selecciona una fila de la lista de aristas para eliminarla.', error=True)
            return
        valores = self.tabla_aristas.item(seleccion[0], 'values')
        self._manejar(lambda: self.callbacks['eliminar'](valores[0], valores[1]))

    def _resolver(self):
        self._manejar(lambda: self.callbacks['resolver'](self.ent_origen_d.get(), self.ent_destino_d.get()))

    def _iniciar(self):
        self._manejar(lambda: self.callbacks['iniciar'](self.ent_origen_d.get(), self.ent_destino_d.get()))

    def _anterior(self):
        self._manejar(lambda: self.callbacks['anterior']())

    def _siguiente(self):
        self._manejar(lambda: self.callbacks['siguiente']())

    def estado_botones(self, anterior, siguiente):
        aplicar_estilo_boton(self.btn_anterior, bool(anterior))
        aplicar_estilo_boton(self.btn_siguiente, bool(siguiente))

    def mostrar_alerta(self, texto, error=False):
        self._estado_tipo = 'error' if error else 'ok'
        self.lbl_estado.configure(text=texto, fg=E.RED if error else E.GREEN)

    def fijar_modo(self, texto):
        self.lbl_modo.configure(text=texto)

    def fijar_nodos(self, cantidad):
        actuales = [chr(65 + i) for i in range(cantidad)]
        for selector in (self.ent_origen, self.ent_destino, self.ent_origen_d, self.ent_destino_d):
            anterior = selector.get()
            selector.configure(values=actuales)
            selector.set(anterior if anterior in actuales else actuales[0])
        self.ent_origen.set('A')
        self.ent_destino.set('B')
        self.ent_origen_d.set('A')
        self.ent_destino_d.set('G' if cantidad >= 7 else actuales[-1])
        self.entrada_nodos.delete(0, 'end')
        self.entrada_nodos.insert(0, str(cantidad))

    def actualizar_tabla_aristas(self, grafo):
        for item in self.tabla_aristas.get_children():
            self.tabla_aristas.delete(item)
        for nodo in sorted(grafo.nodos):
            for arista in sorted(grafo.obtener_sucesores(nodo), key=lambda a: a.destino.id_nodo):
                self.tabla_aristas.insert('', 'end', values=(
                    chr(nodo + 64), chr(arista.destino.id_nodo + 64),
                    formatear_numero(getattr(arista, 'peso_exacto', arista.peso))))

    def enfocar_aristas(self):
        """Desplaza el panel hasta el editor al iniciar modo manual."""
        self.update_idletasks()
        limite = max(1, self.interior.winfo_height() - self.canvas_scroll.winfo_height())
        self.canvas_scroll.yview_moveto(min(1, self.seccion_aristas.winfo_y() / limite))

    def enfocar_busqueda(self):
        """Desplaza el panel hasta los controles del algoritmo."""
        self.update_idletasks()
        limite = max(1, self.interior.winfo_height() - self.canvas_scroll.winfo_height())
        self.canvas_scroll.yview_moveto(min(1, self.seccion_busqueda.winfo_y() / limite))
