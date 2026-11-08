"""Auditoría integral para las observaciones del profesor y casos límite similares.

Verifica tanto a nivel algorítmico/modelo como en la interfaz gráfica real (Tkinter):
1. Rechazo estricto de aristas duplicadas, lazos y ciclos.
2. Unicidad garantizada de caminos óptimos (jamás duplicar una misma ruta).
3. Visibilidad explícita de distancias d(v), predecesores π(v) y etiquetas [d,V](n)
   en cada iteración (tabla, banner paso a paso, lienzo e historial por rondas).
4. Robustez ante casos numéricos límite (-0.0, precisión decimal IEEE-754,
   desbordamiento float / inf, nodos sumidero en historial y clics repetidos).
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algoritmos.dijkstra import Dijkstra
from modelos.arista import Arista
from modelos.grafo import Grafo
from modelos.nodo import Nodo
from servicios.validador_grafo import ValidadorGrafo
from ui.etiquetas import datos_etiqueta, etiqueta_plana
from ui.vistas_didacticas import datos_historial, datos_matriz


class AuditoriaModeloYAlgoritmo(unittest.TestCase):
    """Pruebas exhaustivas de modelo y motor matemático de Dijkstra."""

    def test_rechazo_aristas_duplicadas_y_lazos_en_modelo(self):
        g = Grafo()
        for i in range(1, 8):
            g.agregar_nodo(i, chr(64 + i))

        # Lazos directos prohibidos incluso llamando al modelo sin pasar por la GUI
        with self.assertRaisesRegex(ValueError, 'lazos'):
            g.agregar_arista(1, 1, 3)
        self.assertEqual(g.obtener_sucesores(1), [])

        # Primera inserción válida
        g.agregar_arista(1, 2, 4)
        self.assertEqual(len(g.obtener_sucesores(1)), 1)

        # Duplicadas con igual peso, distinto peso, peso 0 o decimal equivalente
        for peso_intento in (4, 4.0, 0, 99, 1.5):
            with self.subTest(peso=peso_intento):
                with self.assertRaisesRegex(ValueError, 'duplicadas'):
                    g.agregar_arista(1, 2, peso_intento)
        self.assertEqual(len(g.obtener_sucesores(1)), 1)
        self.assertEqual(g.obtener_sucesores(1)[0].peso, 4.0)

        # Tras eliminar explícitamente la arista, sí se permite volver a crearla
        self.assertTrue(g.eliminar_arista(1, 2))
        g.agregar_arista(1, 2, 7)
        self.assertEqual(len(g.obtener_sucesores(1)), 1)
        self.assertEqual(g.obtener_sucesores(1)[0].peso, 7.0)

    def test_normalizacion_cero_negativo_y_limites_numericos(self):
        n1, n2 = Nodo(1, 'A'), Nodo(2, 'B')

        # -0.0 en float se normaliza a +0.0 para jamás renderizar "-0"
        arista_cero = Arista(n1, n2, -0.0)
        self.assertEqual(arista_cero.peso, 0.0)
        self.assertFalse(math.copysign(1.0, arista_cero.peso) < 0)
        self.assertEqual(f'{arista_cero.peso:g}', '0')
        self.assertNotIn('-0', str(arista_cero))

        # Pesos fuera de rango o no finitos rechazados
        for invalido in (-1, -0.0001, math.nan, math.inf, -math.inf, 1e13, 1e308, True, False, '3'):
            with self.subTest(invalido=invalido):
                with self.assertRaises(ValueError):
                    Arista(n1, n2, invalido)

    def test_unicidad_estricta_de_caminos_optimos_en_empates_complejos(self):
        # Diamantes encadenados: A -> {B,C} -> D -> {E,F} -> G (4 rutas óptimas únicas de costo 6)
        g = Grafo()
        for i in range(1, 8):
            g.agregar_nodo(i, chr(64 + i))
        for u, v, w in (
            (1, 2, 1), (1, 3, 1),
            (2, 4, 2), (3, 4, 2),
            (4, 5, 1), (4, 6, 1),
            (5, 7, 2), (6, 7, 2),
        ):
            g.agregar_arista(u, v, w)

        motor = Dijkstra(g)
        motor.ejecutar(1)
        rutas = motor.obtener_caminos_minimos(7)
        self.assertEqual(motor.distancias[7], 6.0)
        self.assertEqual(motor.contar_caminos_minimos(7), 4)
        self.assertEqual(len(rutas), 4)
        self.assertEqual(len(rutas), len({tuple(r) for r in rutas}))
        self.assertEqual(rutas, [
            [1, 2, 4, 5, 7],
            [1, 2, 4, 6, 7],
            [1, 3, 4, 5, 7],
            [1, 3, 4, 6, 7],
        ])

    def test_unicidad_defensiva_ante_corrupcion_interna_y_origen_igual_destino(self):
        g = Grafo()
        for i in range(1, 8):
            g.agregar_nodo(i, chr(64 + i))
        g.agregar_arista(1, 2, 0)
        g.agregar_arista(2, 7, 0)
        g.agregar_arista(1, 7, 0)
        # Inyección defensiva directa en estructura interna simulando datos corruptos
        g.adyacencia[1].append(Arista(g.nodos[1], g.nodos[2], 0))
        g.adyacencia[2].append(Arista(g.nodos[2], g.nodos[7], 0))

        motor = Dijkstra(g)
        motor.ejecutar(1)
        # Origen == Destino jamás duplica ni cicla por aristas de peso 0
        self.assertEqual(motor.predecesores[1], [])
        self.assertEqual(motor.contar_caminos_minimos(1), 1)
        self.assertEqual(motor.obtener_caminos_minimos(1), [[1]])

        # Destino 7 tiene exactamente 2 rutas únicas ([1, 2, 7] y [1, 7]), nunca repetidas
        self.assertEqual(motor.predecesores[2], [1])
        self.assertEqual(motor.predecesores[7], [1, 2])
        self.assertEqual(motor.contar_caminos_minimos(7), 2)
        self.assertEqual(motor.obtener_caminos_minimos(7), [[1, 2, 7], [1, 7]])

    def test_precision_decimal_en_desempate_y_etiquetas(self):
        # 0.1 + 0.2 en IEEE-754 produce 0.30000000000000004; debe limpiarse a 0.3 exacto
        g = Grafo()
        for i in range(1, 8):
            g.agregar_nodo(i, chr(64 + i))
        g.agregar_arista(1, 2, 0.1)
        g.agregar_arista(2, 3, 0.2)
        g.agregar_arista(1, 4, 0.3)
        g.agregar_arista(3, 7, 1.0)
        g.agregar_arista(4, 7, 1.0)

        motor = Dijkstra(g)
        pasos = list(motor.ejecutar_paso_a_paso(1))
        self.assertEqual(motor.distancias[3], 0.3)
        self.assertEqual(motor.distancias[4], 0.3)
        self.assertEqual(motor.distancias[7], 1.3)
        # C (nodo 3) debe seleccionarse antes que D (nodo 4) por orden alfabético al empatar en 0.3
        seleccionados = [p['nodo_actual'] for p in pasos if p['estado'] == 'VISITADO']
        self.assertLess(seleccionados.index(3), seleccionados.index(4))
        self.assertEqual(motor.obtener_caminos_minimos(7), [[1, 2, 3, 7], [1, 4, 7]])

    def test_historial_registra_fila_correcta_en_descartes_y_cabeceras_sumidero(self):
        # Caso Lectura 5.2: cuando B evalúa B->C (peso 1, candidata 5 vs actual 3 -> SIN_CAMBIO),
        # el descarte '× [5,B](2)' DEBE quedar en la fila de C (índice 2), jamás en la fila de B.
        g = Grafo()
        for n in range(1, 9):
            g.agregar_nodo(n, chr(64 + n))
        for u, v, w in (
            (1, 2, 4), (1, 3, 3), (2, 3, 1), (2, 5, 3),
            (3, 4, 2), (3, 5, 2), (4, 5, 1), (4, 7, 3),
            (5, 6, 2), (5, 7, 2), (6, 7, 1), (6, 8, 3), (7, 8, 4),
        ):
            g.agregar_arista(u, v, w)

        pasos = list(Dijkstra(g).ejecutar_paso_a_paso(1))
        final = pasos[-1]
        for modo, esperado_c in (('lectura', '× [5,B](2)'), ('ronda', '× [5,B](3)')):
            cols, filas = datos_historial(g, final, modo=modo)
            # Todas las columnas de ronda incluyen el nombre del vértice seleccionado (incluido sumidero 8 · H)
            self.assertEqual(cols[-1], '8 · H')
            self.assertTrue(all('Ronda ' not in c for c in cols[2:]))

            filas_por_vertice = {fila[0]: fila for fila in filas}
            # Ronda 3 corresponde a '3 · B' (columna índice 4)
            idx_ronda_b = cols.index('3 · B')
            self.assertIn(esperado_c, filas_por_vertice['C'][idx_ronda_b])
            self.assertEqual(filas_por_vertice['B'][idx_ronda_b], '—')


class AuditoriaInterfazProfesor(unittest.TestCase):
    """Pruebas de extremo a extremo sobre la ventana real de Version_2."""

    def setUp(self):
        if sys.platform.startswith('linux') and not os.environ.get('DISPLAY'):
            self.skipTest('Entorno sin servidor gráfico X11')
        from ui.app import App
        self.app = App(mostrar_inicio=False)
        self.app.update_idletasks()
        self.app.update()

    def tearDown(self):
        if hasattr(self, 'app') and self.app is not None:
            try:
                self.app.destroy()
            except Exception:
                pass

    def test_gui_bloquea_duplicados_lazos_ciclos_y_cero_negativo(self):
        app = self.app
        cfg = app.panel_config
        app.manejador_iniciar_manual(7)
        app.update_idletasks()

        # Agregar A -> B con peso 2 desde los controles reales del panel lateral
        cfg.ent_origen.set('A')
        cfg.ent_destino.set('B')
        cfg.ent_peso.delete(0, 'end')
        cfg.ent_peso.insert(0, '2')
        cfg._agregar()
        self.assertEqual(len(cfg.tabla_aristas.get_children()), 1)

        # Intentar duplicar A -> B desde el botón de la GUI (mismo o distinto peso)
        for peso_dup in ('2', '2.0', '2,0', '8'):
            cfg.ent_peso.delete(0, 'end')
            cfg.ent_peso.insert(0, peso_dup)
            cfg._agregar()
            self.assertEqual(len(cfg.tabla_aristas.get_children()), 1)
            self.assertEqual(cfg._estado_tipo, 'error')
            self.assertIn('duplicadas', cfg.lbl_estado.cget('text'))

        # Intentar lazo A -> A desde la GUI
        cfg.ent_origen.set('A')
        cfg.ent_destino.set('A')
        cfg._agregar()
        self.assertEqual(len(cfg.tabla_aristas.get_children()), 1)
        self.assertEqual(cfg._estado_tipo, 'error')

        # Intentar pesos negativos o "-0" / "-0.0"
        cfg.ent_origen.set('B')
        cfg.ent_destino.set('C')
        for peso_neg in ('-0', '-0.0', '-0,0', '-3', 'inf', 'nan', '1e20'):
            cfg.ent_peso.delete(0, 'end')
            cfg.ent_peso.insert(0, peso_neg)
            cfg._agregar()
            self.assertEqual(len(cfg.tabla_aristas.get_children()), 1)
            self.assertEqual(cfg._estado_tipo, 'error')

        # Crear B -> C (peso 0 válido) y verificar que C -> A se rechaza por formar ciclo
        cfg.ent_peso.delete(0, 'end')
        cfg.ent_peso.insert(0, '0')
        cfg._agregar()
        self.assertEqual(len(cfg.tabla_aristas.get_children()), 2)
        cols_m, filas_m = datos_matriz(app.grafo_actual)
        self.assertEqual(filas_m[1][3], '0')  # B -> C tiene peso '0', nunca '-0'

        cfg.ent_origen.set('C')
        cfg.ent_destino.set('A')
        cfg.ent_peso.delete(0, 'end')
        cfg.ent_peso.insert(0, '1')
        cfg._agregar()
        self.assertEqual(len(cfg.tabla_aristas.get_children()), 2)
        self.assertIn('ciclo', cfg.lbl_estado.cget('text').lower())

    def test_gui_muestra_distancias_y_predecesores_explicitamente_en_cada_paso(self):
        app = self.app
        panel = app.panel_grafo

        # Etiquetas [d,V](n) activas por defecto en el lienzo
        self.assertTrue(panel.mostrar_etiquetas.get())

        app.manejador_iniciar_pasos('A', 'G')
        total_pasos = len(app.pasos)
        self.assertGreater(total_pasos, 4)

        for idx in range(total_pasos):
            app.update_idletasks()
            paso = app.pasos[idx]
            etapa = paso['estado']

            # 1. Contador explícito de paso e iteración sobre la tabla
            self.assertIn(f'Paso {idx + 1}/{total_pasos}', panel.lbl_paso.cget('text'))
            self.assertIn(f"Iteración {paso['iteracion']}", panel.lbl_paso.cget('text'))

            # 2. Tabla explícita de distancias d(v), predecesores π(v) y etiquetas [d,V](n) para los 7 nodos
            self.assertEqual(len(panel.tabla.get_children()), 7)
            for n in range(1, 8):
                valores = panel.tabla.item(str(n), 'values')
                dist_esperada = '∞' if math.isinf(paso['distancias'][n]) else f"{paso['distancias'][n]:g}"
                preds_esperados = ', '.join(chr(64 + p) for p in paso['predecesores'][n]) or '—'
                etiq_esperada = etiqueta_plana(paso, n, modo=panel._modo())
                self.assertEqual(valores[0], chr(64 + n))
                self.assertEqual(valores[1], dist_esperada)
                self.assertEqual(valores[2], preds_esperados)
                self.assertEqual(valores[4], etiq_esperada)

            # 3. Mensaje explicativo explícito bajo el lienzo en cada etapa
            texto_banner = panel.lbl_explicacion.cget('text')
            if etapa in ('INICIO', 'VISITADO', 'EVALUANDO'):
                self.assertIn('Iteración', texto_banner)
                self.assertIn('d(', texto_banner)
                self.assertIn('π(', texto_banner)
            elif etapa == 'FIN':
                self.assertIn('A → B → D → G', texto_banner)
                self.assertNotIn('A → C → E → F → G', texto_banner)
                # Confirmar que ninguna ruta aparece duplicada en el banner ni en el resumen
                self.assertEqual(texto_banner.count('A → B → D → G'), 1)
                self.assertEqual(texto_banner.count('A → C → E → F → G'), 0)
                self.assertEqual(panel.lbl_resumen.cget('text').count('A → B → D → G'), 1)
                self.assertEqual(panel.lbl_resumen.cget('text').count('A → C → E → F → G'), 0)

            # 4. Cajas de etiquetas [d,V](n) dibujadas para cada vértice en el lienzo
            self.assertEqual(set(panel.cajas_etiquetas.keys()), set(range(1, 8)))

            if idx < total_pasos - 1:
                app.manejador_siguiente_paso()

    def test_resolver_ahora_permite_retroceder_y_conserva_posiciones_manuales(self):
        app = self.app
        # Al pulsar «Resolver ahora», el botón «← Anterior» queda habilitado para revisar iteraciones
        app.manejador_ejecutar_dijkstra('A', 'G')
        self.assertEqual(str(app.panel_config.btn_anterior.cget('state')), 'normal')
        self.assertIn('A → B → D → G', app.panel_grafo.lbl_explicacion.cget('text'))
        self.assertNotIn('A → C → E → F → G', app.panel_grafo.lbl_explicacion.cget('text'))

        app.manejador_anterior_paso()
        self.assertEqual(app.indice_paso, len(app.pasos) - 2)
        self.assertIn('Iteración', app.panel_grafo.lbl_explicacion.cget('text'))

        # Mover manualmente un nodo y agregar una arista válida conserva la disposición manual
        app.panel_grafo.posiciones[4] = (123.0, 234.0)
        app.panel_grafo._posiciones_manuales = True
        app.manejador_agregar_arista('D', 'E', '3')
        self.assertEqual(app.panel_grafo.posiciones[4], (123.0, 234.0))

        # Hacer doble clic accidental sobre el mismo nodo de origen en el lienzo no pisa el destino
        app.panel_config.ent_destino_d.set('G')
        app.manejador_nodo_click(1)  # Selecciona origen A
        app.manejador_nodo_click(1)  # Clic repetido en A: sigue esperando destino distinto
        self.assertTrue(app._pendiente_destino)
        self.assertEqual(app.panel_config.ent_destino_d.get(), 'G')
        app.manejador_nodo_click(7)  # Ahora clic en G resuelve A -> G
        self.assertFalse(app._pendiente_destino)
        self.assertEqual(app.motor.distancias[7], 5.0)


if __name__ == '__main__':
    unittest.main(verbosity=2)

