"""Regresiones de precisión: comparación exacta, rutas y presentación."""
import math
import os
import sys
import unittest
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modelos.grafo import Grafo
from algoritmos.dijkstra import Dijkstra
from ui.etiquetas import datos_etiqueta
from ui.numeros import formatear_numero
from ui.vistas_didacticas import datos_matriz, datos_historial


def graph(edges, n=7):
    g = Grafo()
    for node in range(1, n + 1):
        g.agregar_nodo(node, chr(64 + node))
    for u, v, w in edges:
        g.agregar_arista(u, v, w)
    return g


class PrecisionFinal(unittest.TestCase):
    def test_grande_rutas_no_se_declaran_iguales(self):
        g = graph([(1, 2, 1000000000.0001), (1, 3, 1000000000), (3, 2, 0)])
        d = Dijkstra(g); d.ejecutar(1)
        self.assertEqual(d.obtener_caminos_minimos(2), [[1, 3, 2]])
        self.assertEqual(d.contar_caminos_minimos(2), 1)
        self.assertEqual(d.distancia_exacta(2), Decimal('1000000000'))

    def test_peso_subnanometrico_positivo_no_se_convierte_en_cero(self):
        g = graph([(1, 2, Decimal('0.0000000000001')), (1, 3, 0), (3, 2, 0)])
        d = Dijkstra(g); d.ejecutar(1)
        self.assertEqual(d.distancia_exacta(2), 0)
        self.assertEqual(d.obtener_caminos_minimos(2), [[1, 3, 2]])
        self.assertEqual(g.obtener_sucesores(1)[0].peso_exacto, Decimal('1e-13'))

    def test_grande_diferencia_menor_que_ulp_float(self):
        g = graph([(1, 2, Decimal('999999999999.00001')),
                   (1, 3, Decimal('999999999999')), (3, 2, Decimal('0'))])
        d = Dijkstra(g); d.ejecutar(1)
        self.assertEqual(d.distancia_exacta(2), Decimal('999999999999'))
        self.assertEqual(d.obtener_caminos_minimos(2), [[1, 3, 2]])

    def test_precisiones_de_entrada_se_conservan_en_matriz(self):
        g = graph([(1, 2, Decimal('999999999999.00001')), (2, 3, Decimal('0.0000000000001'))])
        headers, rows = datos_matriz(g)
        self.assertEqual(rows[0][2], '999999999999.00001')
        self.assertIn('0.0000000000001', str(rows[1]))
        self.assertEqual(formatear_numero(Decimal('1.0000000001')), '1.0000000001')

    def test_empates_decimales_reales_se_mantienen(self):
        g = graph([(1, 2, 0.1), (2, 4, 0.2), (1, 3, 0.3), (3, 4, 0)])
        d = Dijkstra(g); estados=list(d.ejecutar_paso_a_paso(1))
        self.assertEqual(d.obtener_caminos_minimos(4), [[1, 2, 4], [1, 3, 4]])
        self.assertEqual(d.distancia_exacta(4), Decimal('0.3'))
        self.assertEqual(datos_etiqueta(estados[-1],4)[0][0], '[0.3,B]')

    def test_historico_no_oculta_diferencias(self):
        g = graph([(1, 2, Decimal('1000000000.0001')),
                   (1, 3, Decimal('1000000000')),
                   (3, 2, 0)])
        d=Dijkstra(g); estados=list(d.ejecutar_paso_a_paso(1))
        _,rows=datos_historial(g,estados[-1])
        fila_b=next(r for r in rows if r[0]=='B')
        self.assertIn('1000000000.0001', str(fila_b))
        self.assertEqual(d.obtener_caminos_minimos(2), [[1,3,2]])

    def test_peso_invalido_no_modifica_grafo(self):
        g=graph([])
        for w in (Decimal('-0.0001'), Decimal('NaN'), Decimal('Infinity'), Decimal('1e13'), True):
            with self.subTest(w=w), self.assertRaises(ValueError):
                g.agregar_arista(1,2,w)
        self.assertEqual(g.obtener_sucesores(1), [])

    def test_cantidad_rutas_se_conserva_con_peso_cero(self):
        g=graph([(1, 2, 0), (1, 3, 0), (2, 3, 0), (2, 7, 0), (3,7,0)])
        d=Dijkstra(g);d.ejecutar(1)
        self.assertEqual(d.obtener_caminos_minimos(7),[[1,2,3,7],[1,2,7],[1,3,7]])
        self.assertEqual(d.contar_caminos_minimos(7),3)


if __name__=='__main__': unittest.main()
