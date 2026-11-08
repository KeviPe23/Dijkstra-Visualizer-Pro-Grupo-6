import math
from decimal import Decimal, InvalidOperation
from modelos.nodo import Nodo


class Arista:
    """Arista dirigida de peso finito y no negativo."""
    MAX_PESO = 1e12

    def __init__(self, origen: Nodo, destino: Nodo, peso: float):
        if isinstance(peso, bool) or not isinstance(peso, (int, float, Decimal)):
            raise ValueError('El peso debe ser un número finito.')
        try:
            exacto = Decimal(str(peso))
        except InvalidOperation as exc:
            raise ValueError('El peso debe ser un número finito.') from exc
        if not exacto.is_finite():
            raise ValueError('El peso debe ser un número finito.')
        if exacto < 0:
            raise ValueError('Dijkstra no admite pesos negativos.')
        if exacto > Decimal(str(self.MAX_PESO)):
            raise ValueError('El peso excede el límite numérico permitido.')
        self.origen = origen
        self.destino = destino
        # Conservar el valor decimal introducido para cálculos sin empates falsos.
        # El atributo histórico «peso» sigue siendo float por compatibilidad.
        self.peso_exacto = Decimal(0) if exacto == 0 else exacto
        self.peso = float(self.peso_exacto)

    def __str__(self):
        return f'{self.origen.etiqueta} --({self.peso_exacto})--> {self.destino.etiqueta}'
