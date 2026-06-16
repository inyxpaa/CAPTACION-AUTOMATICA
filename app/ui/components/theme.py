import streamlit as st


def get_theme() -> str:
    """Devuelve 'light' o 'dark' según la sesión."""
    if "theme" not in st.session_state:
        st.session_state["theme"] = "light"
    return st.session_state["theme"]


def toggle_theme():
    current = get_theme()
    st.session_state["theme"] = "dark" if current == "light" else "light"


# ─────────────────────────────────────────────────────────────
#  TEMA CLARO — espejo exacto del oscuro, colores invertidos
#  La estructura, sombras y jerarquía son idénticas al dark.
# ─────────────────────────────────────────────────────────────
LIGHT = {
    # Fondos (inverso del navy oscuro)
    "--color-bg":             "#f8fafc",     # blanco frío (= dark #0a0e1a)
    "--color-surface":        "#ffffff",     # blanco puro (= dark #111827)
    "--color-surface-2":      "#f1f5f9",     # gris muy claro (= dark #1f2937)
    "--color-border":         "#e2e8f0",     # borde sutil cool (= dark #2d3748)
    # Acento dorado (más oscuro para ser legible sobre blanco)
    "--color-gold":           "#8a6a18",     # dorado oscuro ámbar
    "--color-gold-light":     "#a07c20",
    # Acento azul (igual que dark, funciona en ambos)
    "--color-accent":         "#3b82f6",
    "--color-accent-dark":    "#1d4ed8",
    # Semáforos
    "--color-green":          "#059669",
    "--color-red":            "#dc2626",
    # Tipografía (inverso del blanco oscuro)
    "--color-text":           "#0f172a",     # casi negro (= dark #f1f5f9 invertido)
    "--color-text-muted":     "#64748b",     # gris medio (= dark #94a3b8)
    # Sidebar
    "--color-sidebar-bg":     "#f1f5f9",     # (= dark #111827)
    "--color-sidebar-border": "#e2e8f0",     # (= dark #2d3748)
    # Métricas
    "--metric-bg":            "#ffffff",
    "--metric-border":        "#e2e8f0",
    # Botones — mismos azules que dark
    "--btn-bg-start":         "#1d4ed8",
    "--btn-bg-end":           "#3b82f6",
    # Tarjetas módulo 1 — azul muy pálido (= dark navy oscuro)
    "--card1-bg-start":       "#eff6ff",
    "--card1-bg-end":         "#dbeafe",
    "--card1-title":          "#1d4ed8",
    # Tarjetas módulo 2 — verde muy pálido (= dark verde oscuro)
    "--card2-bg-start":       "#f0fdf4",
    "--card2-bg-end":         "#dcfce7",
    "--card2-title":          "#065f46",
    # Watermark
    "--watermark-color":      "rgba(15,23,42,0.18)",
}

# ─────────────────────────────────────────────────────────────
#  TEMA OSCURO — original elegante
# ─────────────────────────────────────────────────────────────
DARK = {
    "--color-bg":             "#0a0e1a",
    "--color-surface":        "#111827",
    "--color-surface-2":      "#1f2937",
    "--color-border":         "#2d3748",
    "--color-gold":           "#e2c36b",
    "--color-gold-light":     "#f0d98a",
    "--color-accent":         "#3b82f6",
    "--color-accent-dark":    "#1d4ed8",
    "--color-green":          "#10b981",
    "--color-red":            "#ef4444",
    "--color-text":           "#f1f5f9",
    "--color-text-muted":     "#94a3b8",
    "--color-sidebar-bg":     "#111827",
    "--color-sidebar-border": "#2d3748",
    "--metric-bg":            "#111827",
    "--metric-border":        "#2d3748",
    "--btn-bg-start":         "#1d4ed8",
    "--btn-bg-end":           "#3b82f6",
    "--card1-bg-start":       "#1a1a2e",
    "--card1-bg-end":         "#0f3460",
    "--card1-title":          "#e2c36b",
    "--card2-bg-start":       "#0d3b2e",
    "--card2-bg-end":         "#1a5c45",
    "--card2-title":          "#a8e6cf",
    "--watermark-color":      "rgba(255,255,255,0.18)",
}


