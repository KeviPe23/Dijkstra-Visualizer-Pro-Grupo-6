"""Pruebas de reproducción del ejemplo de la Lectura 5.2 (página 9) en DAG."""
import math
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from algoritmos.dijkstra import Dijkstra
from modelos.grafo import Grafo
from servicios.validador_grafo import ValidadorGrafo
from ui.etiquetas import datos_etiqueta, etiquetas_descartadas
from ui.vistas_didacticas import datos_matriz, datos_historial
from ui import render_hd


def ejemplo_pdf():
    g=Grafo()
    for n in range(1,9):
        g.agregar_nodo(n, chr(64+n))
    for u,v,w in ((1,2,4),(1,3,3),(2,3,1),(2,5,3),
                  (3,4,2),(3,5,2),(4,5,1),(4,7,3),
                  (5,6,2),(5,7,2),(6,7,1),(6,8,3),(7,8,4)):
        g.agregar_arista(u,v,w)
    return g


class LecturaDAG(unittest.TestCase):
    def setUp(self):
        self.g = ejemplo_pdf()
        self.motor=Dijkstra(self.g)
        self.pasos=list(self.motor.ejecutar_paso_a_paso(1))

    def test_ejemplo_pdf_es_dag(self):
        self.assertFalse(ValidadorGrafo.tiene_ciclos(self.g))
        self.assertEqual(self.g.cantidad_nodos(),8)

    def test_pagina9_etiqueta_E_y_H(self):
        fin=self.pasos[-1]
        self.assertEqual(datos_etiqueta(fin,5),[('[5,C]',2)])
        self.assertEqual(datos_etiqueta(fin,8),[('[10,F]',4)])
        self.assertEqual(self.motor.obtener_caminos_minimos(8),[[1,3,5,6,8]])

    def test_numero_de_ronda_no_se_confunde_con_nivel(self):
        fin=self.pasos[-1]
        self.assertGreater(fin['iteracion'],4)
        self.assertEqual(fin['iteraciones_predecesor'][8][6],4)

    def test_propuestas_descartadas_se_registran(self):
        paso=next(s for s in self.pasos if s.get('estado')=='EVALUANDO' and
                  s.get('etiquetas_descartadas'))
        self.assertTrue(paso['etiquetas_descartadas'])
        self.assertTrue(etiquetas_descartadas(paso,paso['vecino']))
        self.assertFalse(etiquetas_descartadas(paso,1))
        self.assertEqual(self.pasos[0]['historial'],[])
        self.assertTrue(self.pasos[-1]['historial'])

    def test_matriz_orientada_con_diagonal_cero(self):
        columnas,filas=datos_matriz(self.g)
        self.assertEqual(columnas, ['Desde \\ Hasta','A','B','C','D','E','F','G','H'])
        self.assertEqual(filas[0][2], '4') # A -> B
        self.assertEqual(filas[1][1], '—') # B -> A ausente
        self.assertEqual(filas[0][1], '0') # A -> A sin bucle

    def test_historial_columnas_y_reemplazos(self):
        columnas,filas=datos_historial(self.g,self.pasos[-1])
        self.assertEqual(len(filas),8)
        self.assertEqual(len(columnas),self.pasos[-1]['iteracion']+2)
        self.assertIn('[0,–](0)',filas[0][1])
        self.assertTrue(any('× ' in celda for fila in filas for celda in fila))
        self.assertTrue(any('[10,F](4)' in celda for fila in filas for celda in fila))

    def test_reemplazo_real_tacha_etiqueta_anterior(self):
        g=Grafo()
        for n in range(1,8):
            g.agregar_nodo(n)
        for a,b,w in ((1,2,1),(1,3,5),(2,3,2)):
            g.agregar_arista(a,b,w)
        self.assertFalse(ValidadorGrafo.tiene_ciclos(g))
        pasos=list(Dijkstra(g).ejecutar_paso_a_paso(1))
        paso=next(s for s in pasos if s.get('estado')=='EVALUANDO'
                  and s.get('decision')=='MEJORA' and s.get('vecino')==3
                  and s.get('distancia_anterior')==5)
        self.assertIn('[5,A](1)', etiquetas_descartadas(paso,3))
        self.assertEqual(datos_etiqueta(paso,3),[('[3,B]',2)])

    def test_anti_alias_tachado(self):
        if not render_hd.disponible():
            self.skipTest('Requiere Pillow')
        paso=next(s for s in self.pasos if s.get('etiquetas_descartadas'))
        pos={n:(50+(n-1)*94,160+(n%2)*110) for n in self.g.nodos}
        aristas=[(u,a.destino.id_nodo,a.peso) for u in self.g.nodos for a in self.g.obtener_sucesores(u)]
        imagen=render_hd.renderizar(900,390,pos,aristas,estado=paso,suavizado=2)
        self.assertEqual(imagen.size,(900,390))

    def test_interfaz_herramientas_y_lectura(self):
        try:
            from ui.app import App
            app=App()
        except Exception:
            if sys.platform=='linux' and not os.getenv('DISPLAY'):
                self.skipTest('Requiere pantalla gráfica')
            raise
        try:
            app.cargar_ejemplo_lectura()
            app.manejador_ejecutar_dijkstra('A','H')
            app.update_idletasks();app.update()
            self.assertIn('[10,F](4)',app.panel_grafo.tabla.item('8','values')[-1])
            vh=app.panel_grafo.abrir_historial()
            vm=app.panel_grafo.abrir_matriz()
            app.update_idletasks();app.update()
            self.assertEqual(len(vh.tabla.get_children()),8)
            self.assertEqual(len(vm.tabla.get_children()),8)
            self.assertIn('4',vm.tabla.item('fila_0','values'))
            app.manejador_iniciar_pasos('A','H')
            app.manejador_siguiente_paso()
            app.update_idletasks();app.update()
            self.assertTrue(vh.winfo_exists())
            self.assertTrue(vm.winfo_exists())
        finally:
            app.destroy()


if __name__=='__main__':
    unittest.main()
