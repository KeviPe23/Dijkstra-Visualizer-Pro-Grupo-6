"""Dijkstra con estados inmutables, distancias y todos los predecesores óptimos."""
import math
from decimal import Decimal, localcontext
from typing import Dict, List, Set

from modelos.grafo import Grafo


class Dijkstra:
    def __init__(self, grafo: Grafo):
        self.grafo = grafo
        self.origen = None
        self.distancias: Dict[int, float] = {}
        # Cálculo exacto en decimal; «distancias» se conserva para compatibilidad
        # con las versiones anteriores y las pruebas académicas.
        self.distancias_exactas: Dict[int, Decimal] = {}
        self.predecesores: Dict[int, List[int]] = {}
        self.visitados: Set[int] = set()
        # Convención docente: n es el número de aristas desde el origen
        # por la ruta que justifica la etiqueta. No es el número de
        # extracciones del algoritmo (que se muestra por separado).
        self.iteraciones_etiqueta = {}
        self.iteraciones_predecesor = {}
        # Ronda REAL de selección del vértice que actualizó cada etiqueta.
        # Se mantiene separada del nivel usado en los ejemplos de la lectura.
        self.rondas_etiqueta = {}
        self.rondas_predecesor = {}
        self.rondas_seleccion: Dict[int, int] = {}
        self.historial = []  # Eventos de relajación, preservados por paso.

    @staticmethod
    def _a_float(valor: Decimal) -> float:
        """Representación legada, nunca utilizada para decidir un camino óptimo."""
        return float(valor)

    @staticmethod
    def _peso_exacto(arista) -> Decimal:
        return getattr(arista, 'peso_exacto', Decimal(str(arista.peso)))

    def distancia_exacta(self, vertice: int) -> Decimal:
        """Distancia calculada sin pérdida de decimales (Decimal('Infinity') si no se alcanza)."""
        return self.distancias_exactas.get(vertice, Decimal('Infinity'))

    def _estado(self, nombre, iteracion, nodo_actual=None, **datos):
        return {
            'estado': nombre, 'iteracion': iteracion, 'nodo_actual': nodo_actual,
            'visitados': set(self.visitados), 'distancias': dict(self.distancias),
            'distancias_exactas': dict(self.distancias_exactas),
            'predecesores': {n:list(ps) for n,ps in self.predecesores.items()},
            'iteraciones_etiqueta': dict(self.iteraciones_etiqueta),
            'iteraciones_predecesor': {
                n: dict(pasos) for n, pasos in self.iteraciones_predecesor.items()
            },
            'rondas_etiqueta': dict(self.rondas_etiqueta),
            'rondas_predecesor': {
                n: dict(pasos) for n, pasos in self.rondas_predecesor.items()
            },
            'rondas_seleccion': dict(self.rondas_seleccion),
            'historial': [dict(evento) for evento in self.historial],
            **datos,
        }

    def ejecutar(self, id_origen):
        for _ in self.ejecutar_paso_a_paso(id_origen):
            pass

    def ejecutar_paso_a_paso(self, id_origen):
        if id_origen not in self.grafo.nodos:
            raise ValueError('El nodo de origen no existe en el grafo.')
        self.origen = id_origen
        self.distancias = {n:math.inf for n in self.grafo.nodos}
        self.distancias_exactas = {n:Decimal('Infinity') for n in self.grafo.nodos}
        self.predecesores = {n:[] for n in self.grafo.nodos}
        self.distancias[id_origen] = 0.0
        self.distancias_exactas[id_origen] = Decimal(0)
        self.iteraciones_etiqueta = {n: None for n in self.grafo.nodos}
        self.iteraciones_etiqueta[id_origen] = 0
        self.iteraciones_predecesor = {n: {} for n in self.grafo.nodos}
        self.rondas_etiqueta = {n: None for n in self.grafo.nodos}
        self.rondas_etiqueta[id_origen] = 0
        self.rondas_predecesor = {n: {} for n in self.grafo.nodos}
        self.rondas_seleccion = {}
        self.historial = []
        self.visitados.clear()
        pendientes = set(self.grafo.nodos)
        iteracion = 0
        yield self._estado('INICIO', iteracion, id_origen)
        while pendientes:
            actual = min(pendientes, key=lambda n: (self.distancias_exactas[n], n))
            if self.distancias_exactas[actual].is_infinite():
                break
            pendientes.remove(actual)
            self.visitados.add(actual)
            iteracion += 1
            self.rondas_seleccion[iteracion] = actual
            yield self._estado('VISITADO', iteracion, actual)
            for arista in self.grafo.obtener_sucesores(actual):
                vecino = arista.destino.id_nodo
                anterior_exacto = self.distancias_exactas[vecino]
                anterior = self.distancias[vecino]
                preds_anteriores = list(self.predecesores[vecino])
                # Precisión de hasta 128 cifras para las distancias y los pesos
                # escritos por el usuario. Nunca comparar floats redondeados.
                with localcontext() as ctx:
                    ctx.prec = 128
                    candidata_exacta = self.distancias_exactas[actual] + self._peso_exacto(arista)
                candidata = self._a_float(candidata_exacta)
                decision = 'SIN_CAMBIO'
                niveles_previos = dict(self.iteraciones_predecesor[vecino])
                rondas_previas = dict(self.rondas_predecesor[vecino])
                # Etiquetado por niveles de ruta: A→C→E tiene n=2 en E,
                # aun si C fue el único vértice seleccionado anteriormente.
                if actual == id_origen:
                    nivel_ruta = 1
                else:
                    anteriores_actual = self.iteraciones_predecesor[actual]
                    nivel_ruta = 1 + min(anteriores_actual.values()) if anteriores_actual else iteracion
                # Empate SOLO si las sumas decimales son realmente iguales.
                # isclose con tolerancia relativa confundía rutas diferentes de peso alto.
                empate = candidata_exacta == anterior_exacto and candidata_exacta.is_finite()
                if vecino not in self.visitados and candidata_exacta < anterior_exacto:
                    self.distancias_exactas[vecino] = candidata_exacta
                    self.distancias[vecino] = candidata
                    self.predecesores[vecino] = [actual]
                    self.iteraciones_etiqueta[vecino] = nivel_ruta
                    self.iteraciones_predecesor[vecino] = {actual: nivel_ruta}
                    self.rondas_predecesor[vecino] = {actual: iteracion}
                    self.rondas_etiqueta[vecino] = iteracion
                    decision = 'MEJORA'
                elif empate and vecino != self.origen and actual not in self.predecesores[vecino]:
                    # Puede existir un empate por peso cero aun si ya se visitó el vecino.
                    self.predecesores[vecino].append(actual)
                    self.predecesores[vecino].sort()
                    self.iteraciones_predecesor[vecino][actual] = nivel_ruta
                    self.rondas_predecesor[vecino][actual] = iteracion
                    self.rondas_etiqueta[vecino] = min(self.rondas_predecesor[vecino].values())
                    self.iteraciones_etiqueta[vecino] = min(
                        self.iteraciones_predecesor[vecino].values())
                    decision = 'EMPATE'
                # Mantener un registro explícito de etiquetas conservadas y
                # descartadas (para la matriz histórica y el tachado visual).
                descartadas = []
                descartadas_ronda = []
                if decision == 'MEJORA' and not math.isinf(anterior):
                    descartadas = [(anterior_exacto, p, niveles_previos.get(p))
                                   for p in preds_anteriores]
                    descartadas_ronda = [(anterior_exacto, p, rondas_previas.get(p))
                                         for p in preds_anteriores]
                elif decision == 'SIN_CAMBIO' and not math.isinf(candidata) and not empate:
                    descartadas = [(candidata_exacta, actual, nivel_ruta)]
                    descartadas_ronda = [(candidata_exacta, actual, iteracion)]
                evento = {
                    'iteracion': iteracion, 'origen': actual, 'vertice': vecino,
                    'peso': arista.peso, 'peso_exacto': self._peso_exacto(arista),
                    'anterior': anterior, 'anterior_exacto': anterior_exacto,
                    'candidata': candidata, 'candidata_exacta': candidata_exacta,
                    'decision': decision,
                    'nivel_candidato': nivel_ruta,
                    'ronda_candidato': iteracion,
                    'antes': tuple((anterior_exacto, p, niveles_previos.get(p)) for p in preds_anteriores),
                    'despues': tuple((self.distancias_exactas[vecino], p,
                                      self.iteraciones_predecesor[vecino].get(p))
                                     for p in self.predecesores[vecino]),
                    'antes_ronda': tuple((anterior_exacto, p, rondas_previas.get(p)) for p in preds_anteriores),
                    'despues_ronda': tuple((self.distancias_exactas[vecino], p,
                                          self.rondas_predecesor[vecino].get(p))
                                         for p in self.predecesores[vecino]),
                    'descartadas': tuple(descartadas),
                    'descartadas_ronda': tuple(descartadas_ronda),
                }
                self.historial.append(evento)
                yield self._estado('EVALUANDO', iteracion, actual,
                                   vecino=vecino, peso=arista.peso,
                                   distancia_anterior=anterior,
                                   distancia_anterior_exacta=anterior_exacto,
                                   distancia_candidata=candidata,
                                   distancia_candidata_exacta=candidata_exacta,
                                   peso_exacto=self._peso_exacto(arista),
                                   predecesores_anteriores=preds_anteriores,
                                   etiquetas_descartadas=tuple(descartadas),
                                   etiquetas_descartadas_ronda=tuple(descartadas_ronda),
                                   decision=decision,
                                   hubo_cambio=(decision != 'SIN_CAMBIO'))
        yield self._estado('FIN', iteracion)

    def contar_caminos_minimos(self, id_destino):
        """Cuenta las rutas sin construir todas sus listas (útil para DAG densos)."""
        if self.origen is None or self.distancia_exacta(id_destino).is_infinite():
            return 0
        memo = {}
        def contar(v, visitando):
            if v == self.origen:
                return 1
            if v in memo:
                return memo[v]
            if v in visitando:
                return 0
            resultado = sum(contar(u, visitando | {v}) for u in set(self.predecesores.get(v, [])))
            memo[v] = resultado
            return resultado
        return contar(id_destino, set())

    def obtener_caminos_minimos(self, id_destino: int, limite=None) -> List[List[int]]:
        """Reconstruye caminos únicos; 'limite' evita congelar la GUI en grafos densos."""
        if self.origen is None or self.distancia_exacta(id_destino).is_infinite():
            return []
        if limite is not None and limite <= 0:
            return []
        rutas = set()
        def reconstruir(v, inverso, visitados):
            if limite is not None and len(rutas) >= limite:
                return
            if v == self.origen:
                rutas.add(tuple(reversed(inverso)))
                return
            for p in sorted(set(self.predecesores.get(v, []))):
                if p not in visitados:
                    reconstruir(p, inverso + [p], visitados | {p})
        reconstruir(id_destino, [id_destino], {id_destino})
        return [list(r) for r in sorted(rutas)]
