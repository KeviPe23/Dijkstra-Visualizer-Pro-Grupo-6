"""Pruebas de la convención [d,V]_(n) solicitada por el profesor."""
import math
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from algoritmos.dijkstra import Dijkstra
from modelos.grafo import Grafo
from ui.etiquetas import datos_etiqueta, etiqueta_plana
from ui import render_hd


def ejemplo():
    g = Grafo()
    for n in range(1, 8):
        g.agregar_nodo(n, chr(64+n))
    for u,v,p in [
        (1,2,1),(1,3,1),
        (2,4,2),(2,5,3),
        (3,4,3),(3,5,2),
        (5,6,1),
        (4,7,2),(6,7,2),
    ]:
        g.agregar_arista(u,v,p)
    return g


class EtiquetasDocente(unittest.TestCase):
    def setUp(self):
        self.grafo = ejemplo()
        self.motor = Dijkstra(self.grafo)
        self.pasos = list(self.motor.ejecutar_paso_a_paso(1))

    def test_inicializacion_origen_y_no_alcanzados(self):
        inicial = self.pasos[0]
        self.assertEqual(datos_etiqueta(inicial, 1), [('[0,–]',0)])
        self.assertEqual(datos_etiqueta(inicial, 7), [('[∞,–]',None)])
        self.assertEqual(inicial['iteracion'], 0)

    def test_mejora_registra_iteracion_y_predecesor(self):
        paso = next(s for s in self.pasos if s['estado']=='EVALUANDO' and
                    s['nodo_actual']==1 and s['vecino']==2)
        self.assertEqual(datos_etiqueta(paso,2), [('[1,A]',1)])
        self.assertEqual(paso['iteraciones_predecesor'][2][1], 1)

    def test_ruta_unica_muestra_una_etiqueta_con_iteracion(self):
        empate = next(s for s in self.pasos if s.get('decision')=='SIN_CAMBIO'
                      and s.get('vecino') == 7 and s.get('nodo_actual') == 6)
        self.assertEqual(datos_etiqueta(empate,7), [('[5,D]',3)])
        self.assertIn('[5,D](3)', etiqueta_plana(empate,7))
        self.assertNotIn('[5,F]', etiqueta_plana(empate,7))
        self.assertEqual(self.motor.obtener_caminos_minimos(7), [[1,2,4,7]])

    def test_cada_estado_conserva_historial_inmutable(self):
        self.assertEqual(datos_etiqueta(self.pasos[0],7), [('[∞,–]',None)])
        self.assertEqual(datos_etiqueta(self.pasos[-1],7),
                         [('[5,D]',3)])

    def test_nueva_ejecucion_restauracion_de_etiquetas(self):
        pasos = list(self.motor.ejecutar_paso_a_paso(3))
        self.assertEqual(datos_etiqueta(pasos[0],3), [('[0,–]',0)])
        self.assertEqual(datos_etiqueta(pasos[0],2), [('[∞,–]',None)])

    @unittest.skipUnless(render_hd.disponible(), 'Pillow no instalado')
    def test_grafo_hd_con_etiquetas_diferente_al_grafo_sin_etiquetas(self):
        pos={1:(75,170),2:(210,80),3:(210,260),4:(350,80),5:(350,260),6:(500,260),7:(610,170)}
        aris = [(1,2,1),(1,3,1),(2,4,2),(2,5,3),(3,4,3),(3,5,2),(5,6,1),(4,7,2),(6,7,2)]
        con = render_hd.renderizar(540,380,pos,aris, estado=self.pasos[-1])
        sin = render_hd.renderizar(540,380,pos,aris)
        from PIL import ImageChops
        self.assertIsNotNone(ImageChops.difference(con,sin).getbbox())
        self.assertEqual(con.size,(540,380))

    def test_interfaz_tabla_y_interruptor_etiquetas(self):
        try:
            from ui.app import App
            app = App(mostrar_inicio=False)
        except Exception:
            if sys.platform.startswith('linux') and not os.getenv('DISPLAY'):
                self.skipTest('No hay servidor gráfico')
            raise
        try:
            app.manejador_ejecutar_dijkstra('A','G')
            app.update_idletasks(); app.update()
            tabla = app.panel_grafo.tabla
            self.assertEqual(tabla.item('7','values')[2], 'D')
            self.assertIn('[5,D](3)', tabla.item('7','values')[-1])
            self.assertNotIn('[5,F]', tabla.item('7','values')[-1])
            self.assertTrue(app.panel_grafo.mostrar_etiquetas.get())
            app.panel_grafo.mostrar_etiquetas.set(False)
            app.panel_grafo.dibujar_grafo()
            self.assertFalse(app.panel_grafo.mostrar_etiquetas.get())
        finally:
            app.destroy()


if __name__ == '__main__':
    unittest.main()
