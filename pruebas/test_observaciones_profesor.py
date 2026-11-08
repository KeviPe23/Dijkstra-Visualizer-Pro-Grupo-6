"""Pruebas de regresión para las observaciones del docente.

Ejecutar desde la raíz: python -m unittest discover -s pruebas -p 'test_observaciones_profesor.py' -v
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algoritmos.dijkstra import Dijkstra
from modelos.arista import Arista
from modelos.grafo import Grafo
from servicios.validador_grafo import ValidadorGrafo


def grafo_ejemplo():
    g = Grafo()
    for i in range(1, 8):
        g.agregar_nodo(i)
    for u, v, p in [
        (1, 2, 1), (1, 3, 1),
        (2, 4, 2), (2, 5, 3),
        (3, 4, 3), (3, 5, 2),
        (5, 6, 1),
        (4, 7, 2), (6, 7, 2),
    ]:
        g.agregar_arista(u, v, p)
    return g


class ObservacionesProfesor(unittest.TestCase):
    def test_arista_repetida_mismo_peso_se_rechaza(self):
        g = grafo_ejemplo()
        cantidad = len(g.obtener_sucesores(1))
        with self.assertRaisesRegex(ValueError, "duplicadas"):
            g.agregar_arista(1, 2, 2)
        self.assertEqual(len(g.obtener_sucesores(1)), cantidad)

    def test_arista_repetida_distinto_peso_se_rechaza(self):
        g = grafo_ejemplo()
        with self.assertRaisesRegex(ValueError, "duplicadas"):
            g.agregar_arista(1, 2, 15)
        self.assertEqual(len(g.obtener_sucesores(1)), 2)

    def test_unica_ruta_minima_sin_vertices_aislados(self):
        motor = Dijkstra(grafo_ejemplo())
        motor.ejecutar(1)
        self.assertEqual(motor.distancias[7], 5)
        self.assertEqual(motor.obtener_caminos_minimos(7), [[1, 2, 4, 7]])
        self.assertEqual(set(motor.distancias), set(range(1, 8)))
        self.assertTrue(all(math.isfinite(motor.distancias[n]) for n in range(1, 8)))
        self.assertEqual(motor.predecesores[7], [4])

    def test_reconstruccion_elimina_duplicados_defensivamente(self):
        g = grafo_ejemplo()
        # Simula cargar desde un archivo antiguo que ya tenía duplicados.
        g.adyacencia[1].append(Arista(g.nodos[1], g.nodos[2], 2))
        d = Dijkstra(g)
        d.ejecutar(1)
        self.assertEqual(d.obtener_caminos_minimos(7), [[1, 2, 4, 7]])
        self.assertEqual(d.predecesores[2], [1])

    def test_todos_los_estados_tienen_distancias_y_predecesores(self):
        g = grafo_ejemplo()
        pasos = list(Dijkstra(g).ejecutar_paso_a_paso(1))
        self.assertEqual(pasos[0]["estado"], "INICIO")
        self.assertEqual(pasos[-1]["estado"], "FIN")
        for paso in pasos:
            self.assertEqual(set(paso["distancias"]), set(range(1, 8)))
            self.assertEqual(set(paso["predecesores"]), set(range(1, 8)))
            self.assertIsInstance(paso["iteracion"], int)
        self.assertEqual(pasos[0]["distancias"][1], 0)
        self.assertTrue(math.isinf(pasos[0]["distancias"][7]))
        self.assertEqual(pasos[-1]["distancias"][7], 5)
        self.assertEqual(pasos[-1]["predecesores"][7], [4])

    def test_estados_son_inmutables_entre_pasos(self):
        d = Dijkstra(grafo_ejemplo())
        generador = d.ejecutar_paso_a_paso(1)
        primer_estado = next(generador)
        list(generador)
        self.assertEqual(primer_estado["predecesores"][7], [])
        self.assertTrue(math.isinf(primer_estado["distancias"][7]))

    def test_relajacion_informa_candidato_y_cambio(self):
        d = Dijkstra(grafo_ejemplo())
        pasos = list(d.ejecutar_paso_a_paso(1))
        calculo = next(p for p in pasos if p["estado"] == "EVALUANDO" and p["nodo_actual"] == 4 and p["vecino"] == 7)
        self.assertEqual(calculo["peso"], 2)
        self.assertEqual(calculo["distancia_candidata"], 5)
        self.assertEqual(calculo["decision"], "MEJORA")
        empate = next(p for p in pasos if p["estado"] == "EVALUANDO" and p["nodo_actual"] == 6 and p["vecino"] == 7)
        self.assertEqual(empate["decision"], "SIN_CAMBIO")
        self.assertEqual(empate["distancia_candidata"], 6)
        self.assertEqual(empate["predecesores"][7], [4])

    def test_peso_cero_no_pierde_rutas_en_dag(self):
        g = Grafo()
        for n in range(1, 4):
            g.agregar_nodo(n)
        g.agregar_arista(1, 2, 1)
        g.agregar_arista(1, 3, 1)
        g.agregar_arista(3, 2, 0)
        self.assertFalse(ValidadorGrafo.tiene_ciclos(g))
        d = Dijkstra(g)
        d.ejecutar(1)
        self.assertEqual(d.obtener_caminos_minimos(2), [[1, 2], [1, 3, 2]])

    def test_pesos_invalidos_se_rechazan(self):
        g = grafo_ejemplo()
        for peso in (math.nan, math.inf, -math.inf, -1):
            with self.subTest(peso=peso):
                with self.assertRaises(ValueError):
                    g.agregar_arista(2, 3, peso)

    def test_repetir_ejecucion_reinicia_etiquetas(self):
        d = Dijkstra(grafo_ejemplo())
        d.ejecutar(1)
        d.ejecutar(7)
        self.assertEqual(d.distancias[7], 0)
        self.assertTrue(math.isinf(d.distancias[1]))
        self.assertEqual(d.obtener_caminos_minimos(7), [[7]])
        self.assertEqual(d.obtener_caminos_minimos(1), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
