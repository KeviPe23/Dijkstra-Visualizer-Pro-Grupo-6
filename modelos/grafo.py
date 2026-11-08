from typing import List, Dict
from modelos.nodo import Nodo
from modelos.arista import Arista


class Grafo:
    """Grafo dirigido, ponderado y simple; el controlador valida la aciclicidad."""
    def __init__(self):
        self.nodos: Dict[int, Nodo] = {}
        self.adyacencia: Dict[int, List[Arista]] = {}

    def agregar_nodo(self, id_nodo: int, etiqueta: str = '') -> Nodo:
        if id_nodo not in self.nodos:
            nodo = Nodo(id_nodo, etiqueta)
            self.nodos[id_nodo] = nodo
            self.adyacencia[id_nodo] = []
        return self.nodos[id_nodo]

    def agregar_arista(self, id_origen: int, id_destino: int, peso: float):
        if id_origen not in self.nodos or id_destino not in self.nodos:
            raise ValueError('Ambos nodos deben existir antes de crear una arista.')
        if id_origen == id_destino:
            letra_n = chr(64 + id_origen) if 1 <= id_origen <= 26 else str(id_origen)
            raise ValueError(f'No se permiten lazos ({letra_n} → {letra_n}): formaría un ciclo.')
        if any(a.destino.id_nodo == id_destino for a in self.adyacencia[id_origen]):
            inicio = chr(64 + id_origen) if 1 <= id_origen <= 26 else str(id_origen)
            fin = chr(64 + id_destino) if 1 <= id_destino <= 26 else str(id_destino)
            raise ValueError(f'La arista {inicio} → {fin} ya existe. No se permiten aristas duplicadas.')
        arista = Arista(self.nodos[id_origen], self.nodos[id_destino], peso)
        self.adyacencia[id_origen].append(arista)

    def eliminar_arista(self, id_origen: int, id_destino: int) -> bool:
        """Elimina solo una arista existente, sin tocar los demás vértices."""
        if id_origen not in self.adyacencia:
            return False
        antes = len(self.adyacencia[id_origen])
        self.adyacencia[id_origen] = [a for a in self.adyacencia[id_origen]
                                        if a.destino.id_nodo != id_destino]
        return len(self.adyacencia[id_origen]) < antes

    def obtener_sucesores(self, id_nodo: int) -> List[Arista]:
        return self.adyacencia.get(id_nodo, [])

    def cantidad_nodos(self) -> int:
        return len(self.nodos)

    def obtener_todos_los_nodos(self) -> List[Nodo]:
        return list(self.nodos.values())

    def reiniciar_grafo(self):
        self.nodos.clear()
        self.adyacencia.clear()
