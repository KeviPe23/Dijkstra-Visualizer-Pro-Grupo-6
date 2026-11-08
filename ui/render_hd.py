"""Renderizador de grafos con trazos y textos suavizados (Pillow).

El diseño utiliza coordenadas de Tkinter, conserva posiciones y no altera
la geometría de las interacciones: solo mejora su presentación visual.
Soporta dinámicamente Modo Claro y Modo Oscuro a través de ui.estilos.
"""
import math
import os
import sys
from functools import lru_cache

try:
    from PIL import Image, ImageDraw, ImageFont, ImageTk
except ImportError:
    Image = ImageDraw = ImageFont = ImageTk = None

from ui import estilos as E
from ui.etiquetas import datos_etiqueta, etiquetas_descartadas
from ui.numeros import formatear_numero


def disponible():
    return Image is not None


@lru_cache(maxsize=100)
def _fuente(tamano, negrita=False):
    if sys.platform == 'win32':
        nombre = 'segoeuib.ttf' if negrita else 'segoeui.ttf'
        candidatos = [os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts', nombre)]
    elif sys.platform == 'darwin':
        candidatos = ['/System/Library/Fonts/Supplemental/Arial Bold.ttf' if negrita else
                      '/System/Library/Fonts/Supplemental/Arial.ttf']
    else:
        candidatos = ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if negrita else
                      '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                      '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf' if negrita else
                      '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf']
    for ruta in candidatos:
        try:
            return ImageFont.truetype(ruta, tamano)
        except OSError:
            pass
    try:
        return ImageFont.truetype('DejaVuSans-Bold.ttf' if negrita else 'DejaVuSans.ttf', tamano)
    except OSError:
        return ImageFont.load_default(size=tamano)


