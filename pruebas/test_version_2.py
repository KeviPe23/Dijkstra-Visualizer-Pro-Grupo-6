"""Pruebas integrales de las mejoras de Dijkstra_Visualizer_Version_2:
- Pantalla de inicio con selección de cantidad inicial de nodos (7 a 16)
- Modo Claro predeterminado y switch dinámico hacia Modo Oscuro (paleta Version_1)
- Indicador informativo '?' NO clickeable en el encabezado de cada una de las 7 secciones
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from servicios.validador_grafo import ValidadorGrafo
from ui import estilos as E
from ui import render_hd


class PruebasVersion2(unittest.TestCase):
    def setUp(self):
        if sys.platform.startswith('linux') and not os.environ.get('DISPLAY'):
            self.skipTest('Entorno sin pantalla gráfica')
        from ui.app import App
        self.App = App
        self.app = None

    def tearDown(self):
        if self.app is not None:
            try:
                self.app.destroy()
            except Exception:
                pass
        E.aplicar_tema(False)

    def test_pantalla_inicio_validacion_y_generacion_dag(self):
        self.app = self.App()  # Por defecto abre VentanaInicio
        self.app.update_idletasks()
        self.app.update()

        self.assertTrue(self.app.en_pantalla_inicio)
        inicio = self.app.pantalla_inicio
        self.assertIsNotNone(inicio)
        self.assertEqual(inicio.cget('bg').upper(), '#111827')
        self.assertEqual(inicio.entrada_nodos.get(), '7')

        # Rechazar valores fuera de rango o no numéricos
        for invalido, esperado in [('5', '7 y 16'), ('19', '7 y 16'), ('abc', 'válido')]:
            inicio.entrada_nodos.delete(0, 'end')
            inicio.entrada_nodos.insert(0, invalido)
            self.assertFalse(inicio._validar_y_comenzar())
            self.assertTrue(self.app.en_pantalla_inicio)
            self.assertIn(esperado, inicio.lbl_error.cget('text'))

        # Ingresar 10 nodos y comenzar
        inicio.entrada_nodos.delete(0, 'end')
        inicio.entrada_nodos.insert(0, '10')
        inicio.btn_comenzar.invoke()
        self.app.update_idletasks()
        self.app.update()

        self.assertFalse(self.app.en_pantalla_inicio)
        self.assertIsNotNone(self.app.grafo_actual)
        self.assertEqual(self.app.grafo_actual.cantidad_nodos(), 10)
        self.assertFalse(ValidadorGrafo.tiene_ciclos(self.app.grafo_actual))
        self.assertEqual(self.app.panel_config.ent_origen_d.get(), 'A')
        self.assertEqual(self.app.panel_config.ent_destino_d.get(), 'J')

    def test_modo_claro_predeterminado_y_switch_modo_oscuro(self):
        self.app = self.App()
        self.app.pantalla_inicio.btn_comenzar.invoke()
        self.app.update_idletasks()
        self.app.update()

        # Verificar Modo Claro predeterminado (basado en Version_0)
        self.assertFalse(E.MODO_OSCURO)
        self.assertFalse(self.app.switch_tema.get())
        self.assertEqual(E.BG.upper(), '#F0F2F5')
        self.assertEqual(E.PANEL.upper(), '#FFFFFF')
        self.assertEqual(E.CANVAS.upper(), '#FFFFFF')
        self.assertEqual(self.app.cget('bg').upper(), '#F0F2F5')
        self.assertEqual(self.app.panel_grafo.canvas.cget('bg').upper(), '#FFFFFF')

        # Cargar ejemplo docente, resolver y abrir ventanas auxiliares antes de alternar tema
        self.app.cargar_ejemplo()
        self.app.manejador_ejecutar_dijkstra('A', 'G')
        vh = self.app.panel_grafo.abrir_historial()
        vm = self.app.panel_grafo.abrir_matriz()
        va = self.app.panel_grafo.abrir_vista_ampliada()
        self.app.update_idletasks()
        self.app.update()

        posiciones_previas = dict(self.app.panel_grafo.posiciones)
        if render_hd.disponible():
            img_clara = self.app.panel_grafo._crear_imagen_hd(escala_salida=1.0, suavizado=2)

        # Activar Modo Oscuro mediante el switch -> paleta exacta de Version_1
        self.app.switch_tema.toggle()
        self.app.update_idletasks()
        self.app.update()

        self.assertTrue(E.MODO_OSCURO)
        self.assertTrue(self.app.switch_tema.get())
        self.assertEqual(E.BG.upper(), '#0B1422')
        self.assertEqual(E.PANEL.upper(), '#152235')
        self.assertEqual(E.CANVAS.upper(), '#101C2C')
        self.assertEqual(self.app.cget('bg').upper(), '#0B1422')
        self.assertEqual(self.app.panel_grafo.canvas.cget('bg').upper(), '#101C2C')
        self.assertEqual(vh.cget('bg').upper(), '#0B1422')
        self.assertEqual(vm.cget('bg').upper(), '#0B1422')
        self.assertEqual(va.cget('bg').upper(), '#0B1422')
        self.assertEqual(self.app.panel_grafo.posiciones, posiciones_previas)
        self.assertEqual(self.app.motor.distancias[7], 5)

        if render_hd.disponible():
            from PIL import ImageChops
            img_oscura = self.app.panel_grafo._crear_imagen_hd(escala_salida=1.0, suavizado=2)
            self.assertIsNotNone(ImageChops.difference(img_clara, img_oscura).getbbox())

        # Volver a Modo Claro
        self.app.switch_tema.toggle()
        self.app.update_idletasks()
        self.app.update()
        self.assertFalse(E.MODO_OSCURO)
        self.assertEqual(self.app.cget('bg').upper(), '#F0F2F5')

        vh.destroy()
        vm.destroy()
        va.destroy()

    def test_siete_indicadores_ayuda_no_clickeables_con_hover(self):
        self.app = self.App(mostrar_inicio=False)
        self.app.update_idletasks()
        self.app.update()

        ind_lateral = self.app.panel_config.indicadores_ayuda
        ind_central = self.app.panel_grafo.indicadores_ayuda
        self.assertEqual(len(ind_lateral), 4, 'Deben existir 4 indicadores en las secciones 01–04')
        self.assertEqual(len(ind_central), 3, 'Deben existir 3 indicadores en Grafo, Numeración n y Tabla')

        todos = ind_lateral + ind_central
        nodos_antes = len(self.app.grafo_actual.nodos)
        for ind in todos:
            self.assertEqual(ind.cget('cursor'), 'arrow')
            self.assertEqual(ind._ignorar_clic(), 'break')
            self.assertIsNone(ind.tooltip.tw)
            ind.tooltip.mostrar()
            self.app.update_idletasks()
            self.assertIsNotNone(ind.tooltip.tw)
            self.assertTrue(ind.tooltip.tw.winfo_exists())
            self.assertGreater(len(ind.texto_ayuda), 30)
            ind.tooltip.ocultar()
            self.assertIsNone(ind.tooltip.tw)
        self.assertEqual(len(self.app.grafo_actual.nodos), nodos_antes)

    @staticmethod
    def _contraste_wcag(hex_a: str, hex_b: str) -> float:
        def lum(h):
            h = h.lstrip('#')
            canales = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
            lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canales]
            return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]

        l1, l2 = lum(hex_a), lum(hex_b)
        mayor, menor = max(l1, l2), min(l1, l2)
        return (mayor + 0.05) / (menor + 0.05)

    def test_paleta_boton_siguiente_y_contraste_controles_en_ambos_temas(self):
        self.app = self.App(mostrar_inicio=False)
        self.app.update_idletasks()
        self.app.update()
        cfg = self.app.panel_config

        # 1. Al iniciar en Modo Claro, «Siguiente →» y «← Anterior» están deshabilitados:
        # jamás deben conservar fondo naranja/ámbar con letra gris.
        self.assertEqual(str(cfg.btn_siguiente.cget('state')), 'disabled')
        self.assertEqual(cfg.btn_siguiente.cget('bg').upper(), E.PALETA_CLARA['BTN_DISABLED_BG'])
        self.assertEqual(cfg.btn_siguiente.cget('disabledforeground').upper(), E.PALETA_CLARA['BTN_DISABLED_FG'])
        self.assertEqual(cfg.btn_siguiente.cget('cursor'), 'arrow')
        self.assertGreaterEqual(
            self._contraste_wcag(cfg.btn_siguiente.cget('bg'), cfg.btn_siguiente.cget('disabledforeground')),
            4.0,
        )

        # Alternar a Modo Oscuro mientras está deshabilitado mantiene apariencia limpia deshabilitada
        self.app.switch_tema.toggle()
        self.app.update_idletasks()
        self.assertEqual(str(cfg.btn_siguiente.cget('state')), 'disabled')
        self.assertEqual(cfg.btn_siguiente.cget('bg').upper(), E.PALETA_OSCURA['BTN_DISABLED_BG'])
        self.assertGreaterEqual(
            self._contraste_wcag(cfg.btn_siguiente.cget('bg'), cfg.btn_siguiente.cget('disabledforeground')),
            3.7,
        )

        # Volver a Modo Claro e iniciar simulación paso a paso -> «Siguiente →» se habilita con alto contraste
        self.app.switch_tema.toggle()
        self.app.manejador_iniciar_pasos('A', 'G')
        self.app.manejador_siguiente_paso()  # Ahora ambos («← Anterior» y «Siguiente →») están activos
        self.app.update_idletasks()

        for modo_oscuro in (False, True):
            self.app.cambiar_tema(modo_oscuro)
            self.app.update_idletasks()
            self.assertEqual(str(cfg.btn_siguiente.cget('state')), 'normal')
            self.assertEqual(str(cfg.btn_anterior.cget('state')), 'normal')
            self.assertEqual(cfg.btn_siguiente.cget('cursor'), 'hand2')
            for btn in cfg._botones + self.app.panel_grafo._botones_accion:
                bg = btn.cget('bg')
                fg = btn.cget('fg') if str(btn.cget('state')) != 'disabled' else btn.cget('disabledforeground')
                self.assertGreaterEqual(
                    self._contraste_wcag(bg, fg),
                    4.5,
                    f'Contraste insuficiente en botón «{btn.cget("text")}» (modo_oscuro={modo_oscuro}): {bg} vs {fg}',
                )

    def test_disposicion_variada_en_grafos_aleatorios_y_manuales(self):
        import math
        self.app = self.App(mostrar_inicio=False)
        self.app.update_idletasks()
        self.app.update()
        panel = self.app.panel_grafo

        tipos_vistos = []
        instantaneas_pos = []
        # Generar 6 grafos alternando aleatorios y manuales: debe recorrer circular, cuadrado y aleatorio
        for idx in range(6):
            if idx % 2 == 0:
                self.app.manejador_generar_aleatorio(9)
            else:
                self.app.manejador_iniciar_manual(9)
            self.app.update_idletasks()
            self.app.update()
            self.assertEqual(panel._modo_disposicion, 'variada')
            self.assertIn(panel.tipo_layout_actual, ('circular', 'cuadrado', 'aleatorio'))
            if tipos_vistos:
                # Nunca repite exactamente la misma figura dos veces seguidas
                self.assertNotEqual(panel.tipo_layout_actual, tipos_vistos[-1])
            tipos_vistos.append(panel.tipo_layout_actual)
            instantaneas_pos.append(dict(panel.posiciones))

            # Ningún par de nodos debe quedar encimado (radio = 22 px => diámetro = 44 px)
            coords = list(panel.posiciones.values())
            for i in range(len(coords)):
                for j in range(i + 1, len(coords)):
                    dist = math.hypot(coords[i][0] - coords[j][0], coords[i][1] - coords[j][1])
                    self.assertGreaterEqual(dist, 50.0)

        self.assertEqual(set(tipos_vistos), {'circular', 'cuadrado', 'aleatorio'})
        self.assertNotEqual(instantaneas_pos[0], instantaneas_pos[1])

        # En modo manual, al agregar y quitar aristas se conservan las posiciones generadas (no salta a columnas)
        self.app.manejador_iniciar_manual(8)
        self.app.update_idletasks()
        pos_manual_inicial = dict(panel.posiciones)
        tipo_manual = panel.tipo_layout_actual
        self.app.manejador_agregar_arista('A', 'B', '4')
        self.app.manejador_agregar_arista('B', 'H', '3')
        self.assertEqual(panel.posiciones, pos_manual_inicial)
        self.assertEqual(panel.tipo_layout_actual, tipo_manual)
        self.app.manejador_eliminar_arista('A', 'B')
        self.assertEqual(panel.posiciones, pos_manual_inicial)


if __name__ == '__main__':
    unittest.main()

