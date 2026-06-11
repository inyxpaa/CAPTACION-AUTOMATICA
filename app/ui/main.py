import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root))

import streamlit as st
from app.core.config import config
from app.core.db import init_db
from app.core.i18n import t, LANGUAGE_OPTIONS, get_lang

st.set_page_config(
    page_title="ORESNA CAPTADOR",
    page_icon="O",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "ORESNA CAPTADOR v1.0 — Plataforma de Captacion B2B con IA",
    }
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

  :root {
    --color-bg: #0a0e1a;
    --color-surface: #111827;
    --color-surface-2: #1f2937;
    --color-border: #2d3748;
    --color-gold: #e2c36b;
    --color-gold-light: #f0d98a;
    --color-blue: #3b82f6;
    --color-blue-dark: #1d4ed8;
    --color-green: #10b981;
    --color-red: #ef4444;
    --color-text: #f1f5f9;
    --color-text-muted: #94a3b8;
    --font-main: 'Inter', sans-serif;
  }

  html, body, [class*="css"] {
    font-family: var(--font-main) !important;
  }

  .stApp {
    background: var(--color-bg) !important;
    color: var(--color-text) !important;
  }

  [data-testid="stSidebar"] {
    background: var(--color-surface) !important;
    border-right: 1px solid var(--color-border) !important;
  }

  [data-testid="stSidebar"] .stMarkdown h1,
  [data-testid="stSidebar"] .stMarkdown h2,
  [data-testid="stSidebar"] .stMarkdown h3 {
    color: var(--color-gold) !important;
  }

  .stButton > button {
    background: linear-gradient(135deg, #1d4ed8, #3b82f6) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-family: var(--font-main) !important;
    transition: all 0.2s ease !important;
  }

  .stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
  }

  [data-testid="stMetric"] {
    background: var(--color-surface) !important;
    border: 1px solid var(--color-border) !important;
    border-radius: 12px !important;
    padding: 16px !important;
  }

  [data-testid="stMetricValue"] {
    color: var(--color-gold) !important;
    font-weight: 800 !important;
    font-size: 2rem !important;
  }

  [data-testid="stMetricLabel"] {
    color: var(--color-text-muted) !important;
    font-size: 0.85rem !important;
  }

  [data-testid="stDataFrame"] {
    border: 1px solid var(--color-border) !important;
    border-radius: 8px !important;
    overflow: hidden !important;
  }

  .stTextInput > div > div > input,
  .stSelectbox > div > div > select {
    background: var(--color-surface-2) !important;
    color: var(--color-text) !important;
    border: 1px solid var(--color-border) !important;
    border-radius: 8px !important;
  }

  .stSuccess, .stWarning, .stError, .stInfo {
    border-radius: 8px !important;
  }

  .streamlit-expanderHeader {
    background: var(--color-surface) !important;
    border-radius: 8px !important;
    color: var(--color-text) !important;
  }

  .stTabs [data-baseweb="tab"] {
    color: var(--color-text-muted) !important;
    font-weight: 500 !important;
  }

  .stTabs [aria-selected="true"] {
    color: var(--color-gold) !important;
    border-bottom-color: var(--color-gold) !important;
  }

  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: var(--color-bg); }
  ::-webkit-scrollbar-thumb { background: var(--color-border); border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: var(--color-text-muted); }
</style>
""", unsafe_allow_html=True)

if "db_inicializada" not in st.session_state:
    try:
        init_db()
        st.session_state.db_inicializada = True
    except Exception as e:
        st.error(f"Error al inicializar la base de datos: {e}")

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 10px;">
        <h2 style="color:#e2c36b; margin:0; font-size:1.4rem; font-weight:800; letter-spacing:1px;">ORESNA</h2>
        <p style="color:#64748b; font-size:0.75rem; margin:2px 0 0; letter-spacing:2px;">CAPTADOR · B2B IA</p>
    </div>
    <hr style="border-color:#2d3748; margin:16px 0;">
    """, unsafe_allow_html=True)

    lang_labels = list(LANGUAGE_OPTIONS.values())
    lang_codes = list(LANGUAGE_OPTIONS.keys())
    current_lang = get_lang()
    current_idx = lang_codes.index(current_lang) if current_lang in lang_codes else 0

    selected_label = st.selectbox(
        "Language / Idioma / Hizkuntza",
        options=lang_labels,
        index=current_idx,
        key="lang_selector"
    )
    selected_code = lang_codes[lang_labels.index(selected_label)]
    if selected_code != current_lang:
        st.session_state["lang"] = selected_code
        st.rerun()

    warnings = config.validate()
    if warnings:
        for w in warnings:
            st.warning(w)
    else:
        st.success(t("system_configured"))

    st.markdown(f"""
    <hr style="border-color:#2d3748; margin:16px 0;">
    <p style="color:#64748b; font-size:0.75rem; text-align:center;">
    {t("sidebar_nav_hint")}
    </p>
    """, unsafe_allow_html=True)

st.markdown(f"""
<div style="text-align:center; padding:60px 20px 40px;">
    <h1 style="font-size:2.8rem; font-weight:800; color:#e2c36b; margin:0; letter-spacing:-1px;">
        {t("home_headline")}
    </h1>
    <p style="color:#94a3b8; font-size:1.1rem; margin-top:12px; max-width:600px; margin-left:auto; margin-right:auto;">
        {t("home_subtitle")}
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown(f"""
    <div style="background:linear-gradient(135deg, #1a1a2e, #0f3460); border:1px solid #2d3748;
                border-radius:16px; padding:28px; height:200px; cursor:pointer;
                transition:all 0.3s ease;">
        <h3 style="color:#e2c36b; margin:0 0 8px; font-size:1.2rem; font-weight:700;">
            {t("module1_title")}
        </h3>
        <p style="color:#94a3b8; font-size:0.9rem; line-height:1.5; margin:0;">
            {t("module1_desc")}
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="background:linear-gradient(135deg, #0d3b2e, #1a5c45); border:1px solid #2d3748;
                border-radius:16px; padding:28px; height:200px; cursor:pointer;
                transition:all 0.3s ease;">
        <h3 style="color:#a8e6cf; margin:0 0 8px; font-size:1.2rem; font-weight:700;">
            {t("module2_title")}
        </h3>
        <p style="color:#94a3b8; font-size:0.9rem; line-height:1.5; margin:0;">
            {t("module2_desc")}
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.info(t("nav_hint"))