def renderizar(ancho, alto, posiciones, aristas, visitados=None, actual=None,
               evaluada=None, rutas=None, escala_salida=1.0, suavizado=3,
               estado=None, modo_etiquetas='lectura',
               posiciones_etiquetas=None, cajas_etiquetas=None):
    """Devuelve PNG RGB HD como PIL.Image.

    coordenadas de entrada: pixels del Canvas normal. escala_salida permite
    exportar el mismo grafo a 3840 px sin mover los nodos.
    """
    if Image is None:
        raise RuntimeError('Pillow no está instalado.')
    ancho, alto = max(100, int(ancho)), max(100, int(alto))
    suavizado = max(1, min(4, int(suavizado)))
    escala_salida = max(0.1, float(escala_salida))
    factor = escala_salida * suavizado
    W, H = max(1, round(ancho * factor)), max(1, round(alto * factor))
    imagen = Image.new('RGB', (W, H), E.CANVAS)
    lapiz = ImageDraw.Draw(imagen)
    visitados = set(visitados or ())
    rutas = rutas or ()
    ruta_arcos = set()
    for ruta in rutas:
        ruta_arcos.update(zip(ruta, ruta[1:]))
    posiciones = {n: (x * factor, y * factor) for n, (x, y) in posiciones.items()}
    r = 22 * factor
    # Medir antes las cajas de etiquetas para evitar taparlas con pesos.
    # La segunda pasada dibuja las etiquetas en su posición original.
    cajas_previstas = {}
    if estado is not None:
        _dibujar_etiquetas(lapiz, posiciones, factor, ancho, alto, estado,
                           visitados, actual, modo_etiquetas=modo_etiquetas,
                           posiciones_etiquetas=posiciones_etiquetas,
                           cajas_etiquetas=cajas_previstas, solo_medir=True)
    zonas_etiquetas = [(a*factor, b*factor, c*factor, d*factor)
                       for a,b,c,d in cajas_previstas.values()]
    zonas_pesos = []

    # Las aristas se dibujan antes de los nodos, sin texto cortado en los extremos.
    for u, v, peso in aristas:
        if u not in posiciones or v not in posiciones:
            continue
        x1, y1 = posiciones[u]
        x2, y2 = posiciones[v]
        dx, dy = x2 - x1, y2 - y1
        distancia = math.hypot(dx, dy)
        if distancia <= 0.01:
            continue
        ux, uy = dx / distancia, dy / distancia
        sx, sy = x1 + ux * (r + 3*factor), y1 + uy * (r + 3*factor)
        ex, ey = x2 - ux * (r + 8*factor), y2 - uy * (r + 8*factor)
        importante = (u, v) in ruta_arcos
        evaluando = (u, v) == evaluada
        color = E.AMBER if evaluando else E.RED if importante else E.EDGE_DEFAULT
        grosor = max(2, round((3.2 if evaluando or importante else 2.2) * factor))
        lapiz.line([(sx, sy), (ex, ey)], fill=color, width=grosor, joint='curve')
        # Triángulo de flecha geométricamente estable en cualquier dirección.
        cabeza = (ex + ux * 3*factor, ey + uy * 3*factor)
        base_x, base_y = ex - ux * 12*factor, ey - uy * 12*factor
        semiancho = 6.2*factor
        lapiz.polygon([cabeza,
                       (base_x - uy*semiancho, base_y + ux*semiancho),
                       (base_x + uy*semiancho, base_y - ux*semiancho)], fill=color)
        # Ubicar el peso sin tapar los rótulos [d,V](n), nodos ni otros pesos.
        # Especialmente útil en grafos densos y pantallas de portátil.
        peso_texto = formatear_numero(peso)
        fuente = _fuente(max(11, round(12.5*factor)), True)
        rect = lapiz.textbbox((0,0), peso_texto, font=fuente, anchor='lt')
        tw, th = rect[2]-rect[0], rect[3]-rect[1]
        padx, pady = 7*factor, 4*factor
        candidatos = []
        for fraccion in (.5, .34, .66, .21, .79):
            for desplazamiento in (14, -18, 29, -32, 45, -49):
                px = sx + (ex-sx)*fraccion - uy*desplazamiento*factor
                py = sy + (ey-sy)*fraccion + ux*desplazamiento*factor
                bbox = (px-tw/2-padx, py-th/2-pady, px+tw/2+padx, py+th/2+pady)
                choque = 0.0
                for zona in zonas_etiquetas:
                    choque += _area_comun(bbox, zona) * 12.0
                for zona in zonas_pesos:
                    choque += _area_comun(bbox, zona) * 3.0
                for nx,ny in posiciones.values():
                    zona = (nx-25*factor, ny-25*factor, nx+25*factor, ny+25*factor)
                    choque += _area_comun(bbox, zona) * 9.0
                fuera = (max(0, 2*factor-bbox[0]) + max(0,bbox[2]-(W-2*factor)) +
                         max(0,2*factor-bbox[1]) + max(0,bbox[3]-(H-2*factor)))
                # Preferir posiciones próximas al centro cuando no haya choques.
                penal = choque/(factor*factor) + fuera*8/factor +                         abs(fraccion-.5)*10 + abs(desplazamiento-14)*.05
                candidatos.append((penal,px,py,bbox))
        _, px, py, bbox = min(candidatos, key=lambda item:item[0])
        zonas_pesos.append(bbox)
        lapiz.rounded_rectangle(bbox, radius=7*factor, fill=E.WEIGHT_BG,
                               outline=E.WEIGHT_BORDER, width=max(1, round(factor*.8)))
        lapiz.text((px, py), peso_texto, font=fuente, fill=E.TEXT,
                   anchor='mm', stroke_width=0)

    for n in sorted(posiciones):
        x, y = posiciones[n]
        alcanzado = bool(estado and not math.isinf(estado['distancias'].get(n, math.inf)))
        relleno = (E.NODE_AMBER if n == actual else E.NODE_GREEN if n in visitados
                   else E.NODE_RED if alcanzado else E.NODE_ACCENT)
        # Borde amplio de alto contraste + ligero anillo para evitar bordes serrados.
        lapiz.ellipse((x-r-2*factor, y-r-2*factor, x+r+2*factor, y+r+2*factor),
                     fill=E.CANVAS)
        grosor_borde = max(1, round(factor * (0.8 if E.MODO_OSCURO else 1.25)))
        lapiz.ellipse((x-r, y-r, x+r, y+r), fill=relleno,
                     outline=E.NODE_OUTLINE, width=grosor_borde)
        fuente = _fuente(max(12, round(14.5*factor)), True)
        letra = chr(64+n) if isinstance(n, int) and 1 <= n <= 26 else str(n)
        lapiz.text((x, y-.6*factor), letra, fill=E.NODE_TEXT, font=fuente, anchor='mm')

    if estado is not None:
        _dibujar_etiquetas(lapiz, posiciones, factor, ancho, alto, estado, visitados, actual,
                           modo_etiquetas=modo_etiquetas,
                           posiciones_etiquetas=posiciones_etiquetas,
                           cajas_etiquetas=cajas_etiquetas)

    if suavizado > 1:
        imagen = imagen.resize((round(ancho*escala_salida), round(alto*escala_salida)),
                                Image.Resampling.LANCZOS)
    return imagen


