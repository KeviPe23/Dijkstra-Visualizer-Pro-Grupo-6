"""Formato legible y fiel de pesos y distancias del simulador."""
import math
from decimal import Decimal, localcontext


def formatear_numero(valor):
    """No ocultar diferencias entre rutas al redondear a 6 cifras significativas."""
    if valor is None:
        return '—'
    if isinstance(valor, Decimal):
        if valor.is_infinite():
            return '∞'
        if valor.is_nan():
            return 'NaN'
        if valor == 0:
            return '0'
        # Normaliza ceros finales, pero conserva TODOS los decimales relevantes.
        with localcontext() as ctx:
            ctx.prec = max(128, len(valor.as_tuple().digits) + 4)
            normal = valor.normalize()
        plano = format(normal, 'f')
        # En valores muy largos, notación científica sin truncar las cifras.
        notacion = format(normal, 'e').replace('E', 'e')
        return plano if len(plano) <= 22 or len(plano) <= len(notacion) else notacion
    if isinstance(valor, (int, float)):
        if math.isinf(valor):
            return '∞'
        if valor == 0:
            return '0'
        # Para floats legados: representa suficientes cifras para ver diferencias.
        return format(valor, '.15g')
    return str(valor)
