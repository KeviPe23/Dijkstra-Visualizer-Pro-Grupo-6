"""Identidad visual con soporte dinámico de Modo Claro (predeterminado) y Modo Oscuro."""

FONT = 'Segoe UI'

# Adaptación de controles en pantallas Windows de 125 %, 150 % y 200 %.
UI_SCALE = 1.0


def dp(numero):
    return max(1, round(float(numero) * UI_SCALE))


# Paleta Modo Oscuro: conserva la identidad de Dijkstra_Visualizer_Version_1
# corrigiendo estados deshabilitados, barras de desplazamiento y contraste de controles.
PALETA_OSCURA = {
    'BG': '#0B1422',
    'PANEL': '#152235',
    'PANEL_ALT': '#1B2A40',
    'CANVAS': '#101C2C',
    'INPUT': '#23354D',
    'BORDER': '#32465E',
    'TEXT': '#F1F6FA',
    'MUTED': '#BDD0E0',
    'ACCENT': '#25BCCC',
    'ACCENT_ACTIVE': '#1599AC',
    'BLUE': '#2563EB',
    'BLUE_ACTIVE': '#1D4ED8',
    'GREEN': '#35D2A4',
    'RED': '#FB7185',
    'AMBER': '#F4C46C',
    # Botones activos y deshabilitados
    'BTN_PRIMARY_BG': '#25BCCC',
    'BTN_PRIMARY_FG': '#07212A',
    'BTN_PRIMARY_HOVER': '#1599AC',
    'BTN_SECONDARY_BG': '#21334B',
    'BTN_SECONDARY_FG': '#F1F6FA',
    'BTN_SECONDARY_HOVER': '#2B4260',
    'BTN_BLUE_BG': '#2563EB',
    'BTN_BLUE_FG': '#FFFFFF',
    'BTN_BLUE_HOVER': '#1D4ED8',
    'BTN_WARNING_BG': '#F4C46C',
    'BTN_WARNING_FG': '#111827',
    'BTN_WARNING_HOVER': '#E2AF4E',
    'BTN_DISABLED_BG': '#1A273A',
    'BTN_DISABLED_FG': '#7F95AE',
    'BTN_DISABLED_BORDER': '#2A3C53',
    # Controles auxiliares y tabla
    'SCROLL_THUMB': '#32465E',
    'SCROLL_THUMB_HOVER': '#466180',
    'SCROLL_TROUGH': '#152235',
    'CHECK_BG': '#23354D',
    'TABLE_ACTUAL': '#F4C46C',
    'TABLE_VISITADO': '#35D2A4',
    'TABLE_EVALUANDO': '#25BCCC',
    # Grafo HD y lienzo vectorial
    'EDGE_DEFAULT': '#9DB7CF',
    'WEIGHT_BG': '#1B2A40',
    'WEIGHT_BORDER': '#7691AB',
    'NODE_ACCENT': '#25BCCC',
    'NODE_GREEN': '#35D2A4',
    'NODE_RED': '#FB7185',
    'NODE_AMBER': '#F4C46C',
    'NODE_OUTLINE': '#D3F7F9',
    'NODE_TEXT': '#081B2B',
    # Etiquetas [d,V](n)
    'TAG_BG': '#1E3149',
    'TAG_SHADOW': '#0A111D',
    'TAG_GUIDE': '#86A4C3',
    'TAG_TEXT': '#F6FBFF',
    'TAG_STROKE': True,
    'TAG_STRIKE_TEXT': '#FFD6DC',
    'TAG_STRIKE_STROKE': '#843543',
    'TAG_STRIKE_LINE': '#FFD1D8',
    'TAG_SUB_ACTUAL': '#EAF7FF',
    'TAG_EXTRA_TEXT': '#EAF7FF',
    # Indicador "?" e información flotante
    'HELP_BG': '#3B82F6',
    'HELP_FG': '#FFFFFF',
    'TOOLTIP_BG': '#1F2937',
    'TOOLTIP_FG': '#FFFFFF',
    'TOOLTIP_BORDER': '#4B5563',
    # Interruptor de tema
    'SWITCH_ON_BG': '#25BCCC',
    'SWITCH_OFF_BG': '#475569',
    'SWITCH_KNOB': '#FFFFFF',
}


