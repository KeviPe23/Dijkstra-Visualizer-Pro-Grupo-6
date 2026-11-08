"""Pruebas reales de eventos y controles gráficos (se omiten sin pantalla)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class VentanaGrafica(unittest.TestCase):
    def setUp(self):
        try:
            from ui.app import App
            self.app = App(mostrar_inicio=False)
            self.app.update_idletasks()
            self.app.update()
        except Exception as error:
            # Solo se omite en servidores Linux sin X11; Windows debe disponer de GUI.
            if sys.platform.startswith('linux') and not os.environ.get('DISPLAY'):
                self.skipTest('No hay pantalla X11 disponible: ' + str(error))
            raise

    def tearDown(self):
        if hasattr(self, 'app'):
            self.app.destroy()

    def test_ejemplo_ya_visible_y_busqueda(self):
        app = self.app
        self.assertEqual(len(app.grafo_actual.nodos), 7)
        self.assertEqual(len(app.panel_config.tabla_aristas.get_children()), 9)
        self.assertEqual((app.panel_config.ent_origen_d.get(), app.panel_config.ent_destino_d.get()), ('A', 'G'))
        self.assertGreater(app.panel_grafo.canvas.winfo_width(), 250)
        app.manejador_ejecutar_dijkstra('A', 'G')
        self.assertEqual(app.motor.distancias[7], 5)
        self.assertIn('5', app.panel_grafo.lbl_explicacion.cget('text'))
        self.assertEqual(app.panel_grafo.tabla.item('7', 'values')[2], 'D')

    def test_manual_aristas_y_rechazo_ciclo_y_duplicados(self):
        app = self.app
        app.manejador_iniciar_manual(7)
        self.assertFalse(any(app.grafo_actual.obtener_sucesores(i) for i in app.grafo_actual.nodos))
        app.manejador_agregar_arista('A', 'B', '3')
        self.assertEqual(len(app.panel_config.tabla_aristas.get_children()), 1)
        with self.assertRaises(ValueError):
            app.manejador_agregar_arista('A', 'B', '5')
        with self.assertRaises(ValueError):
            app.manejador_agregar_arista('B', 'A', '2')
        self.assertEqual(len(app.panel_config.tabla_aristas.get_children()), 1)
        app.manejador_eliminar_arista('A', 'B')
        self.assertFalse(app.grafo_actual.obtener_sucesores(1))

    def test_pasos_anterior_y_siguiente_y_ampliacion(self):
        app = self.app
        app.manejador_iniciar_pasos('A', 'G')
        self.assertEqual(app.indice_paso, 0)
        self.assertEqual(app.panel_grafo.tabla.item('1','values')[1], '0')
        app.manejador_siguiente_paso()
        self.assertEqual(app.indice_paso, 1)
        app.manejador_anterior_paso()
        self.assertEqual(app.indice_paso, 0)
        vista = app.panel_grafo.abrir_vista_ampliada()
        self.assertIsNotNone(vista)
        vista.update()
        vista.destroy()
        for _ in range(len(app.pasos)):
            app.manejador_siguiente_paso()
        self.assertEqual(app.panel_grafo.tabla.item('7','values')[2], 'D')
        self.assertEqual(app.panel_grafo.tabla.item('7','values')[1], '5')


if __name__ == '__main__':
    unittest.main()
