import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import streamlit as st
import pandas as pd

from app.core.db import SessionLocal, EmailLog, Campana, Contacto
from app.core.i18n import t
from app.ui.components.theme import inject_theme_css, inject_watermark, render_theme_toggle, get_theme

st.set_page_config(page_title="Correos · ORESNA", page_icon="🏠", layout="wide")

inject_theme_css()
inject_watermark()
render_theme_toggle(sidebar=True)

theme = get_theme()
gold = "#8a6a18" if theme == "light" else "#e2c36b"
muted = "#64748b"


def cargar_campanas():
    db = SessionLocal()
    try:
        return db.query(Campana).order_by(Campana.fecha_inicio.desc()).all()
    finally:
        db.close()


def cargar_emails_campana(campana_id: int):
    db = SessionLocal()
    try:
        return (
            db.query(EmailLog, Contacto)
            .join(Contacto, EmailLog.contacto_id == Contacto.id)
            .filter(EmailLog.campana_id == campana_id)
            .order_by(EmailLog.fecha_envio.desc())
            .all()
        )
    finally:
        db.close()


def cargar_todos_emails():
    db = SessionLocal()
    try:
        return (
            db.query(EmailLog, Contacto)
            .join(Contacto, EmailLog.contacto_id == Contacto.id)
            .order_by(EmailLog.fecha_envio.desc())
            .limit(100)
            .all()
        )
    finally:
        db.close()


st.markdown(f"""
<h1 style="color:{gold}; font-weight:800; font-size:2rem; margin-bottom:4px;">
    {t("emails_title")}
</h1>
<p style="color:{muted}; font-size:0.95rem; margin-bottom:28px;">
    {t("emails_subtitle")}
</p>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs([t("tab_campaigns"), t("tab_history")])

with tab1:
    campanas = cargar_campanas()

    if not campanas:
        st.info(t("no_campaigns"))
    else:
        total_enviados = sum(c.total_enviados for c in campanas)
        total_respondidos = sum(c.total_respondidos for c in campanas)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(t("metric_total_campaigns"), len(campanas))
        with col2:
            st.metric(t("metric_sent"), total_enviados)
        with col3:
            st.metric(t("metric_responses"), total_respondidos)
        with col4:
            tasa = round((total_respondidos / total_enviados * 100), 1) if total_enviados > 0 else 0
            st.metric(t("metric_response_rate"), f"{tasa}%")

        st.markdown("<br>", unsafe_allow_html=True)

        df_camp = pd.DataFrame([{
            t("tab_campaigns"): c.nombre,
            "Modulo": c.modulo.capitalize(),
            t("col_date"): c.fecha_inicio.strftime("%d/%m/%Y %H:%M") if c.fecha_inicio else "-",
            t("metric_sent"): c.total_enviados,
            t("metric_responses"): c.total_respondidos,
            "Tasa": f"{c.tasa_apertura}%",
            "Activa": "Si" if c.activa else "No",
        } for c in campanas])

        st.dataframe(df_camp, use_container_width=True, hide_index=True)

        st.markdown(f"### {t('campaign_detail')}")
        nombres_campanas = {c.nombre: c.id for c in campanas}
        campana_sel = st.selectbox(
            t("select_campaign"),
            options=list(nombres_campanas.keys()),
            key="sel_campana"
        )

        if campana_sel:
            emails_campana = cargar_emails_campana(nombres_campanas[campana_sel])
            if emails_campana:
                df_emails = pd.DataFrame([{
                    t("col_company"): contacto.empresa,
                    t("col_email"): contacto.email,
                    t("email_subject"): email.asunto[:60] + "..." if len(email.asunto) > 60 else email.asunto,
                    t("col_state"): email.estado,
                    t("col_date"): email.fecha_envio.strftime("%d/%m %H:%M") if email.fecha_envio else "-",
                } for email, contacto in emails_campana])

                st.dataframe(df_emails, use_container_width=True, hide_index=True)

                if st.button(t("preview_btn"), key="btn_preview"):
                    email_preview, _ = emails_campana[0]
                    with st.expander(t("email_preview"), expanded=True):
                        st.markdown(f"**{t('email_subject')}:** {email_preview.asunto}")
                        st.markdown("---")
                        st.components.v1.html(email_preview.cuerpo_html, height=500, scrolling=True)


with tab2:
    todos_emails = cargar_todos_emails()

    if not todos_emails:
        st.info(t("no_emails"))
    else:
        st.markdown(f"*{t('showing_last').format(n=len(todos_emails))}*")

        df_all = pd.DataFrame([{
            t("col_company"): contacto.empresa,
            t("col_email"): contacto.email,
            t("email_subject"): email.asunto[:50] + "..." if len(email.asunto) > 50 else email.asunto,
            t("col_state"): email.estado,
            "ID Resend": email.resend_id or "-",
            t("col_date"): email.fecha_envio.strftime("%d/%m/%Y %H:%M") if email.fecha_envio else "-",
            "Error": email.error_msg[:40] if email.error_msg else "-",
        } for email, contacto in todos_emails])

        estados_disponibles = ["Todos"] + list(set(email.estado for email, _ in todos_emails))
        filtro_estado = st.selectbox(t("filter_by_state2"), estados_disponibles, key="filtro_email_estado")

        if filtro_estado != "Todos":
            df_filtrado = df_all[df_all[t("col_state")] == filtro_estado]
        else:
            df_filtrado = df_all

        st.dataframe(df_filtrado, use_container_width=True, hide_index=True, height=450)

        csv = df_filtrado.to_csv(index=False).encode("utf-8")
        st.download_button(
            t("export_history_csv"),
            data=csv,
            file_name=f"historial_emails_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="btn_export_emails"
        )
