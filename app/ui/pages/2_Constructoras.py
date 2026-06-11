import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import streamlit as st
import pandas as pd

from app.core.db import SessionLocal, Contacto, Campana
from app.core.config import config
from app.core.i18n import t

st.set_page_config(page_title="Constructoras · ORESNA", page_icon="O", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.stApp { background: #0a0e1a !important; color: #f1f5f9 !important; }
[data-testid="stSidebar"] { background: #111827 !important; border-right: 1px solid #2d3748 !important; }
[data-testid="stMetricValue"] { color: #e2c36b !important; font-weight: 800 !important; }
.stButton > button { background: linear-gradient(135deg, #1d4ed8, #3b82f6) !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)


def cargar_constructoras(filtro_estado=None, filtro_localidad=None):
    db = SessionLocal()
    try:
        query = db.query(Contacto).filter(Contacto.modulo == "constructores")
        if filtro_estado and filtro_estado != "Todos":
            query = query.filter(Contacto.estado == filtro_estado)
        if filtro_localidad and filtro_localidad != "Todas":
            query = query.filter(Contacto.localidad.ilike(f"%{filtro_localidad}%"))
        return query.order_by(Contacto.fecha_captura.desc()).all()
    finally:
        db.close()


st.markdown(f"""
<div style="background:linear-gradient(135deg, #1a1a2e 0%, #0f3460 100%); border-radius:16px;
            padding:28px 32px; margin-bottom:28px; border:1px solid #1e3a5f;">
    <h1 style="color:#e2c36b; font-size:1.8rem; font-weight:800; margin:0;">
        {t("constructoras_title")}
    </h1>
    <p style="color:#94a3b8; margin:8px 0 0; font-size:0.95rem;">
        {t("constructoras_desc")}
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown(f"### {t('launch_search')}")

with st.form("form_constructoras"):
    col1, col2, col3 = st.columns(3)

    with col1:
        localidad = st.selectbox(
            t("search_zone"),
            ["Navarra", "Pamplona", "Tudela", "Estella", "Tafalla", "Sanguesa", "Aoiz"],
            key="sel_localidad_const"
        )

    with col2:
        max_contactos = st.slider(
            t("max_contacts"),
            min_value=5, max_value=100, value=30, step=5,
            key="slider_max_const"
        )

    with col3:
        enviar_emails = st.checkbox(
            t("send_emails"),
            value=False,
            key="chk_emails_const",
            help=t("requires_resend")
        )

    nombre_campana = st.text_input(
        t("campaign_name"),
        placeholder=t("campaign_placeholder"),
        key="txt_campana_const"
    )

    col_btn, col_info = st.columns([1, 4])
    with col_btn:
        submitted = st.form_submit_button(
            t("btn_start_ia"),
            use_container_width=True,
            type="primary"
        )
    with col_info:
        if not config.get_llm_api_key():
            st.warning(t("warn_no_llm"))
        elif not config.RESEND_API_KEY and enviar_emails:
            st.warning(t("warn_no_resend"))
        else:
            st.info(f"{t('system_ready')} · LLM: {config.LLM_PROVIDER.upper()} · {config.LLM_MODEL}")

if submitted:
    progreso_msgs = []

    def actualizar_progreso(paso, msg):
        progreso_msgs.append(f"**[{paso}]** {msg}")

    with st.spinner(t("ia_working")):
        try:
            from app.modules.constructores.crew import ejecutar_pipeline_constructoras
            resultados = ejecutar_pipeline_constructoras(
                localidad=localidad,
                enviar_emails=enviar_emails,
                nombre_campana=nombre_campana,
                callback_progreso=actualizar_progreso,
            )

            st.success(f"""
            {t("search_done")}
            - {t("companies_found")}: **{resultados['contactos_encontrados']}**
            - {t("contacts_saved")}: **{resultados['contactos_guardados']}**
            - {t("emails_sent")}: **{resultados['emails_enviados']}**
            """)

            if resultados["errores"]:
                with st.expander(t("errors_during_exec")):
                    for err in resultados["errores"]:
                        st.error(err)

            st.rerun()

        except Exception as e:
            st.error(f"{t('error_generic')}: {str(e)}")
            st.info(t("check_api_keys"))

st.markdown("<br>", unsafe_allow_html=True)
st.divider()

st.markdown(f"### {t('db_constructoras')}")

col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    filtro_estado = st.selectbox(
        t("filter_by_state"),
        ["Todos", "nuevo", "email_enviado", "respondido", "descartado"],
        key="filtro_estado_const"
    )
with col_f2:
    filtro_localidad = st.text_input(t("filter_by_location"), key="filtro_loc_const", placeholder=t("location_placeholder"))
with col_f3:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button(t("btn_refresh_table"), key="btn_refresh_const"):
        st.rerun()

contactos = cargar_constructoras(filtro_estado, filtro_localidad)

if contactos:
    df = pd.DataFrame([{
        t("col_company"): c.empresa,
        t("col_email"): c.email or "-",
        t("col_phone"): c.telefono or "-",
        t("col_web"): c.web or "-",
        t("col_location"): c.localidad or "-",
        t("col_state"): c.estado,
        t("col_date"): c.fecha_captura.strftime("%d/%m/%Y") if c.fecha_captura else "-",
    } for c in contactos])

    st.markdown(f"*{t('n_constructoras').format(n=len(contactos))}*")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=450,
    )

    col_exp, _ = st.columns([1, 5])
    with col_exp:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            t("export_csv"),
            data=csv,
            file_name=f"constructoras_navarra_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="btn_export_const"
        )
else:
    st.info(t("no_constructoras"))