def inject_theme_css():
    """Inyecta el CSS del tema activo en la página."""
    theme = get_theme()
    vars_dict = LIGHT if theme == "light" else DARK
    css_vars = "\n".join(f"    {k}: {v};" for k, v in vars_dict.items())

    css = f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

  :root {{
{css_vars}
    --font-main: 'Inter', sans-serif;
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --shadow-sm: 0 1px 4px rgba(0,0,0,0.07), 0 1px 2px rgba(0,0,0,0.05);
    --shadow-md: 0 4px 16px rgba(0,0,0,0.10);
  }}

  html, body, [class*="css"] {{
    font-family: var(--font-main) !important;
  }}

  /* Fondo principal */
  .stApp {{
    background: var(--color-bg) !important;
    color: var(--color-text) !important;
  }}

  /* Sidebar */
  [data-testid="stSidebar"] {{
    background: var(--color-sidebar-bg) !important;
    border-right: 1px solid var(--color-sidebar-border) !important;
  }}
  [data-testid="stSidebar"] .stMarkdown h1,
  [data-testid="stSidebar"] .stMarkdown h2,
  [data-testid="stSidebar"] .stMarkdown h3 {{
    color: var(--color-gold) !important;
  }}

  /* Tipografía */
  h1, h2, h3, h4, h5, h6 {{
    color: var(--color-text) !important;
    letter-spacing: -0.3px;
  }}
  p, span, label, div {{
    color: var(--color-text) !important;
  }}

  /* Botones — idénticos en ambos temas */
  .stButton > button {{
    background: linear-gradient(135deg, var(--btn-bg-start), var(--btn-bg-end)) !important;
    color: white !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-family: var(--font-main) !important;
    letter-spacing: 0.2px !important;
    transition: all 0.2s ease !important;
    box-shadow: var(--shadow-sm) !important;
  }}
  .stButton > button:hover {{
    transform: translateY(-1px) !important;
    box-shadow: var(--shadow-md) !important;
    filter: brightness(1.07) !important;
  }}

  /* Métricas */
  [data-testid="stMetric"] {{
    background: var(--metric-bg) !important;
    border: 1px solid var(--metric-border) !important;
    border-radius: var(--radius-md) !important;
    padding: 16px 20px !important;
    box-shadow: var(--shadow-sm) !important;
  }}
  [data-testid="stMetricValue"] {{
    color: var(--color-gold) !important;
    font-weight: 800 !important;
    font-size: 2rem !important;
  }}
  [data-testid="stMetricLabel"] {{
    color: var(--color-text-muted) !important;
    font-size: 0.82rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
  }}

  /* Tablas */
  [data-testid="stDataFrame"] {{
    border: 1px solid var(--color-border) !important;
    border-radius: var(--radius-sm) !important;
    overflow: hidden !important;
    box-shadow: var(--shadow-sm) !important;
  }}

  /* Inputs */
  .stTextInput > div > div > input,
  .stSelectbox > div > div > select,
  .stTextArea > div > div > textarea {{
    background: var(--color-surface-2) !important;
    color: var(--color-text) !important;
    border: 1px solid var(--color-border) !important;
    border-radius: var(--radius-sm) !important;
    transition: border-color 0.15s ease !important;
  }}
  .stTextInput > div > div > input:focus,
  .stTextArea > div > div > textarea:focus {{
    border-color: var(--color-accent) !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.15) !important;
  }}

  /* Alertas */
  .stSuccess, .stWarning, .stError, .stInfo {{
    border-radius: var(--radius-sm) !important;
  }}

  /* Expanders */
  .streamlit-expanderHeader {{
    background: var(--color-surface-2) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--color-text) !important;
    border: 1px solid var(--color-border) !important;
  }}

  /* Tabs */
  .stTabs [data-baseweb="tab"] {{
    color: var(--color-text-muted) !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
  }}
  .stTabs [aria-selected="true"] {{
    color: var(--color-gold) !important;
    border-bottom-color: var(--color-gold) !important;
  }}

  /* Scrollbar */
  ::-webkit-scrollbar {{ width: 5px; }}
  ::-webkit-scrollbar-track {{ background: var(--color-bg); }}
  ::-webkit-scrollbar-thumb {{ background: var(--color-border); border-radius: 3px; }}
  ::-webkit-scrollbar-thumb:hover {{ background: var(--color-text-muted); }}

  /* Watermark */
  .oresna-watermark {{
    position: fixed;
    bottom: 14px;
    right: 18px;
    font-size: 0.68rem;
    color: var(--watermark-color);
    font-family: var(--font-main);
    font-weight: 400;
    letter-spacing: 0.4px;
    pointer-events: none;
    z-index: 9999;
    user-select: none;
  }}
</style>
"""
    st.markdown(css, unsafe_allow_html=True)


def inject_watermark():
    """Inyecta el watermark fijo en la esquina inferior derecha."""
    st.markdown(
        '<div class="oresna-watermark">Desarrollado por Iñigo Del Mazo Monreal</div>',
        unsafe_allow_html=True,
    )


def render_theme_toggle(sidebar: bool = True):
    """Renderiza el botón de toggle de tema."""
    theme = get_theme()
    label = "Tema claro" if theme == "dark" else "Tema oscuro"
    if sidebar:
        if st.sidebar.button(label, key="theme_toggle_btn"):
            toggle_theme()
            st.rerun()
    else:
        if st.button(label, key="theme_toggle_btn"):
            toggle_theme()
            st.rerun()
