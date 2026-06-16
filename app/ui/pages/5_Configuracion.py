import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import streamlit as st
from pathlib import Path

from app.core.config import config
from app.core.i18n import t
from app.ui.components.theme import inject_theme_css, inject_watermark, render_theme_toggle, get_theme

st.set_page_config(page_title="Ajustes · ORESNA", page_icon="🏠", layout="wide")

inject_theme_css()
inject_watermark()
render_theme_toggle(sidebar=True)

theme = get_theme()
gold  = "#8a6a18" if theme == "light" else "#e2c36b"
muted = "#64748b"

st.markdown(f"""
<h1 style="color:{gold}; font-weight:800; font-size:2rem; margin-bottom:4px;">
    {t("config_title")}
</h1>
<p style="color:{muted}; font-size:0.95rem; margin-bottom:28px;">
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

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    t("tab_ia"), t("tab_email"), t("tab_scraping"), t("tab_company"), "🛠️ Desarrollador"
])

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

    st.info("""
**¿Qué API necesito para la IA?**

Elige **una** de estas dos opciones:

- 🟢 **Groq** *(recomendado — completamente gratuito)*
  1. Ve a [console.groq.com](https://console.groq.com) → Crear cuenta gratis
  2. En el menú lateral: **API Keys** → **Create API Key**
  3. Copia la clave (empieza por `gsk_...`) y pégala abajo

- 🔵 **OpenAI** *(de pago, ~€0,15 por 1.000 emails generados)*
  1. Ve a [platform.openai.com](https://platform.openai.com) → Crear cuenta
  2. Menú: **API Keys** → **Create new secret key**
  3. Copia la clave (empieza por `sk-...`) y pégala abajo
    """)

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

with tab2:
    st.markdown(f"#### {t('email_config_title')}")

    st.info("""
**¿Cómo configurar el envío de emails?**

El sistema usa **Resend** para enviar emails profesionales. Es gratuito hasta 3.000 emails/mes.

**Paso 1 — Crear cuenta en Resend**
1. Ve a [resend.com](https://resend.com) → Sign Up (gratis)
2. Verifica tu email

**Paso 2 — Verificar tu dominio de envío**
1. En Resend: **Domains** → **Add Domain** → escribe `oresna.es`
2. Resend te dará unos registros DNS (TXT, MX...)
3. Ve al panel de tu hosting/dominio y añade esos registros
4. En Resend pulsa **Verify** — tardará unos minutos

**Paso 3 — Obtener la API Key**
1. En Resend: **API Keys** → **Create API Key**
2. Copia la clave (empieza por `re_...`) y pégala abajo

> ⚠️ Si no tienes acceso al dominio `oresna.es`, contacta con quien gestiona el hosting.
    """)

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

with tab5:
    st.markdown("#### Información del Desarrollador")
    st.markdown("<br>", unsafe_allow_html=True)

    surf  = "#f1f5f9" if theme == "light" else "#111827"
    bord  = "#e2e8f0" if theme == "light" else "#2d3748"
    body  = "#334155" if theme == "light" else "#94a3b8"

    col_dev, col_ver = st.columns([3, 1])
    with col_dev:
        st.markdown(f"""
<div style="background:{surf}; border:1px solid {bord};
            border-radius:12px; padding:28px 32px;">
    <p style="font-size:1.15rem; font-weight:700; margin:0 0 2px; color:{gold}; letter-spacing:-0.3px;">
        Iñigo Del Mazo Monreal
    </p>
    <p style="color:{muted}; margin:0 0 18px; font-size:0.85rem; letter-spacing:0.3px; text-transform:uppercase;">
        Desarrollador de software
    </p>
    <p style="color:{body}; font-size:0.9rem; line-height:1.65; margin:0;">
        Desarrollo e implantación de herramientas digitales a medida para empresas.
        Esta aplicación fue construida específicamente para
        <strong style="color:{gold};">ORESNA Inmobiliaria</strong> (Navarra, España)
        con el objetivo de automatizar la captación comercial B2B mediante Inteligencia Artificial.
    </p>
</div>
        """, unsafe_allow_html=True)

    with col_ver:
        st.markdown(f"""
<div style="background:{surf}; border:1px solid {bord};
            border-radius:12px; padding:24px; text-align:center; height:100%;">
    <p style="color:{muted}; font-size:0.7rem; margin:0 0 6px; text-transform:uppercase; letter-spacing:1.5px;">Versión</p>
    <p style="font-size:1.8rem; font-weight:800; color:{gold}; margin:0; letter-spacing:-1px;">1.0.0</p>
    <p style="color:{muted}; font-size:0.72rem; margin:10px 0 0; letter-spacing:0.5px;">ORESNA CAPTADOR</p>
    <p style="color:{muted}; font-size:0.7rem; margin:4px 0 0;">2026</p>
</div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### Resumen de componentes")
    st.markdown("""
| Componente | Tecnología | Propósito |
|---|---|---|
| Panel visual | Streamlit | Interfaz de usuario |
| Agentes IA | CrewAI + Groq / OpenAI | Búsqueda y redacción |
| Scraping | Playwright | Rastreo web |
| Base de datos | SQLite | Almacenamiento local |
| Emails | Resend API | Envío de correos |
    """)