# Paleta Modo Claro (predeterminada): basada en Dijkstra_Visualizer_Version_0
# (#F0F2F5, #FFFFFF, #F9FAFB, #00E5FF) con alto contraste en todos los estados.
PALETA_CLARA = {
    'BG': '#F0F2F5',
    'PANEL': '#FFFFFF',
    'PANEL_ALT': '#F9FAFB',
    'CANVAS': '#FFFFFF',
    'INPUT': '#F3F4F6',
    'BORDER': '#CBD5E1',
    'TEXT': '#111827',
    'MUTED': '#475569',
    'ACCENT': '#0284C7',
    'ACCENT_ACTIVE': '#0369A1',
    'BLUE': '#2563EB',
    'BLUE_ACTIVE': '#1D4ED8',
    'GREEN': '#047857',
    'RED': '#DC2626',
    'AMBER': '#D97706',
    # Botones activos y deshabilitados (sin choques de texto gris sobre naranja/color)
    'BTN_PRIMARY_BG': '#00E5FF',
    'BTN_PRIMARY_FG': '#06202B',
    'BTN_PRIMARY_HOVER': '#00C4E0',
    'BTN_SECONDARY_BG': '#E2E8F0',
    'BTN_SECONDARY_FG': '#0F172A',
    'BTN_SECONDARY_HOVER': '#CBD5E1',
    'BTN_BLUE_BG': '#2563EB',
    'BTN_BLUE_FG': '#FFFFFF',
    'BTN_BLUE_HOVER': '#1D4ED8',
    'BTN_WARNING_BG': '#F59E0B',
    'BTN_WARNING_FG': '#111827',
    'BTN_WARNING_HOVER': '#D97706',
    'BTN_DISABLED_BG': '#E5E7EB',
    'BTN_DISABLED_FG': '#526071',
    'BTN_DISABLED_BORDER': '#CBD5E1',
    # Controles auxiliares y tabla
    'SCROLL_THUMB': '#CBD5E1',
    'SCROLL_THUMB_HOVER': '#94A3B8',
    'SCROLL_TROUGH': '#F1F5F9',
    'CHECK_BG': '#FFFFFF',
    'TABLE_ACTUAL': '#B45309',
    'TABLE_VISITADO': '#047857',
    'TABLE_EVALUANDO': '#0369A1',
    # Grafo HD y lienzo vectorial sobre blanco
    'EDGE_DEFAULT': '#64748B',
    'WEIGHT_BG': '#F8FAFC',
    'WEIGHT_BORDER': '#94A3B8',
    'NODE_ACCENT': '#00E5FF',
    'NODE_GREEN': '#34D399',
    'NODE_RED': '#FB7185',
    'NODE_AMBER': '#FCD34D',
    'NODE_OUTLINE': '#1E293B',
    'NODE_TEXT': '#081B2B',
    # Etiquetas [d,V](n) con contraste alto sobre fondo blanco
    'TAG_BG': '#F8FAFC',
    'TAG_SHADOW': '#CBD5E1',
    'TAG_GUIDE': '#64748B',
    'TAG_TEXT': '#0F172A',
    'TAG_STROKE': False,
    'TAG_STRIKE_TEXT': '#B91C1C',
    'TAG_STRIKE_STROKE': '#B91C1C',
    'TAG_STRIKE_LINE': '#DC2626',
    'TAG_SUB_ACTUAL': '#B45309',
    'TAG_EXTRA_TEXT': '#334155',
    # Indicador "?" e información flotante (idéntico a Version_0)
    'HELP_BG': '#3B82F6',
    'HELP_FG': '#FFFFFF',
    'TOOLTIP_BG': '#1F2937',
    'TOOLTIP_FG': '#FFFFFF',
    'TOOLTIP_BORDER': '#374151',
    # Interruptor de tema
    'SWITCH_ON_BG': '#25BCCC',
    'SWITCH_OFF_BG': '#94A3B8',
    'SWITCH_KNOB': '#FFFFFF',
}

MODO_OSCURO = False


def aplicar_tema(modo_oscuro: bool = False):
    """Actualiza en caliente las constantes visuales globales."""
    global MODO_OSCURO
    MODO_OSCURO = bool(modo_oscuro)
    paleta = PALETA_OSCURA if MODO_OSCURO else PALETA_CLARA
    globals().update(paleta)


# Inicializar en Modo Claro predeterminado.
aplicar_tema(False)
