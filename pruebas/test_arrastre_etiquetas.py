"""Arrastre real de etiquetas: independiente del grafo y de los cálculos."""
import os
import sys
import unittest
from types import SimpleNamespace
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ui import render_hd


class ArrastreEtiquetas(unittest.TestCase):
    def setUp(self):
        from ui.app import App
        try:
            self.app = App(mostrar_inicio=False)
            self.app.update_idletasks()
            self.app.update()
        except Exception:
            if sys.platform.startswith('linux') and not os.environ.get('DISPLAY'):
                self.skipTest('Entorno sin pantalla')
            raise
        self.app.manejador_ejecutar_dijkstra('A', 'G')
        self.app.update_idletasks()
        self.app.update()
        self.panel = self.app.panel_grafo

    def tearDown(self):
        if hasattr(self, 'app'):
            self.app.destroy()

    def _etiqueta(self):
        for n, caja in self.panel.cajas_etiquetas.items():
            x1, y1, x2, y2 = caja
            x, y = x1+min(10,(x2-x1)/2), y1+min(8,(y2-y1)/2)
            if self.panel._nodo_cercano(x,y) is None:
                return n, caja, x, y
        self.fail('No se encontró etiqueta visible separada de un nodo')

    def _drag(self):
        n, (x1,y1,x2,y2), x,y = self._etiqueta()
        nodos_antes = dict(self.panel.posiciones)
        distancias_antes = dict(self.app.motor.distancias)
        self.panel._presionar(SimpleNamespace(x=x,y=y))
        self.assertEqual(self.panel.etiqueta_pulsada, n)
        self.assertIsNone(self.panel.nodo_pulsado)
        self.panel._mover(SimpleNamespace(x=x+46,y=y+35))
        self.panel._soltar(SimpleNamespace(x=x+46,y=y+35))
        return n, (x1,y1,x2,y2), nodos_antes, distancias_antes

    def test_arrastre_independiente_de_los_vertices_y_dijkstra(self):
        n, anterior, nodos_antes, distancias_antes = self._drag()
        nueva = self.panel.cajas_etiquetas[n]
        self.assertIn(n,self.panel.posiciones_etiquetas)
        self.assertEqual(nodos_antes,self.panel.posiciones)
        self.assertEqual(distancias_antes,self.app.motor.distancias)
        self.assertGreater(nueva[0]-anterior[0],20)
        self.assertGreater(nueva[1]-anterior[1],15)
        self.assertEqual(self.app.motor.obtener_caminos_minimos(7),[[1,2,4,7]])

    def test_doble_clic_restaura_posicion_automatica(self):
        n, _, _, _ = self._drag()
        x1,y1,x2,y2 = self.panel.cajas_etiquetas[n]
        self.panel._restaurar_etiqueta(SimpleNamespace(x=(x1+x2)/2,y=(y1+y2)/2))
        self.assertNotIn(n,self.panel.posiciones_etiquetas)

    def test_arrastre_persiste_en_pasos_y_se_limpia_en_nuevo_grafo(self):
        n, _, _, _ = self._drag()
        posicion_relativa = self.panel.posiciones_etiquetas[n]
        self.app.manejador_iniciar_pasos('A','G')
        self.app.manejador_siguiente_paso()
        self.assertEqual(self.panel.posiciones_etiquetas[n],posicion_relativa)
        self.app.manejador_iniciar_manual(7)
        self.assertEqual(self.panel.posiciones_etiquetas,{})

    def test_arrastre_en_modo_sin_pillow(self):
        original = render_hd.disponible
        try:
            render_hd.disponible = lambda: False
            self.panel.dibujar_grafo()
            self.assertTrue(self.panel.cajas_etiquetas)
            n, _, nodos_antes, _ = self._drag()
            self.assertIn(n,self.panel.posiciones_etiquetas)
            self.assertEqual(nodos_antes,self.panel.posiciones)
        finally:
            render_hd.disponible = original
            self.panel.dibujar_grafo()

    def test_arrastre_se_conserva_en_ambas_numeraciones(self):
        n, _, vertices, distancias = self._drag()
        anterior = self.panel.posiciones_etiquetas[n]
        for modo in ('Dijkstra (ronda real)', 'Lectura (etapas por ruta)'):
            self.panel.modo_numeracion.set(modo)
            self.panel._cambiar_numeracion()
            self.assertEqual(self.panel.posiciones_etiquetas[n], anterior)
            self.assertIn(n, self.panel.cajas_etiquetas)
            self.assertEqual(self.panel.posiciones, vertices)
            self.assertEqual(self.app.motor.distancias, distancias)


class HitboxesRenderizador(unittest.TestCase):
    @unittest.skipUnless(render_hd.disponible(),'Pillow requerido')
    def test_metadata_hd_y_desplazamiento_exportado(self):
        from modelos.grafo import Grafo
        from algoritmos.dijkstra import Dijkstra
        g = Grafo()
        for n in range(1,8): g.agregar_nodo(n)
        for u,v,p in ((1,2,2),(1,3,1),(2,7,3),(3,7,4)):
            g.agregar_arista(u,v,p)
        d = Dijkstra(g)
        estados=list(d.ejecutar_paso_a_paso(1))
        pos={1:(90,170),2:(230,95),3:(230,245),7:(410,170),4:(140,330),5:(260,340),6:(420,330)}
        aris=[(1,2,2),(1,3,1),(2,7,3),(3,7,4)]
        base={}
        render_hd.renderizar(520,400,pos,aris,estado=estados[-1],cajas_etiquetas=base)
        n=1
        x1,y1,x2,y2=base[n]
        manual={n:(x1-pos[n][0]+40,y1-pos[n][1]+30)}
        nuevo={}
        render_hd.renderizar(520,400,pos,aris,estado=estados[-1],
                            posiciones_etiquetas=manual,cajas_etiquetas=nuevo)
        self.assertAlmostEqual(nuevo[n][0], x1+40, delta=2)
        self.assertAlmostEqual(nuevo[n][1], y1+30, delta=2)
        hd={}
        im=render_hd.renderizar(520,400,pos,aris,estado=estados[-1],
                   posiciones_etiquetas=manual,cajas_etiquetas=hd,escala_salida=2)
        self.assertEqual(im.size,(1040,800))
        self.assertAlmostEqual(hd[n][0],nuevo[n][0],delta=2)

if __name__=='__main__':
    unittest.main()