def _area_comun(a, b):
    return max(0, min(a[2],b[2])-max(a[0],b[0])) * max(0, min(a[3],b[3])-max(a[1],b[1]))


def _se_cruzan(a, b, margen=2):
    return (a[0] < b[2] + margen and a[2] + margen > b[0]
            and a[1] < b[3] + margen and a[3] + margen > b[1])


def _dibujar_etiquetas(lapiz, posiciones, factor, ancho, alto,
                       estado, visitados, actual, modo_etiquetas='lectura',
                       posiciones_etiquetas=None, cajas_etiquetas=None,
                       solo_medir=False):
    """Rótulos [distancia,predecesor]_(iteración); opción de medir sin dibujar."""
    limite_x, limite_y = ancho*factor, alto*factor
    posiciones_etiquetas = posiciones_etiquetas or {}
    if cajas_etiquetas is not None:
        cajas_etiquetas.clear()
    total_nodos = max(1, len(posiciones))
    escala_tag = 1.38 if total_nodos <= 9 else 1.28 if total_nodos <= 12 else 1.18
    fuente = _fuente(max(12, round(12.8*factor*escala_tag)), True)
    subfuente = _fuente(max(10, round(10.0*factor*escala_tag)), True)
    infofuente = _fuente(max(10, round(10.3*factor*escala_tag)))
    fila_h = max(22*factor, 24*factor*escala_tag)
    margen = 11*factor
    ocupados = [(x-27*factor, y-27*factor, x+27*factor, y+27*factor)
                for x,y in posiciones.values()]
    for nodo in sorted(posiciones):
        datos = datos_etiqueta(estado, nodo, modo_etiquetas)
        if not datos:
            continue
        extra = max(0, len(datos)-3)
        datos = datos[:3]
        tachadas = etiquetas_descartadas(estado, nodo, modo_etiquetas)[:2]
        lineas = []
        for valor, it in datos:
            suf = f'({it})' if it is not None else '(–)'
            texto_ancho = lapiz.textbbox((0,0), valor, font=fuente)[2]
            suf_ancho = lapiz.textbbox((0,0), suf, font=subfuente)[2]
            lineas.append((valor, suf, texto_ancho, suf_ancho, False))
        for texto in tachadas:
            texto_ancho = lapiz.textbbox((0,0), texto, font=infofuente)[2]
            lineas.append((texto, '', texto_ancho, 0, True))
        texto_extra = f'+{extra} predecesores: ver tabla' if extra else ''
        ancho_filas = max((f[2]+f[3]+5*factor for f in lineas), default=0)
        if texto_extra:
            ancho_filas = max(ancho_filas, lapiz.textbbox((0,0), texto_extra, font=infofuente)[2])
        caja_w = ancho_filas + 2*margen
        caja_h = (len(lineas) + bool(texto_extra))*fila_h + 9*factor
        x, y = posiciones[nodo]
        posiciones_posibles = [
            (x+38*factor, y-50*factor-caja_h/2),
            (x-38*factor-caja_w, y-50*factor-caja_h/2),
            (x+38*factor, y+22*factor),
            (x-38*factor-caja_w, y+22*factor),
            (x-caja_w/2, y-44*factor-caja_h),
            (x-caja_w/2, y+44*factor),
            (x+46*factor, y-caja_h/2),
            (x-46*factor-caja_w, y-caja_h/2),
        ]
        elegido = None
        if nodo in posiciones_etiquetas:
            ox, oy = posiciones_etiquetas[nodo]
            xx, yy = x + ox*factor, y + oy*factor
            xx = max(5*factor, min(max(5*factor, limite_x-caja_w-5*factor), xx))
            yy = max(5*factor, min(max(5*factor, limite_y-caja_h-5*factor), yy))
            elegido = (xx, yy, xx+caja_w, yy+caja_h)
        else:
            mejor = float('inf')
            for k,(ox,oy) in enumerate(posiciones_posibles):
                xx = max(5*factor, min(max(5*factor, limite_x-caja_w-5*factor), ox))
                yy = max(5*factor, min(max(5*factor, limite_y-caja_h-5*factor), oy))
                caja = (xx, yy, xx+caja_w, yy+caja_h)
                choques = sum(_se_cruzan(caja, otro, margen=2*factor) for otro in ocupados)
                penal = 100*choques + (abs(xx-ox)+abs(yy-oy))/(50*factor) + k*.05
                if penal < mejor:
                    elegido, mejor = caja, penal
        if elegido is None:
            continue
        x1,y1,x2,y2 = elegido
        if cajas_etiquetas is not None:
            cajas_etiquetas[nodo] = (x1/factor, y1/factor, x2/factor, y2/factor)
        if solo_medir:
            ocupados.append(elegido)
            continue
        alcanzado = not math.isinf(estado.get('distancias_exactas',estado['distancias']).get(nodo, math.inf))
        color = E.AMBER if nodo==actual else E.GREEN if nodo in visitados else E.RED if alcanzado else E.MUTED
        # Línea guía hasta el rótulo; por debajo de la caja.
        centro_x, centro_y = (x1+x2)/2, (y1+y2)/2
        dx,dy = centro_x-x,centro_y-y
        largo = max(math.hypot(dx,dy),1)
        inicio = (x+dx/largo*22*factor, y+dy/largo*22*factor)
        lapiz.line([inicio, (centro_x,centro_y)], fill=E.TAG_GUIDE, width=max(2,round(1.4*factor)))
        # Sombra suave para separar la etiqueta del fondo del grafo.
        sombra = (x1+2*factor, y1+2*factor, x2+2*factor, y2+2*factor)
        lapiz.rounded_rectangle(sombra, radius=9*factor, fill=E.TAG_SHADOW)
        lapiz.rounded_rectangle(elegido, radius=9*factor, fill=E.TAG_BG,
                               outline=color, width=max(2,round(1.8*factor)))
        stroke_w = max(1, round(0.6*factor)) if E.TAG_STROKE else 0
        for i,(valor,suf,tw,sw,tachada) in enumerate(lineas):
            total = tw+sw+7*factor
            tx = x1 + (caja_w-total)/2
            ty = y1 + 6*factor + i*fila_h
            lapiz.text((tx, ty), valor, font=infofuente if tachada else fuente,
                       fill=E.TAG_STRIKE_TEXT if tachada else E.TAG_TEXT, anchor='lt',
                       stroke_width=stroke_w,
                       stroke_fill=(color if not tachada else E.TAG_STRIKE_STROKE) if stroke_w else None)
            if tachada:
                caja_t = lapiz.textbbox((tx, ty), valor, font=infofuente, anchor='lt')
                ym = (caja_t[1] + caja_t[3]) / 2
                lapiz.line([(caja_t[0], ym), (caja_t[2], ym)],
                           fill=E.TAG_STRIKE_LINE, width=max(2,round(1.7*factor)))
            else:
                color_sub = E.TAG_SUB_ACTUAL if nodo==actual else color
                lapiz.text((tx+tw+4*factor, ty+8*factor), suf,
                           font=subfuente, fill=color_sub, anchor='lt')
        if texto_extra:
            lapiz.text((centro_x, y1+6*factor+len(lineas)*fila_h),
                       texto_extra, font=infofuente, fill=E.TAG_EXTRA_TEXT, anchor='mt')
        ocupados.append(elegido)
