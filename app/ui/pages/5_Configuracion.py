import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import streamlit as st
from pathlib import Path

from app.core.config import config
from app.core.i18n import t

st.set_page_config(page_title="Configuracion · ORESNA", page_icon="O", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.stApp { background: #0a0e1a !important; color: #f1f5f9 !important; }
[data-testid="stSidebar"] { background: #111827 !important; border-right: 1px solid #2d3748 !important; }
.stButton > button { background: linear-gradient(135deg, #374151, #4b5563) !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<h1 style="color:#e2c36b; font-weight:800; font-size:2rem; margin-bottom:4px;">
    {t("config_title")}
</h1>
<p style="color:#64748b; font-size:0.95rem; margin-bottom:28px;">
    {t("config_subtitle")}
</p>
""", unsafe_allow_html=True)

st.markdown(f"### {t('system_status')}")

col1, col2, col3 = st.columns(3)
with col1:
    llm_ok = bool(config.get_llm_api_key())
    if llm_ok:
        st.success(f"{t('llm_ok')}: {config.LLM_PROVIDER.upper()} · {config.LLM_MODEL}")
    else:
        st.error(f"{t('llm_error')}: {config.LLM_PROVIDER.upper()}")

with col2:
    email_ok = bool(config.RESEND_API_KEY)
    if email_ok:
        st.success(t("email_ok"))
    else:
        st.warning(t("email_warn"))

with col3:
    db_path = Path(config.DATABASE_URL.replace("sqlite:///", ""))
    if db_path.exists():
        size_kb = round(db_path.stat().st_size / 1024, 1)
        st.success(f"{t('db_ok')} · {size_kb} KB")
    else:
        st.info(t("db_pending"))

st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([t("tab_ia"), t("tab_email"), t("tab_scraping"), t("tab_company")])

ENV_PATH = config.BASE_DIR / ".env"


def leer_env() -> dict:
    vars_env = {}
    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if linea and not linea.startswith("#") and "=" in linea:
                    clave, _, valor = linea.partition("=")
                    vars_env[clave.strip()] = valor.strip()
    return vars_env


def guardar_env(vars_dict: dict):
    if not ENV_PATH.exists():
        ejemplo = config.BASE_DIR / ".env.example"
        if ejemplo.exists():
            import shutil
            shutil.copy(ejemplo, ENV_PATH)

    vars_actuales = leer_env()
    vars_actuales.update(vars_dict)

    lineas = []
    for clave, valor in vars_actuales.items():
        lineas.append(f"{clave}={valor}")

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")


with tab1:
    st.markdown(f"#### {t('ia_provider')}")

    vars_env = leer_env()

    with st.form("form_ia"):
        proveedor = st.radio(
            t("llm_provider_label"),
            options=["groq", "openai"],
            index=0 if vars_env.get("LLM_PROVIDER", "groq") == "groq" else 1,
            format_func=lambda x: t("groq_label") if x == "groq" else t("openai_label"),
            horizontal=True,
            key="radio_proveedor"
        )

        if proveedor == "groq":
            modelo = st.selectbox(
                t("groq_model"),
                ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"],
                index=0,
                key="sel_modelo_groq"
            )
            api_key = st.text_input(
                t("groq_key"),
                value=vars_env.get("GROQ_API_KEY", ""),
                type="password",
                help=t("groq_key_help"),
                key="txt_groq_key"
            )
        else:
            modelo = st.selectbox(
                t("openai_model"),
                ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
                index=0,
                key="sel_modelo_openai"
            )
            api_key = st.text_input(
                t("openai_key"),
                value=vars_env.get("OPENAI_API_KEY", ""),
                type="password",
                help=t("openai_key_help"),
                key="txt_openai_key"
            )

        if st.form_submit_button(t("btn_save_ia"), type="primary"):
            nuevas = {
                "LLM_PROVIDER": proveedor,
                "LLM_MODEL": modelo,
            }
            if proveedor == "groq":
                nuevas["GROQ_API_KEY"] = api_key
            else:
                nuevas["OPENAI_API_KEY"] = api_key

            guardar_env(nuevas)
            st.success(t("ia_saved"))

    st.info(t("ia_recommendation"))

with tab2:
    st.markdown(f"#### {t('email_config_title')}")

    with st.form("form_email"):
        vars_env = leer_env()

        resend_key = st.text_input(
            t("resend_key"),
            value=vars_env.get("RESEND_API_KEY", ""),
            type="password",
            help=t("resend_key_help"),
            key="txt_resend_key"
        )

        col1, col2 = st.columns(2)
        with col1:
            email_from = st.text_input(
                t("email_from"),
                value=vars_env.get("EMAIL_FROM", "captacion@oresna.es"),
                help=t("email_from_help"),
                key="txt_email_from"
            )
        with col2:
            email_from_name = st.text_input(
                t("email_from_name"),
                value=vars_env.get("EMAIL_FROM_NAME", "ORESNA Inmobiliaria"),
                key="txt_email_from_name"
            )

        if st.form_submit_button(t("btn_save_email"), type="primary"):
            guardar_env({
                "RESEND_API_KEY": resend_key,
                "EMAIL_FROM": email_from,
                "EMAIL_FROM_NAME": email_from_name,
            })
            st.success(t("email_saved"))

    st.markdown(t("email_spam_instructions"))

with tab3:
    st.markdown(f"#### {t('scraping_title')}")

    with st.form("form_scraping"):
        vars_env = leer_env()

        col1, col2 = st.columns(2)
        with col1:
            delay = st.slider(
                t("delay_label"),
                min_value=1, max_value=10,
                value=int(vars_env.get("SCRAPING_DELAY_SECONDS", "2")),
                help=t("delay_help"),
                key="slider_delay"
            )
            headless = st.checkbox(
                t("headless_label"),
                value=vars_env.get("SCRAPING_HEADLESS", "true").lower() == "true",
                key="chk_headless"
            )
        with col2:
            max_contactos = st.slider(
                t("max_contacts_label"),
                min_value=10, max_value=200,
                value=int(vars_env.get("MAX_CONTACTOS_POR_SESION", "50")),
                key="slider_max_contactos"
            )

        if st.form_submit_button(t("btn_save_scraping"), type="primary"):
            guardar_env({
                "SCRAPING_DELAY_SECONDS": str(delay),
                "SCRAPING_HEADLESS": str(headless).lower(),
                "MAX_CONTACTOS_POR_SESION": str(max_contactos),
            })
            st.success(t("scraping_saved"))

with tab4:
    st.markdown(f"#### {t('company_data_title')}")

    with st.form("form_empresa"):
        vars_env = leer_env()

        col1, col2 = st.columns(2)
        with col1:
            empresa_nombre = st.text_input(
                t("company_name"),
                value=vars_env.get("EMPRESA_NOMBRE", "ORESNA Inmobiliaria"),
                key="txt_empresa_nombre"
            )
            empresa_zona = st.text_input(
                t("company_zone"),
                value=vars_env.get("EMPRESA_ZONA", "Navarra"),
                key="txt_empresa_zona"
            )
        with col2:
            empresa_tel = st.text_input(
                t("company_phone"),
                value=vars_env.get("EMPRESA_TELEFONO", ""),
                key="txt_empresa_tel"
            )
            empresa_web = st.text_input(
                t("company_web"),
                value=vars_env.get("EMPRESA_WEB", ""),
                key="txt_empresa_web"
            )

        if st.form_submit_button(t("btn_save_company"), type="primary"):
            guardar_env({
                "EMPRESA_NOMBRE": empresa_nombre,
                "EMPRESA_ZONA": empresa_zona,
                "EMPRESA_TELEFONO": empresa_tel,
                "EMPRESA_WEB": empresa_web,
            })
            st.success(t("company_saved"))
