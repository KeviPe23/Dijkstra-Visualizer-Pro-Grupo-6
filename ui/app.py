"""Aplicación de escritorio: pantalla de inicio, Modo Claro/Oscuro dinámico y simulador DAG HD."""
import math
from decimal import Decimal, InvalidOperation
import os
from ui.dpi import activar_dpi_nativo
activar_dpi_nativo()
import tkinter as tk
from tkinter import ttk

from algoritmos.dijkstra import Dijkstra
from generadores.grafo_aleatorio import GeneradorAleatorio
from modelos.grafo import Grafo
from servicios.validador_grafo import ValidadorGrafo
from ui import estilos as E
from ui.componentes import InterruptorTema
from ui.panel_configuracion import PanelConfiguracion
from ui.panel_grafo import PanelGrafo
from ui.ventana_inicio import VentanaInicio
from ui.numeros import formatear_numero


class App(tk.Tk):
    def __init__(self, mostrar_inicio: bool = True):
        super().__init__()
        # Iniciar siempre en Modo Claro predeterminado.
        E.aplicar_tema(False)

        self.title('Dijkstra Visualizer Pro · Simulador DAG')
        escala_tk = float(self.tk.call('tk', 'scaling'))
        E.UI_SCALE = max(.90, min(2.0, escala_tk / (96 / 72)))
        ancho_pantalla, alto_pantalla = self.winfo_screenwidth(), self.winfo_screenheight()
        ancho = min(int(1510 * E.UI_SCALE), int(ancho_pantalla * .94))
        alto = min(int(925 * E.UI_SCALE), int(alto_pantalla * .90))
        pos_x = max(0, (ancho_pantalla - ancho) // 2)
        pos_y = max(0, (alto_pantalla - alto) // 2 - E.dp(14))
        self.geometry(f'{ancho}x{alto}+{pos_x}+{pos_y}')
        self.minsize(min(int(970 * E.UI_SCALE), ancho_pantalla),
                     min(int(650 * E.UI_SCALE), alto_pantalla))
        self.option_add('*Font', (E.FONT, 10))
        icono = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'icono.ico')
        try:
            self.iconbitmap(icono)
        except (OSError, tk.TclError):
            pass

        self.grafo_actual = None
        self.motor = None
        self.pasos = []
        self.indice_paso = -1
        self.busqueda = None
        self._pendiente_destino = False
        self._interfaz_construida = False
        self.pantalla_inicio = None
        self.panel_config = None
        self.panel_grafo = None
        self.switch_tema = None

        self._definir_estilos()

        if mostrar_inicio:
            self.configure(bg=VentanaInicio.BG_INICIO)
            self.pantalla_inicio = VentanaInicio(self, self._iniciar_desde_portada)
            self.pantalla_inicio.pack(fill='both', expand=True)
        else:
            self.configure(bg=E.BG)
            self._construir_ventana()
            self.cargar_ejemplo()

    @property
    def en_pantalla_inicio(self) -> bool:
        return self.pantalla_inicio is not None and bool(self.pantalla_inicio.winfo_exists())

    def _iniciar_desde_portada(self, nodos_iniciales: int):
        """Transición desde la pantalla de inicio al simulador principal en Modo Claro."""
        self.pantalla_inicio = None
        E.aplicar_tema(False)
        self._definir_estilos()
        self.configure(bg=E.BG)
        self._construir_ventana()
        self.manejador_generar_aleatorio(nodos_iniciales)
        self.panel_config.ent_origen_d.set('A')
        self.panel_config.ent_destino_d.set(self._letra(nodos_iniciales))

    def _asegurar_ventana_principal(self):
        if not self._interfaz_construida:
            if self.pantalla_inicio is not None and self.pantalla_inicio.winfo_exists():
                self.pantalla_inicio.destroy()
            self.pantalla_inicio = None
            self.configure(bg=E.BG)
            self._construir_ventana()

    def _definir_estilos(self):
        estilo = ttk.Style(self)
        estilo.theme_use('clam')
        estilo.configure(
            'Dijkstra.Treeview',
            background=E.PANEL_ALT,
            fieldbackground=E.PANEL_ALT,
            foreground=E.TEXT,
            bordercolor=E.BORDER,
            lightcolor=E.PANEL_ALT,
            darkcolor=E.PANEL_ALT,
            font=(E.FONT, 11),
            rowheight=E.dp(30),
            relief='flat',
            borderwidth=0,
        )
        estilo.configure(
            'Dijkstra.Treeview.Heading',
            background=E.BTN_SECONDARY_BG,
            foreground=E.TEXT,
            bordercolor=E.BORDER,
            lightcolor=E.BTN_SECONDARY_BG,
            darkcolor=E.BTN_SECONDARY_BG,
            font=(E.FONT, 10, 'bold'),
            relief='flat',
            padding=(E.dp(5), E.dp(8)),
        )
        estilo.map(
            'Dijkstra.Treeview',
            background=[('selected', E.BLUE)],
            foreground=[('selected', '#FFFFFF')],
        )
        estilo.map(
            'Dijkstra.Treeview.Heading',
            background=[('active', E.BTN_SECONDARY_HOVER)],
            foreground=[('active', E.TEXT)],
        )
        estilo.configure(
            'Dijkstra.TCombobox',
            fieldbackground=E.INPUT,
            background=E.BTN_SECONDARY_BG,
            foreground=E.TEXT,
            arrowcolor=E.TEXT,
            bordercolor=E.BORDER,
            lightcolor=E.BORDER,
            darkcolor=E.BORDER,
            padding=(7, 6),
        )
        estilo.map(
            'Dijkstra.TCombobox',
            fieldbackground=[('readonly', E.INPUT)],
            background=[('readonly', E.BTN_SECONDARY_BG), ('active', E.BTN_SECONDARY_HOVER)],
            foreground=[('readonly', E.TEXT)],
            arrowcolor=[('readonly', E.TEXT), ('active', E.TEXT)],
            selectforeground=[('readonly', E.TEXT)],
            selectbackground=[('readonly', E.INPUT)],
        )
        for orientacion in ('Vertical.TScrollbar', 'Horizontal.TScrollbar'):
            estilo.configure(
                orientacion,
                background=E.SCROLL_THUMB,
                troughcolor=E.SCROLL_TROUGH,
                arrowcolor=E.MUTED,
                bordercolor=E.SCROLL_TROUGH,
                lightcolor=E.SCROLL_THUMB,
                darkcolor=E.SCROLL_THUMB,
            )
            estilo.map(
                orientacion,
                background=[('active', E.SCROLL_THUMB_HOVER), ('disabled', E.SCROLL_TROUGH)],
                arrowcolor=[('active', E.TEXT)],
            )
        self.option_add('*TCombobox*Listbox.background', E.PANEL)
        self.option_add('*TCombobox*Listbox.foreground', E.TEXT)
        self.option_add('*TCombobox*Listbox.selectBackground', E.BLUE)
        self.option_add('*TCombobox*Listbox.selectForeground', '#FFFFFF')

    def _construir_ventana(self):
        if self._interfaz_construida:
            return
        self._interfaz_construida = True

        self.barra = tk.Frame(self, bg=E.BG, height=E.dp(73))
        self.barra.pack(fill='x', padx=17, pady=(12, 8))
        self.barra.pack_propagate(False)

        self.cabecera = tk.Frame(self.barra, bg=E.BG)
        self.cabecera.pack(side='left', fill='y')
        self.lbl_titulo_app = tk.Label(self.cabecera, text='Dijkstra Visualizer Pro', bg=E.BG, fg=E.TEXT,
                                       font=(E.FONT, 22, 'bold'), anchor='w')
        self.lbl_titulo_app.pack(anchor='w')
        self.lbl_subtitulo_app = tk.Label(self.cabecera, text='Grafos dirigidos y acíclicos · 7 a 16 vértices',
                                          bg=E.BG, fg=E.MUTED, font=(E.FONT, 10), anchor='w')
        self.lbl_subtitulo_app.pack(anchor='w')

        self.controles_barra = tk.Frame(self.barra, bg=E.BG)
        self.controles_barra.pack(side='right', fill='y')

        self.switch_tema = InterruptorTema(
            self.controles_barra,
            command=self.cambiar_tema,
            activo_inicial=E.MODO_OSCURO,
            texto='Modo Oscuro',
        )
        self.switch_tema.pack(side='right', padx=(E.dp(16), 0), pady=E.dp(12))

        self.insignia = tk.Label(
            self.controles_barra,
            text='DAG  •  PESOS NO NEGATIVOS',
            bg=E.PANEL_ALT,
            fg=E.GREEN,
            highlightbackground=E.BORDER,
            highlightthickness=1,
            padx=13,
            pady=8,
            font=(E.FONT, 9, 'bold'),
        )
        self.insignia.pack(side='right', pady=6)

        self.central = tk.Frame(self, bg=E.BG)
        self.central.pack(fill='both', expand=True, padx=16, pady=(0, 8))
        self.lateral = tk.Frame(self.central, bg=E.PANEL, width=E.dp(356))
        self.lateral.pack(side='left', fill='y', padx=(0, 10))
        self.lateral.pack_propagate(False)
        callbacks = {
            'ejemplo': self.cargar_ejemplo,
            'ejemplo_lectura': self.cargar_ejemplo_lectura,
            'aleatorio': self.manejador_generar_aleatorio,
            'manual': self.manejador_iniciar_manual,
            'agregar': self.manejador_agregar_arista,
            'eliminar': self.manejador_eliminar_arista,
            'resolver': self.manejador_ejecutar_dijkstra,
            'iniciar': self.manejador_iniciar_pasos,
            'anterior': self.manejador_anterior_paso,
            'siguiente': self.manejador_siguiente_paso,
        }
        self.panel_config = PanelConfiguracion(self.lateral, callbacks)
        self.panel_config.pack(fill='both', expand=True)
        self.panel_grafo = PanelGrafo(self.central, on_nodo_click=self.manejador_nodo_click)
        self.panel_grafo.pack(side='left', fill='both', expand=True)
        self.pie = tk.Frame(self, bg=E.BG, height=E.dp(26))
        self.pie.pack(fill='x', padx=17, pady=(0, 7))
        self.lbl_pie_izq = tk.Label(
            self.pie,
            text='Primero crea o carga un grafo; después elige origen y destino.',
            bg=E.BG, fg=E.MUTED, font=(E.FONT, 9),
        )
        self.lbl_pie_izq.pack(side='left')
        self.lbl_pie_der = tk.Label(
            self.pie,
            text='Dibujo HD · DPI nativo · PNG 4K',
            bg=E.BG, fg=E.MUTED, font=(E.FONT, 9),
        )
        self.lbl_pie_der.pack(side='right')

    def cambiar_tema(self, modo_oscuro: bool):
        """Alterna en caliente entre Modo Claro y Modo Oscuro en toda la aplicación."""
        E.aplicar_tema(modo_oscuro)
        self._definir_estilos()
        if not self._interfaz_construida:
            return
        self.configure(bg=E.BG)
        self.barra.configure(bg=E.BG)
        self.cabecera.configure(bg=E.BG)
        self.lbl_titulo_app.configure(bg=E.BG, fg=E.TEXT)
        self.lbl_subtitulo_app.configure(bg=E.BG, fg=E.MUTED)
        self.controles_barra.configure(bg=E.BG)
        self.insignia.configure(bg=E.PANEL_ALT, fg=E.GREEN, highlightbackground=E.BORDER)
        if self.switch_tema.get() != bool(modo_oscuro):
            self.switch_tema.set(modo_oscuro, notificar=False)
        else:
            self.switch_tema.aplicar_tema()
        self.central.configure(bg=E.BG)
        self.lateral.configure(bg=E.PANEL)
        self.pie.configure(bg=E.BG)
        self.lbl_pie_izq.configure(bg=E.BG, fg=E.MUTED)
        self.lbl_pie_der.configure(bg=E.BG, fg=E.MUTED)
        self.panel_config.aplicar_tema()
        self.panel_grafo.aplicar_tema()

    @staticmethod
    def _letra(id_nodo):
        return chr(64 + id_nodo) if 1 <= id_nodo <= 26 else str(id_nodo)

    @staticmethod
    def _parse_nodo(texto, existentes):
        valor = str(texto).strip().upper()
        if len(valor) == 1 and 'A' <= valor <= 'Z':
            id_nodo = ord(valor) - 64
        else:
            try:
                id_nodo = int(valor)
            except ValueError as exc:
                raise ValueError('Selecciona un vértice válido (A, B, C...).') from exc
        if id_nodo not in existentes:
            raise ValueError('El vértice elegido no existe en el grafo actual.')
        return id_nodo

    def _cambiar_grafo(self, nuevo, modo, disposicion='niveles'):
        self._asegurar_ventana_principal()
        self.grafo_actual = nuevo
        self._invalidar_pasos()
        self.panel_config.fijar_nodos(nuevo.cantidad_nodos())
        self.panel_config.fijar_modo(modo)
        self.panel_config.actualizar_tabla_aristas(nuevo)
        self.panel_grafo.set_grafo(nuevo, disposicion=disposicion)
        self.panel_grafo.mostrar_mensaje(
            'Grafo listo. Puedes modificar aristas o comenzar la búsqueda de caminos mínimos.')
        self.panel_config.mostrar_alerta(modo)

    def _invalidar_pasos(self):
        self.motor = None
        self.pasos = []
        self.indice_paso = -1
        self.busqueda = None
        self._pendiente_destino = False
        if self.panel_config is not None:
            self.panel_config.estado_botones(False, False)

    def cargar_ejemplo(self):
        """Un solo clic: DAG de 7 nodos alcanzables con un único camino mínimo de costo 5."""
        grafo = Grafo()
        for i in range(1, 8):
            grafo.agregar_nodo(i, self._letra(i))
        aristas = (
            (1, 2, 1), (1, 3, 1),
            (2, 4, 2), (2, 5, 3),
            (3, 4, 3), (3, 5, 2),
            (5, 6, 1),
            (4, 7, 2), (6, 7, 2),
        )
        for u, v, peso in aristas:
            grafo.agregar_arista(u, v, peso)
        self._cambiar_grafo(grafo, 'Ejemplo cargado: A → G (único camino mínimo de costo 5; 7 vértices conectados).')
        w = max(650, self.panel_grafo.canvas.winfo_width())
        h = max(340, self.panel_grafo.canvas.winfo_height())
        ubicacion = {
            1:(.08,.50), 2:(.24,.28), 3:(.24,.72),
            4:(.46,.28), 5:(.46,.72), 6:(.66,.72), 7:(.88,.50)
        }
        self.panel_grafo.posiciones = {n:(x*w,y*h) for n,(x,y) in ubicacion.items()}
        self.panel_grafo._size = (w,h)
        self.panel_grafo._posiciones_manuales = True
        self.panel_grafo._modo_disposicion = 'fija'
        self.panel_grafo.tipo_layout_actual = 'ejemplo'
        self.panel_grafo.dibujar_grafo()
        self.panel_config.ent_origen_d.set('A')
        self.panel_config.ent_destino_d.set('G')
        self.panel_grafo.mostrar_mensaje(
            'Ejemplo listo: selecciona A y G, o pulsa «Resolver ahora» / «Iniciar simulación paso a paso».')

    def cargar_ejemplo_lectura(self):
        """Caso de la página 9 de la Lectura 5.2, transcrito como DAG.

        Origen A, destino H. E = [5,C](2), H = [10,F](4).
        Las aristas corresponden a la matriz orientada de la lectura.
        """
        grafo = Grafo()
        for n in range(1, 9):
            grafo.agregar_nodo(n, self._letra(n))
        aristas = ((1,2,4), (1,3,3), (2,3,1), (2,5,3),
                   (3,4,2), (3,5,2), (4,5,1), (4,7,3),
                   (5,6,2), (5,7,2), (6,7,1), (6,8,3), (7,8,4))
        for u,v,peso in aristas:
            grafo.agregar_arista(u,v,peso)
        assert not ValidadorGrafo.tiene_ciclos(grafo)
        self._cambiar_grafo(grafo, 'Lectura pág. 9: DAG de 8 vértices; ruta A → H.')
        w = max(650, self.panel_grafo.canvas.winfo_width())
        h = max(340, self.panel_grafo.canvas.winfo_height())
        ubicacion = {1:(.08,.50),2:(.24,.77),3:(.24,.24),4:(.43,.23),
                     5:(.43,.72),6:(.65,.73),7:(.65,.25),8:(.88,.50)}
        self.panel_grafo.posiciones = {
            n:(x*w,y*h) for n,(x,y) in ubicacion.items()}
        self.panel_grafo._size = (w,h)
        self.panel_grafo._posiciones_manuales = True
        self.panel_grafo._modo_disposicion = 'fija'
        self.panel_grafo.tipo_layout_actual = 'lectura'
        self.panel_grafo.dibujar_grafo()
        self.panel_config.ent_origen_d.set('A')
        self.panel_config.ent_destino_d.set('H')
        self.panel_grafo.mostrar_mensaje(
            'Ejemplo de la lectura cargado (DAG): A → H. E debe tener [5,C](2); H [10,F](4).')

    def manejador_generar_aleatorio(self, num_nodos):
        self._cambiar_grafo(GeneradorAleatorio.generar_dag(num_nodos),
                            f'Grafo aleatorio DAG con {num_nodos} vértices.',
                            disposicion='variada')

    def manejador_iniciar_manual(self, num_nodos):
        grafo = Grafo()
        for i in range(1, num_nodos + 1):
            grafo.agregar_nodo(i, self._letra(i))
        self._cambiar_grafo(grafo, f'Grafo manual vacío: {num_nodos} vértices.',
                            disposicion='variada')
        self.panel_grafo.mostrar_mensaje(
            'Grafo manual: elige origen, destino y peso en «Aristas dirigidas», luego presiona «Agregar arista».')
        self.panel_config.enfocar_aristas()

    def manejador_agregar_arista(self, origen, destino, peso):
        if self.grafo_actual is None:
            raise ValueError('Primero carga o crea un grafo.')
        u = self._parse_nodo(origen, self.grafo_actual.nodos)
        v = self._parse_nodo(destino, self.grafo_actual.nodos)
        if u == v:
            raise ValueError('Un vértice no puede conectarse consigo mismo: formaría un ciclo.')
        texto_peso = str(peso).strip().replace(',', '.')
        if texto_peso.startswith('-'):
            raise ValueError('Dijkstra no admite pesos negativos.')
        try:
            peso_num = Decimal(texto_peso)
        except InvalidOperation as exc:
            raise ValueError('El peso debe ser un número no negativo, por ejemplo 2 o 2.5.') from exc
        self.grafo_actual.agregar_arista(u, v, peso_num)
        if ValidadorGrafo.tiene_ciclos(self.grafo_actual):
            self.grafo_actual.adyacencia[u].pop()
            raise ValueError('Arista rechazada: crearía un ciclo. El grafo debe ser DAG.')
        self._actualizar_tras_edicion(f'Arista {self._letra(u)} → {self._letra(v)} agregada (peso {formatear_numero(self.grafo_actual.adyacencia[u][-1].peso_exacto)}).')

    def manejador_eliminar_arista(self, origen, destino):
        if self.grafo_actual is None:
            raise ValueError('No hay grafo cargado.')
        u = self._parse_nodo(origen, self.grafo_actual.nodos)
        v = self._parse_nodo(destino, self.grafo_actual.nodos)
        if not self.grafo_actual.eliminar_arista(u, v):
            raise ValueError('La arista seleccionada ya no existe.')
        self._actualizar_tras_edicion(f'Arista {self._letra(u)} → {self._letra(v)} eliminada.')

    def _actualizar_tras_edicion(self, mensaje):
        self._invalidar_pasos()
        self.panel_config.actualizar_tabla_aristas(self.grafo_actual)
        self.panel_grafo.set_grafo(self.grafo_actual, conservar_posiciones=True)
        self.panel_grafo.mostrar_mensaje(mensaje)
        self.panel_config.mostrar_alerta(mensaje)

    def _parse_busqueda(self, origen, destino):
        if self.grafo_actual is None:
            raise ValueError('Primero crea un grafo.')
        return (self._parse_nodo(origen, self.grafo_actual.nodos),
                self._parse_nodo(destino, self.grafo_actual.nodos))

    def _resultado(self, motor, origen, destino):
        if motor.distancia_exacta(destino).is_infinite():
            self.panel_grafo.caminos = []
            self.panel_grafo.mostrar_mensaje(
                f'No existe un camino dirigido desde {self._letra(origen)} hasta {self._letra(destino)}.', E.RED)
            self.panel_grafo.mostrar_resumen('Destino inalcanzable (distancia ∞).')
            return
        rutas = motor.obtener_caminos_minimos(destino, limite=30)
        total = motor.contar_caminos_minimos(destino)
        self.panel_grafo.caminos = rutas
        distancia = motor.distancia_exacta(destino)
        mostrar = [' → '.join(self._letra(n) for n in ruta) for ruta in rutas[:4]]
        descripcion = ' | '.join(mostrar)
        if total > 4:
            descripcion += f' | y {total-4} más'
        # La vista colorea hasta 30 rutas para evitar saturación y congelamientos.
        # Informar el límite sin confundir el total real con las rutas resaltadas.
        aviso_visual = (f' Se resaltan {len(rutas)} de {total} rutas en el grafo.'
                        if total > len(rutas) else '')
        self.panel_grafo.mostrar_mensaje(
            f'Distancia mínima de {self._letra(origen)} a {self._letra(destino)}: '
            f'{formatear_numero(distancia)}. '
            f'{total} camino(s) óptimo(s) distinto(s): {descripcion}.{aviso_visual}', E.GREEN)
        self.panel_grafo.mostrar_resumen('Rutas: ' + descripcion + aviso_visual)

    def manejador_ejecutar_dijkstra(self, origen, destino):
        u, v = self._parse_busqueda(origen, destino)
        self._invalidar_pasos()
        motor = Dijkstra(self.grafo_actual)
        self.pasos = list(motor.ejecutar_paso_a_paso(u))
        self.motor = motor
        self.busqueda = (u, v)
        self.indice_paso = len(self.pasos) - 1
        estado = self.pasos[-1]
        self.panel_grafo.actualizar_tabla_etiquetas(estado, len(self.pasos), len(self.pasos))
        self._resultado(motor, u, v)
        self.panel_grafo.dibujar_grafo()
        self.panel_config.estado_botones(len(self.pasos) > 1, False)
        self.panel_config.mostrar_alerta('Solución calculada correctamente.')

    def manejador_iniciar_pasos(self, origen, destino):
        u,v = self._parse_busqueda(origen, destino)
        self._invalidar_pasos()
        self.motor = Dijkstra(self.grafo_actual)
        self.pasos = list(self.motor.ejecutar_paso_a_paso(u))
        self.indice_paso = 0
        self.busqueda = (u,v)
        self._mostrar_paso()
        self.panel_config.mostrar_alerta('Simulación iniciada. Pulsa «Siguiente →» para avanzar.')

    def _mostrar_paso(self):
        paso = self.pasos[self.indice_paso]
        self.panel_grafo.caminos = []
        self.panel_grafo.actualizar_tabla_etiquetas(paso, self.indice_paso+1, len(self.pasos))
        etapa = paso['estado']
        actual = paso.get('nodo_actual')
        if etapa == 'INICIO':
            letra_o = self._letra(actual)
            mensaje = (f'Iteración 0 (Inicialización): d({letra_o}) = 0, π({letra_o}) = —; '
                       'las demás distancias son ∞ y los predecesores están vacíos.')
        elif etapa == 'VISITADO':
            letra_a = self._letra(actual)
            preds_a = ', '.join(self._letra(p) for p in paso['predecesores'].get(actual, [])) or '—'
            mensaje = (f"Iteración {paso['iteracion']} · Se selecciona el nodo {letra_a}: "
                       f"d({letra_a}) = {self.panel_grafo._distancia(paso.get('distancias_exactas', paso['distancias'])[actual])}, "
                       f"π({letra_a}) = {{{preds_a}}}. Su etiqueta queda definitiva.")
        elif etapa == 'EVALUANDO':
            vecino = paso['vecino']
            letra_v = self._letra(vecino)
            anterior = self.panel_grafo._distancia(paso.get('distancia_anterior_exacta', paso['distancia_anterior']))
            candidato = self.panel_grafo._distancia(paso.get('distancia_candidata_exacta', paso['distancia_candidata']))
            despues = self.panel_grafo._distancia(
                paso.get('distancias_exactas', paso['distancias'])[vecino])
            preds_v = ', '.join(self._letra(p) for p in paso['predecesores'].get(vecino, [])) or '—'
            accion = {'MEJORA': 'Mejora: se reemplaza la etiqueta anterior; si existía, se muestra tachada.',
                      'EMPATE': 'Empate: se conserva la distancia y se añade otro predecesor óptimo.',
                      'SIN_CAMBIO': 'La propuesta no mejora: se descarta y se conserva la mejor etiqueta.'}[paso['decision']]
            mensaje = (f"Iteración {paso['iteracion']} · {self._letra(actual)} → {letra_v} (peso {formatear_numero(paso.get('peso_exacto', paso['peso']))}): "
                       f'd anterior = {anterior}; candidata = {candidato} ➔ d({letra_v}) = {despues}, '
                       f'π({letra_v}) = {{{preds_v}}}. {accion}')
        else:
            self._resultado(self.motor, *self.busqueda)
            mensaje = None
        if mensaje is not None:
            self.panel_grafo.mostrar_mensaje(mensaje)
            self.panel_grafo.mostrar_resumen(
                'Compara los dos significados de n con el selector «Numeración n»: '
                'la lectura representa etapas de ruta; Dijkstra registra las rondas reales.')
        self.panel_grafo.dibujar_grafo()
        self.panel_config.estado_botones(self.indice_paso > 0,
                                         self.indice_paso < len(self.pasos)-1)

    def manejador_siguiente_paso(self):
        if self.pasos and self.indice_paso < len(self.pasos)-1:
            self.indice_paso += 1
            self._mostrar_paso()
        else:
            self.panel_config.mostrar_alerta('La simulación ya está en el último paso.')

    def manejador_anterior_paso(self):
        if self.pasos and self.indice_paso > 0:
            self.indice_paso -= 1
            self._mostrar_paso()
        else:
            self.panel_config.mostrar_alerta('La simulación ya está en el primer paso.')

    def manejador_nodo_click(self, nodo_id):
        letra = self._letra(nodo_id)
        if not self._pendiente_destino:
            self.panel_config.ent_origen_d.set(letra)
            self._pendiente_destino = True
            self.panel_config.mostrar_alerta(f'Origen {letra} seleccionado. Haz clic en el destino.')
        else:
            origen_actual = self.panel_config.ent_origen_d.get()
            if letra == origen_actual:
                self.panel_config.mostrar_alerta(
                    f'Origen {letra} activo. Haz clic en un vértice distinto para el destino.')
                return
            self.panel_config.ent_destino_d.set(letra)
            self._pendiente_destino = False
            self.manejador_ejecutar_dijkstra(origen_actual, letra)
