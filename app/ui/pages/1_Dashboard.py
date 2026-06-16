import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import streamlit as st
import pandas as pd
from datetime import datetime

from app.core.db import SessionLocal, Contacto, Campana, EmailLog
from app.core.i18n import t, get_lang
from app.ui.components.theme import inject_theme_css, inject_watermark, render_theme_toggle, get_theme

st.set_page_config(page_title="Panel de Control · ORESNA", page_icon="🏠", layout="wide")

inject_theme_css()
inject_watermark()
render_theme_toggle(sidebar=True)

theme = get_theme()
gold = "#8a6a18" if theme == "light" else "#e2c36b"
muted = "#64748b"


def cargar_stats() -> dict:
    db = SessionLocal()
    try:
        total_contactos = db.query(Contacto).count()
        constructoras = db.query(Contacto).filter(Contacto.modulo == "constructores").count()
        alianzas = db.query(Contacto).filter(Contacto.modulo == "alianzas").count()
        emails_enviados = db.query(EmailLog).filter(EmailLog.estado == "enviado").count()
        nuevos_hoy = db.query(Contacto).filter(
            Contacto.fecha_captura >= datetime.utcnow().replace(hour=0, minute=0, second=0)
        ).count()
        campanas_activas = db.query(Campana).filter(Campana.activa == True).count()
        total_campanas = db.query(Campana).count()

        ultimos = db.query(Contacto).order_by(Contacto.fecha_captura.desc()).limit(10).all()

        from sqlalchemy import func
        por_localidad = (
            db.query(Contacto.localidad, func.count(Contacto.id).label("total"))
            .group_by(Contacto.localidad)
            .order_by(func.count(Contacto.id).desc())
            .limit(5)
            .all()
        )

        return {
            "total_contactos": total_contactos,
            "constructoras": constructoras,
            "alianzas": alianzas,
            "emails_enviados": emails_enviados,
            "nuevos_hoy": nuevos_hoy,
            "campanas_activas": campanas_activas,
            "total_campanas": total_campanas,
            "ultimos_contactos": [
                {
                    "empresa": c.empresa,
                    "tipo": c.tipo_empresa or c.modulo,
                    "localidad": c.localidad,
                    "estado": c.estado,
                    "fecha": c.fecha_captura.strftime("%d/%m/%Y") if c.fecha_captura else "-",
                }
                for c in ultimos
            ],
            "por_localidad": [{"Localidad": row[0] or "N/D", "Contactos": row[1]} for row in por_localidad],
        }
    finally:
        db.close()


st.markdown(f"""
<h1 style="color:{gold}; font-weight:800; font-size:2rem; margin-bottom:4px;">
    {t("dashboard_title")}
</h1>
<p style="color:{muted}; font-size:0.95rem; margin-bottom:28px;">
    {t("dashboard_subtitle")}
</p>
""", unsafe_allow_html=True)

col_ref, _ = st.columns([1, 6])
with col_ref:
    if st.button(t("btn_refresh"), key="btn_refresh"):
        st.rerun()

stats = cargar_stats()

st.markdown(f"### {t('metrics_title')}")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(t("metric_total"), stats["total_contactos"], delta=f"+{stats['nuevos_hoy']} hoy")
with col2:
    st.metric(t("metric_constructoras"), stats["constructoras"])
with col3:
    st.metric(t("metric_alianzas"), stats["alianzas"])
with col4:
    st.metric(t("metric_emails"), stats["emails_enviados"])
with col5:
    st.metric(t("metric_campanas"), stats["total_campanas"])

st.markdown("<br>", unsafe_allow_html=True)

col_left, col_right = st.columns([3, 2], gap="large")

with col_left:
    st.markdown(f"### {t('recent_contacts')}")
    if stats["ultimos_contactos"]:
        df_ultimos = pd.DataFrame(stats["ultimos_contactos"])
        st.dataframe(
            df_ultimos,
            use_container_width=True,
            hide_index=True,
            column_config={
                "empresa": st.column_config.TextColumn(t("col_company"), width="large"),
                "tipo": st.column_config.TextColumn(t("col_type"), width="medium"),
                "localidad": st.column_config.TextColumn(t("col_location")),
                "estado": st.column_config.TextColumn(t("col_state")),
                "fecha": st.column_config.TextColumn(t("col_date")),
            }
        )
    else:
        st.info(t("no_contacts_yet"))

with col_right:
    st.markdown(f"### {t('by_location')}")
    if stats["por_localidad"]:
        df_loc = pd.DataFrame(stats["por_localidad"])
        st.bar_chart(df_loc.set_index("Localidad"))
    else:
        st.info(t("no_location_data"))

    st.markdown("<br>", unsafe_allow_html=True)

    if stats["total_contactos"] > 0:
        st.markdown(f"### {t('by_module')}")
        df_modulo = pd.DataFrame({
            "Modulo": [t("metric_constructoras"), t("metric_alianzas")],
            "Contactos": [stats["constructoras"], stats["alianzas"]]
        })
        st.bar_chart(df_modulo.set_index("Modulo"))
