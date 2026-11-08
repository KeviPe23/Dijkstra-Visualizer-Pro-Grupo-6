"""Etiquetas académicas [d,V]_(n) para los vértices de Dijkstra.

Dos contadores explícitos: «lectura» reproduce los subíndices de los
problemas resueltos (etapa de propagación por ruta); «ronda» indica la
ronda real de Dijkstra en la que se guardó cada etiqueta. Nunca se
mezclan, pues en el PDF la descripción y los ejemplos no siempre
utilizan el mismo sentido de «iteración».
"""
import math
from ui.numeros import formatear_numero


def letra(n):
    return chr(64+n) if isinstance(n, int) and 1 <= n <= 26 else str(n)


def distancia(valor):
    if valor is None or math.isinf(valor):
        return '∞'
    return formatear_numero(valor)


def datos_etiqueta(estado, nodo, modo="lectura"):
    """Devuelve [(texto_[d,V], iteración), ...], con datos del paso actual."""
    if not estado or 'distancias' not in estado:
        return []
    valor = estado.get('distancias_exactas', estado['distancias']).get(nodo, math.inf)
    distancia_txt = distancia(valor)
    anteriores = sorted(set(estado.get('predecesores', {}).get(nodo, [])))
    if modo not in ('lectura', 'ronda'):
        raise ValueError('Modo de numeración desconocido')
    clave_paso = 'rondas_etiqueta' if modo == 'ronda' else 'iteraciones_etiqueta'
    clave_pred = 'rondas_predecesor' if modo == 'ronda' else 'iteraciones_predecesor'
    paso = estado.get(clave_paso, {}).get(nodo)
    if not anteriores:
        if math.isinf(valor):
            return [('[∞,–]', None)]
        return [(f'[{distancia_txt},–]', 0 if paso is None else paso)]
    pasos_pred = estado.get(clave_pred, {}).get(nodo, {})
    return [(f'[{distancia_txt},{letra(pred)}]', pasos_pred.get(pred, paso))
            for pred in anteriores]


def etiqueta_plana(estado, nodo, modo="lectura"):
    """Forma textual accesible, también usada en la columna de la tabla."""
    datos = datos_etiqueta(estado, nodo, modo=modo)
    return '  /  '.join(f'{valor}({n if n is not None else "–"})'
                       for valor, n in datos) or '—'


def etiqueta_tripleta(dist, predecesor, nivel):
    """Formatea una etiqueta para el historial, incluso si fue descartada."""
    if predecesor is None:
        return f'[{distancia(dist)},–]({nivel if nivel is not None else "–"})'
    return f'[{distancia(dist)},{letra(predecesor)}]({nivel if nivel is not None else "–"})'


def etiquetas_descartadas(estado, nodo, modo="lectura"):
    """Etiquetas que deben aparecer tachadas en la relajación actual."""
    if (not estado or estado.get('estado') != 'EVALUANDO'
            or estado.get('vecino') != nodo):
        return []
    clave = 'etiquetas_descartadas_ronda' if modo == 'ronda' else 'etiquetas_descartadas'
    return [(etiqueta_tripleta(dist, pre, n))
            for dist, pre, n in estado.get(clave, ())]
