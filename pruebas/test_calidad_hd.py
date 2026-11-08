"""Pruebas del modo visual HD, sin necesidad de pantalla excepto la última."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui import render_hd


@unittest.skipUnless(render_hd.disponible(), 'Pillow opcional no instalado')
class CalidadHD(unittest.TestCase):
    def setUp(self):
        self.posiciones = {1:(50, 60),2:(190, 35),3:(190, 100),4:(340, 60)}
        self.aristas = [(1,2,2),(1,3,1),(2,4,3),(3,4,4)]

    def test_generacion_alta_calidad_y_dimensiones(self):
        image = render_hd.renderizar(410, 140, self.posiciones, self.aristas,
                                     visitados={1}, actual=2,
                                     rutas=[[1,2,4],[1,3,4]])
        self.assertEqual(image.size, (410, 140))
        self.assertEqual(image.mode, 'RGB')
        self.assertGreater(len(image.getcolors(410*140) or ()), 30,
                           'Se espera antialiasing: multiples tonos intermedios')

    def test_exportacion_4k_proporcional(self):
        imagen = render_hd.renderizar(410, 140, self.posiciones, self.aristas,
                                      escala_salida=3840/410, suavizado=2)
        self.assertEqual(imagen.width, 3840)
        self.assertEqual(imagen.height, round(140*3840/410))

    def test_pesos_decimales_y_nodos_sin_aristas(self):
        imagen = render_hd.renderizar(500, 250, {1:(100,120),2:(390,120),3:(250,200)},
                                      [(1,2,2.75)])
        self.assertEqual(imagen.size,(500,250))


class DesplazamientoHD(unittest.TestCase):
    def test_tabla_accesible_en_portatil(self):
        try:
            from ui.app import App
            app = App(mostrar_inicio=False)
        except Exception:
            if sys.platform.startswith('linux') and not os.environ.get('DISPLAY'):
                self.skipTest('Entorno sin pantalla gráfica')
            raise
        try:
            app.update_idletasks(); app.update()
            panel = app.panel_grafo
            app.manejador_ejecutar_dijkstra('A', 'G')
            self.assertEqual(panel.tabla.item('7','values')[2], 'D')
            panel.scroll_canvas.yview_moveto(1.0)
            app.update_idletasks(); app.update()
            self.assertGreater(panel.scroll_canvas.yview()[0], 0,
                               'La tabla debe poder verse al desplazarse abajo')
            panel.scroll_canvas.yview_moveto(0.0)
            app.update_idletasks(); app.update()
            if render_hd.disponible():
                self.assertIsNotNone(panel._foto_hd)
        finally:
            app.destroy()


if __name__ == '__main__':
    unittest.main()
