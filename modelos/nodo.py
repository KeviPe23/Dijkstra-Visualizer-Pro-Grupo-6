class Nodo:
    """
    Representa un vértice en el grafo.
    """
    def __init__(self, id_nodo: int, etiqueta: str = ""):
        self.id_nodo = id_nodo
        self.etiqueta = etiqueta if etiqueta else str(id_nodo)
        
    def __hash__(self):
        return hash(self.id_nodo)
        
    def __eq__(self, otro):
        if isinstance(otro, Nodo):
            return self.id_nodo == otro.id_nodo
        return False
        
    def __str__(self):
        return f"Nodo({self.etiqueta})"
