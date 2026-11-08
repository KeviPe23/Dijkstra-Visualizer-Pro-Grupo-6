from modelos.grafo import Grafo

class ValidadorGrafo:
    """
    Servicio encargado de aplicar algoritmos matemáticos para comprobar
    la integridad y restricciones del grafo.
    """
    
    @staticmethod
    def tiene_ciclos(grafo: Grafo) -> bool:
        """
        Utiliza Búsqueda en Profundidad (DFS - Depth First Search) para detectar 
        si existen ciclos en el grafo dirigido.
        
        Retorna:
            True si hay al menos un ciclo (inválido para el proyecto).
            False si es un Grafo Dirigido Acíclico (DAG) (válido).
        """
        visitados = set()
        apilados = set() 
        
        def dfs(id_nodo: int) -> bool:
            visitados.add(id_nodo)
            apilados.add(id_nodo)
            for arista in grafo.obtener_sucesores(id_nodo):
                id_vecino = arista.destino.id_nodo
                if id_vecino not in visitados:
                    if dfs(id_vecino):
                        return True
                elif id_vecino in apilados:
                    return True
            apilados.remove(id_nodo)
            return False
        for nodo in grafo.obtener_todos_los_nodos():
            if nodo.id_nodo not in visitados:
                if dfs(nodo.id_nodo):
                    return True
                    
        return False
