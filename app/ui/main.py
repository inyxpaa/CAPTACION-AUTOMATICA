import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root))

import streamlit as st
from app.core.config import config
from app.core.db import init_db
from app.core.i18n import t, LANGUAGE_OPTIONS, get_lang
from app.ui.components.theme import inject_theme_css, inject_watermark

st.set_page_config(
    page_title="ORESNA CAPTADOR",
    page_icon="O",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "ORESNA CAPTADOR v1.0 — Plataforma de Captacion B2B con IA\nDesarrollado por Iñigo Del Mazo Monreal",
    }
)

inject_theme_css()
inject_watermark()

if "db_inicializada" not in st.session_state:
    try:
        init_db()
        st.session_state.db_inicializada = True
    except Exception as e:
        st.error(f"Error al inicializar la base de datos: {e}")

GOLD  = "#e2c36b"
MUTED = "#94a3b8"
CARD1_START = "#1a1a2e"
CARD1_END   = "#0f3460"
CARD2_START = "#0d3b2e"
CARD2_END   = "#1a5c45"
CARD1_TITLE = "#e2c36b"
CARD2_TITLE = "#a8e6cf"

with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding: 20px 0 10px;">
        <h2 style="color:{GOLD}; margin:0; font-size:1.4rem; font-weight:800; letter-spacing:1px;">ORESNA</h2>
        <p style="color:#64748b; font-size:0.75rem; margin:2px 0 0; letter-spacing:2px;">CAPTADOR &middot; B2B IA</p>
    </div>
    <hr style="border-color:#2d3748; margin:16px 0;">
    """, unsafe_allow_html=True)

    lang_labels = list(LANGUAGE_OPTIONS.values())
    lang_codes = list(LANGUAGE_OPTIONS.keys())
    current_lang = get_lang()
    current_idx = lang_codes.index(current_lang) if current_lang in lang_codes else 0

    selected_label = st.selectbox(
        "Idioma / Language / Hizkuntza",
        options=lang_labels,
        index=current_idx,
        key="lang_selector"
    )
    selected_code = lang_codes[lang_labels.index(selected_label)]
    if selected_code != current_lang:
        st.session_state["lang"] = selected_code
        st.rerun()

    st.markdown('<hr style="border-color:#2d3748; margin:16px 0;">', unsafe_allow_html=True)

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
    <h1 style="font-size:2.8rem; font-weight:800; color:{GOLD}; margin:0; letter-spacing:-1px;">
        {t("home_headline")}
    </h1>
    <p style="color:{MUTED}; font-size:1.1rem; margin-top:12px; max-width:600px; margin-left:auto; margin-right:auto;">
        {t("home_subtitle")}
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown(f"""
    <div style="background:linear-gradient(135deg, {CARD1_START}, {CARD1_END}); border:1px solid #2d3748;
                border-radius:16px; padding:28px; min-height:160px; transition:all 0.3s ease;">
        <h3 style="color:{CARD1_TITLE}; margin:0 0 8px; font-size:1.2rem; font-weight:700;">
            {t("module1_title")}
        </h3>
        <p style="color:{MUTED}; font-size:0.9rem; line-height:1.5; margin:0;">
            {t("module1_desc")}
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="background:linear-gradient(135deg, {CARD2_START}, {CARD2_END}); border:1px solid #2d3748;
                border-radius:16px; padding:28px; min-height:160px; transition:all 0.3s ease;">
        <h3 style="color:{CARD2_TITLE}; margin:0 0 8px; font-size:1.2rem; font-weight:700;">
            {t("module2_title")}
        </h3>
        <p style="color:{MUTED}; font-size:0.9rem; line-height:1.5; margin:0;">
            {t("module2_desc")}
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.info(t("nav_hint"))
