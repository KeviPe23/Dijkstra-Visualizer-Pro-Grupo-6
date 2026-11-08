import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algoritmos.dijkstra import Dijkstra
from generadores.grafo_aleatorio import GeneradorAleatorio
from modelos.grafo import Grafo
from servicios.validador_grafo import ValidadorGrafo


class MejorasDAG(unittest.TestCase):
    def test_eliminar_arista(self):
        g = Grafo()
        for n in range(1, 8):
            g.agregar_nodo(n)
        g.agregar_arista(1, 2, 3)
        self.assertFalse(g.eliminar_arista(2, 1))
        self.assertTrue(g.eliminar_arista(1, 2))
        self.assertFalse(g.eliminar_arista(1, 2))
        self.assertEqual(g.obtener_sucesores(1), [])

    def test_cantidad_nodos_grafo_aleatorio(self):
        for n in (7, 8, 12, 16):
            for _ in range(10):
                g = GeneradorAleatorio.generar_dag(n)
                self.assertEqual(g.cantidad_nodos(), n)
                self.assertFalse(ValidadorGrafo.tiene_ciclos(g))
                self.assertTrue(all(a.peso >= 0 for u in g.nodos for a in g.obtener_sucesores(u)))

    def test_invalido_peso_booleano(self):
        g = Grafo()
        g.agregar_nodo(1)
        g.agregar_nodo(2)
        with self.assertRaises(ValueError):
            g.agregar_arista(1, 2, True)

    def test_pesos_decimales_sin_falsos_errores_por_precision(self):
        g = Grafo()
        for n in range(1, 8):
            g.agregar_nodo(n)
        g.agregar_arista(1, 2, 0.1)
        g.agregar_arista(2, 7, 0.2)
        g.agregar_arista(1, 7, 0.3)
        d = Dijkstra(g)
        d.ejecutar(1)
        self.assertEqual(d.contar_caminos_minimos(7), 2)
        self.assertEqual(d.obtener_caminos_minimos(7), [[1, 2, 7], [1, 7]])

    def test_limite_de_rutas_evita_congelamiento(self):
        g = Grafo()
        for n in range(1, 17):
            g.agregar_nodo(n)
        for u in range(1, 17):
            for v in range(u + 1, 17):
                g.agregar_arista(u, v, 0)
        d = Dijkstra(g)
        d.ejecutar(1)
        self.assertEqual(d.contar_caminos_minimos(16), 2**14)
        self.assertEqual(len(d.obtener_caminos_minimos(16, limite=30)), 30)

    def test_tabla_estados_completos_en_dag_aleatorio(self):
        for _ in range(10):
            g = GeneradorAleatorio.generar_dag(10)
            pasos = list(Dijkstra(g).ejecutar_paso_a_paso(1))
            self.assertEqual(pasos[0]['estado'], 'INICIO')
            self.assertEqual(pasos[-1]['estado'], 'FIN')
            for estado in pasos:
                self.assertEqual(len(estado['distancias']), 10)
                self.assertEqual(len(estado['predecesores']), 10)
                self.assertTrue(set(estado['visitados']).issubset(g.nodos))


if __name__ == '__main__':
    unittest.main()
