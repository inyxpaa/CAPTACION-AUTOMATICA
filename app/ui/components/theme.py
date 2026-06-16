import streamlit as st


def inject_theme_css():
    """Inyecta el CSS del tema oscuro elegante en la página."""

    css = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

  :root {
    --color-bg:             #0a0e1a;
    --color-surface:        #111827;
    --color-surface-2:      #1f2937;
    --color-border:         #2d3748;
    --color-gold:           #e2c36b;
    --color-gold-light:     #f0d98a;
    --color-blue:           #3b82f6;
    --color-blue-dark:      #1d4ed8;
    --color-green:          #10b981;
    --color-red:            #ef4444;
    --color-text:           #f1f5f9;
    --color-text-muted:     #94a3b8;
    --color-sidebar-bg:     #111827;
    --color-sidebar-border: #2d3748;
    --metric-bg:            #111827;
    --metric-border:        #2d3748;
    --btn-bg-start:         #1d4ed8;
    --btn-bg-end:           #3b82f6;
    --font-main:            'Inter', sans-serif;
    --radius-sm:            8px;
    --radius-md:            12px;
    --radius-lg:            16px;
    --shadow-sm:            0 1px 4px rgba(0,0,0,0.25), 0 1px 2px rgba(0,0,0,0.18);
    --shadow-md:            0 4px 16px rgba(0,0,0,0.35);
  }

  html, body, [class*="css"] {
    font-family: var(--font-main) !important;
  }

  .stApp {
    background: var(--color-bg) !important;
    color: var(--color-text) !important;
  }

  [data-testid="stSidebar"] {
    background: var(--color-sidebar-bg) !important;
    border-right: 1px solid var(--color-sidebar-border) !important;
  }
  [data-testid="stSidebar"] .stMarkdown h1,
  [data-testid="stSidebar"] .stMarkdown h2,
  [data-testid="stSidebar"] .stMarkdown h3 {
    color: var(--color-gold) !important;
  }

  h1, h2, h3, h4, h5, h6 {
    color: var(--color-text) !important;
    letter-spacing: -0.3px;
  }
  p, span, label, div {
    color: var(--color-text) !important;
  }

  /* Botones */
  .stButton > button {
    background: linear-gradient(135deg, var(--btn-bg-start), var(--btn-bg-end)) !important;
    color: white !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-family: var(--font-main) !important;
    letter-spacing: 0.2px !important;
    transition: all 0.2s ease !important;
    box-shadow: var(--shadow-sm) !important;
  }
  .stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: var(--shadow-md) !important;
    filter: brightness(1.07) !important;
  }

  /* Métricas */
  [data-testid="stMetric"] {
    background: var(--metric-bg) !important;
    border: 1px solid var(--metric-border) !important;
    border-radius: var(--radius-md) !important;
    padding: 16px 20px !important;
    box-shadow: var(--shadow-sm) !important;
  }
  [data-testid="stMetricValue"] {
    color: var(--color-gold) !important;
    font-weight: 800 !important;
    font-size: 2rem !important;
  }
  [data-testid="stMetricLabel"] {
    color: var(--color-text-muted) !important;
    font-size: 0.82rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
  }

  /* Tablas */
  [data-testid="stDataFrame"] {
    border: 1px solid var(--color-border) !important;
    border-radius: var(--radius-sm) !important;
    overflow: hidden !important;
    box-shadow: var(--shadow-sm) !important;
  }

  /* Inputs */
  .stTextInput > div > div > input,
  .stSelectbox > div > div > select,
  .stTextArea > div > div > textarea {
    background: var(--color-surface-2) !important;
    color: var(--color-text) !important;
    border: 1px solid var(--color-border) !important;
    border-radius: var(--radius-sm) !important;
    transition: border-color 0.15s ease !important;
  }
  .stTextInput > div > div > input:focus,
  .stTextArea > div > div > textarea:focus {
    border-color: var(--color-blue) !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.15) !important;
  }

  /* Alertas */
  .stSuccess, .stWarning, .stError, .stInfo {
    border-radius: var(--radius-sm) !important;
  }

  /* Expanders */
  .streamlit-expanderHeader {
    background: var(--color-surface-2) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--color-text) !important;
    border: 1px solid var(--color-border) !important;
  }

  /* Tabs */
  .stTabs [data-baseweb="tab"] {
    color: var(--color-text-muted) !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
  }
  .stTabs [aria-selected="true"] {
    color: var(--color-gold) !important;
    border-bottom-color: var(--color-gold) !important;
  }

  /* Scrollbar */
  ::-webkit-scrollbar { width: 5px; }
  ::-webkit-scrollbar-track { background: var(--color-bg); }
  ::-webkit-scrollbar-thumb { background: var(--color-border); border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: var(--color-text-muted); }

  /* Watermark */
  .oresna-watermark {
    position: fixed;
    bottom: 14px;
    right: 18px;
    font-size: 0.68rem;
    color: rgba(255,255,255,0.18);
    font-family: var(--font-main);
    font-weight: 400;
    letter-spacing: 0.4px;
    pointer-events: none;
    z-index: 9999;
    user-select: none;
  }
</style>
"""
    st.markdown(css, unsafe_allow_html=True)


def inject_watermark():
    """Inyecta el watermark fijo en la esquina inferior derecha."""
    st.markdown(
        '<div class="oresna-watermark">Desarrollado por Iñigo Del Mazo Monreal</div>',
        unsafe_allow_html=True,
    )
