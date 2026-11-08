import random
from modelos.grafo import Grafo
from servicios.validador_grafo import ValidadorGrafo

class GeneradorAleatorio:
    """
    Clase utilitaria para generar Grafos Dirigidos Acíclicos (DAG) aleatorios,
    cumpliendo con las restricciones del proyecto.
    """
    
    @staticmethod
    def generar_dag(num_nodos: int, min_peso: int = 1, max_peso: int = 20) -> Grafo:
        """
        Genera un grafo aleatorio asegurando que sea dirigido, conexo hacia adelante
        y sin ciclos (DAG).
        
        Args:
            num_nodos: Cantidad de vértices (entre 7 y 16 según enunciado).
            min_peso: Peso mínimo de la arista.
            max_peso: Peso máximo de la arista.
            
        Retorna:
            Instancia de Grafo validada.
        """
        if num_nodos < 7 or num_nodos > 16:
            raise ValueError("La cantidad de nodos debe estar entre 7 y 16, según los requisitos oficiales.")
            
        grafo = Grafo()
        for i in range(1, num_nodos + 1):
            grafo.agregar_nodo(i, chr(64 + i) if 1 <= i <= 26 else str(i))
        for i in range(2, num_nodos + 1):
            origen = random.randint(1, i - 1)
            peso = random.randint(min_peso, max_peso)
            grafo.agregar_arista(origen, i, float(peso))
        probabilidad_conexion = min(0.23, 2.2 / num_nodos) # Densidad moderada para legibilidad
        limite_aristas = min(2 * num_nodos + 2, num_nodos * (num_nodos - 1) // 2)
        cantidad_aristas = num_nodos - 1
        
        for u in range(1, num_nodos):
            for v in range(u + 1, num_nodos + 1):
                ya_existe = any(arista.destino.id_nodo == v for arista in grafo.obtener_sucesores(u))
                
                if not ya_existe and cantidad_aristas < limite_aristas and random.random() < probabilidad_conexion:
                    peso = random.randint(min_peso, max_peso)
                    grafo.agregar_arista(u, v, float(peso))
                    cantidad_aristas += 1
        if ValidadorGrafo.tiene_ciclos(grafo):
            raise RuntimeError("Error crítico: El generador produjo un grafo con ciclos.")
            
        return grafo
