"""Vistas complementarias de Dijkstra: historial y matriz ponderada DAG.

Se abren en ventanas independientes para no estrechar el grafo principal.
El historial contiene una columna por vértice procesado, tal como la lectura.
Soporta cambio dinámico entre Modo Claro y Modo Oscuro.
"""
import math
import tkinter as tk
from tkinter import ttk
from ui import estilos as E
from ui.etiquetas import etiqueta_tripleta, letra
from ui.numeros import formatear_numero


def datos_matriz(grafo):
    """Matriz de *aristas*, no de caminos mínimos: fila u, columna v = peso u→v."""
    ids = sorted(grafo.nodos)
    pesos = {(u, a.destino.id_nodo): getattr(a, 'peso_exacto', a.peso)
             for u in ids for a in grafo.obtener_sucesores(u)}
    filas = []
    for u in ids:
        filas.append([letra(u)] + [formatear_numero(pesos[(u, v)]) if (u, v) in pesos
                                     else ('0' if u == v else '—') for v in ids])
    return ['Desde \\ Hasta'] + [letra(v) for v in ids], filas


def datos_historial(grafo, estado, modo="lectura"):
    """Construye la matriz histórica por rondas reales de Dijkstra.

    En modo «lectura», n identifica las etapas de propagación del ejemplo;
    en «ronda», n es la ronda real de asignación de la etiqueta.
    Las columnas siempre representan las rondas reales.
    """
    ids = sorted(grafo.nodos)
    eventos = estado.get('historial', []) if estado else []
    ronda_max = int(estado.get('iteracion', 0)) if estado else 0
    origenes_ronda = dict(estado.get('rondas_seleccion', {})) if estado else {}
    for e in eventos:
        origenes_ronda.setdefault(e['iteracion'], e['origen'])
    headers = ['Vértice', 'Inicio (0)'] + [f'{i} · {letra(origenes_ronda[i])}'
        if i in origenes_ronda else f'Ronda {i}' for i in range(1, ronda_max+1)]
    origen = None
    if estado:
        for n, ps in estado.get('iteraciones_etiqueta', {}).items():
            if ps == 0 and not estado.get('predecesores', {}).get(n):
                origen = n
                break
    campos = {(n, i): [] for n in ids for i in range(1, ronda_max+1)}
    for e in eventos:
        vertice, i = e['vertice'], e['iteracion']
        clave_antes = 'antes_ronda' if modo == 'ronda' else 'antes'
        clave_despues = 'despues_ronda' if modo == 'ronda' else 'despues'
        anterior = [etiqueta_tripleta(*t) for t in e[clave_antes]]
        nuevo = [etiqueta_tripleta(*t) for t in e[clave_despues]]
        if e['decision'] == 'MEJORA':
            contenido = ('× ' + ' / '.join(anterior) + ' → ' if anterior else '') + ' / '.join(nuevo)
        elif e['decision'] == 'EMPATE':
            agregado = [x for x in nuevo if x not in anterior]
            contenido = '= ' + ' / '.join(agregado)
        else:
            if math.isinf(e.get('candidata_exacta', e['candidata'])):
                continue
            subindice = e['ronda_candidato'] if modo == 'ronda' else e['nivel_candidato']
            contenido = '× ' + etiqueta_tripleta(e.get('candidata_exacta', e['candidata']), e['origen'], subindice)
        if (vertice, i) in campos:
            campos[(vertice, i)].append(contenido)
    filas = [[letra(n), '[0,–](0)' if n == origen else '—'] + [
        ' · '.join(campos[(n, i)]) if campos[(n,i)] else '—'
        for i in range(1,ronda_max+1)] for n in ids]
    return headers, filas


class VentanaTabla(tk.Toplevel):
    """Tabla legible con ambos desplazamientos, sin deformar la ventana original."""
    def __init__(self, master, titulo, explicacion, ancho_columna=115):
        super().__init__(master)
        self.title('Dijkstra Visualizer Pro · ' + titulo)
        self.configure(bg=E.BG)
        self._ancho_columna = ancho_columna
        pantalla_w = self.winfo_screenwidth()
        pantalla_h = self.winfo_screenheight()
        self.geometry(f'{min(1070, pantalla_w-95)}x{min(630, pantalla_h-100)}')
        self.minsize(min(620,pantalla_w-30),min(400,pantalla_h-30))
        self.cab = tk.Frame(self, bg=E.BG)
        self.cab.pack(fill='x', padx=18, pady=(15,11))
        self.lbl_titulo = tk.Label(self.cab, text=titulo, bg=E.BG, fg=E.TEXT,
                                   font=(E.FONT,16,'bold'))
        self.lbl_titulo.pack(anchor='w')
        self.descripcion = tk.Label(self.cab, text=explicacion, bg=E.BG, fg=E.MUTED,
             font=(E.FONT,10), anchor='w', justify='left', wraplength=850)
        self.descripcion.pack(fill='x', pady=(5,0))
        self.descripcion.bind('<Configure>', lambda ev: self.descripcion.configure(
            wraplength=max(300,ev.width-20)))
        self.marco = tk.Frame(self, bg=E.PANEL, highlightbackground=E.BORDER,
                              highlightthickness=1)
        self.marco.pack(fill='both', expand=True, padx=16, pady=(0,13))
        self.tabla = ttk.Treeview(self.marco, show='headings', selectmode='browse',
                                  style='Dijkstra.Treeview')
        vy = ttk.Scrollbar(self.marco,orient='vertical',command=self.tabla.yview)
        hx = ttk.Scrollbar(self.marco,orient='horizontal',command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=vy.set,xscrollcommand=hx.set)
        self.marco.grid_columnconfigure(0,weight=1)
        self.marco.grid_rowconfigure(0,weight=1)
        self.tabla.grid(row=0,column=0,sticky='nsew')
        vy.grid(row=0,column=1,sticky='ns')
        hx.grid(row=1,column=0,sticky='ew')
        self.pie = tk.Label(self, text='Desplázate horizontalmente para ver las últimas rondas o vértices.',
                            fg=E.MUTED,bg=E.BG,font=(E.FONT,9),anchor='w')
        self.pie.pack(fill='x', padx=18,pady=(0,11))

    def aplicar_tema(self):
        if not self.winfo_exists():
            return
        self.configure(bg=E.BG)
        self.cab.configure(bg=E.BG)
        self.lbl_titulo.configure(bg=E.BG, fg=E.TEXT)
        self.descripcion.configure(bg=E.BG, fg=E.MUTED)
        self.marco.configure(bg=E.PANEL, highlightbackground=E.BORDER)
        self.pie.configure(bg=E.BG, fg=E.MUTED)

    def actualizar(self, encabezados, filas):
        columnas = tuple(f'c{i}' for i in range(len(encabezados)))
        self.tabla.configure(columns=columnas)
        for i,(col,titulo) in enumerate(zip(columnas,encabezados)):
            ancho = (86 if i==0 else max(self._ancho_columna,
                      min(360,max(90,len(titulo)*8))))
            self.tabla.heading(col,text=titulo)
            self.tabla.column(col,width=ancho,minwidth=65,stretch=False,anchor='center')
        self.tabla.delete(*self.tabla.get_children())
        for i,fila in enumerate(filas):
            self.tabla.insert('','end',iid=f'fila_{i}',values=fila)
