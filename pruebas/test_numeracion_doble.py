"""La numeración del ejemplo didáctico y la ronda real no se confunden."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from algoritmos.dijkstra import Dijkstra
from ui.etiquetas import datos_etiqueta, etiqueta_plana, etiquetas_descartadas
from ui.vistas_didacticas import datos_historial
from ui import render_hd
from pruebas.test_lectura_dag import ejemplo_pdf


class NumeracionDocente(unittest.TestCase):
    def setUp(self):
        self.grafo = ejemplo_pdf()
        self.motor = Dijkstra(self.grafo)
        self.pasos = list(self.motor.ejecutar_paso_a_paso(1))
        self.final = self.pasos[-1]

    def test_doc_pagina9_se_conserva(self):
        self.assertEqual(datos_etiqueta(self.final, 5), [('[5,C]', 2)])
        self.assertEqual(datos_etiqueta(self.final, 8), [('[10,F]', 4)])
        self.assertEqual(self.motor.obtener_caminos_minimos(8), [[1,3,5,6,8]])

    def test_numeracion_real_distinta_y_rastreable(self):
        self.assertEqual(datos_etiqueta(self.final, 8, 'ronda'), [('[10,F]', 6)])
        self.assertEqual(self.final['rondas_predecesor'][8][6], 6)
        self.assertIn('[10,F](6)', etiqueta_plana(self.final,8,'ronda'))
        self.assertEqual(datos_etiqueta(self.pasos[0],1,'ronda'), [('[0,–]', 0)])

    def test_ronda_grabada_inmutable_por_paso(self):
        previo = self.pasos[0]
        self.assertIsNone(previo['rondas_etiqueta'][8])
        self.assertEqual(previo['rondas_predecesor'][8], {})
        self.assertEqual(self.final['rondas_etiqueta'][8], 6)

    def test_descartadas_cambian_subindice(self):
        descartes = [s for s in self.pasos if s.get('etiquetas_descartadas')]
        self.assertTrue(descartes)
        for s in descartes:
            self.assertTrue(etiquetas_descartadas(s, s['vecino'], 'lectura'))
            self.assertTrue(etiquetas_descartadas(s, s['vecino'], 'ronda'))

    def test_historial_responde_al_selector(self):
        cab1, filas1 = datos_historial(self.grafo, self.final, 'lectura')
        cab2, filas2 = datos_historial(self.grafo, self.final, 'ronda')
        self.assertEqual(cab1, cab2)
        self.assertTrue(any('[10,F](4)' in c for row in filas1 for c in row))
        self.assertTrue(any('[10,F](6)' in c for row in filas2 for c in row))

    def test_renderizado_hd_en_ambos_modos(self):
        if not render_hd.disponible():
            self.skipTest('Pillow no instalado')
        from PIL import ImageChops
        pos = {n:(75+(n-1)*90, 120 if n%2 else 270) for n in self.grafo.nodos}
        aristas=[(u,a.destino.id_nodo,a.peso) for u in self.grafo.nodos
                 for a in self.grafo.obtener_sucesores(u)]
        lectura=render_hd.renderizar(840,420,pos,aristas,estado=self.final,modo_etiquetas='lectura')
        ronda=render_hd.renderizar(840,420,pos,aristas,estado=self.final,modo_etiquetas='ronda')
        self.assertEqual(lectura.size,ronda.size)
        self.assertIsNotNone(ImageChops.difference(lectura,ronda).getbbox())

    def test_interfaz_selector_y_4k(self):
        if sys.platform=='linux' and not os.getenv('DISPLAY'):
            self.skipTest('Requiere interfaz gráfica')
        from ui.app import App
        app=App()
        try:
            app.cargar_ejemplo_lectura()
            app.manejador_ejecutar_dijkstra('A','H')
            app.update_idletasks();app.update()
            panel=app.panel_grafo
            self.assertIn('[10,F](4)',panel.tabla.item('8','values')[-1])
            hist=panel.abrir_historial()
            self.assertTrue(any('[10,F](4)' in str(hist.tabla.item(i,'values'))
                                for i in hist.tabla.get_children()))
            panel.modo_numeracion.set('Dijkstra (ronda real)')
            panel._cambiar_numeracion()
            app.update_idletasks();app.update()
            self.assertIn('[10,F](6)',panel.tabla.item('8','values')[-1])
            self.assertTrue(any('[10,F](6)' in str(hist.tabla.item(i,'values'))
                                for i in hist.tabla.get_children()))
            im=panel._crear_imagen_hd(escala_salida=1, suavizado=2)
            self.assertGreater(im.width,400)
            self.assertGreater(im.height,200)
            panel.modo_numeracion.set('Lectura (etapas por ruta)')
            panel._cambiar_numeracion()
            self.assertIn('[10,F](4)',panel.tabla.item('8','values')[-1])
        finally:
            app.destroy()


if __name__ == '__main__':
    unittest.main()
