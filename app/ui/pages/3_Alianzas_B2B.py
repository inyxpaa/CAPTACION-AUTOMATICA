import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import streamlit as st
import pandas as pd

from app.core.db import SessionLocal, Contacto
from app.core.config import config
from app.core.i18n import t
from app.ui.components.theme import inject_theme_css, inject_watermark, render_theme_toggle, get_theme

st.set_page_config(page_title="Alianzas B2B · ORESNA", page_icon="🏠", layout="wide")

inject_theme_css()
inject_watermark()
render_theme_toggle(sidebar=True)

theme = get_theme()
muted  = "#64748b"
bg2s   = "#f0fdf4" if theme == "light" else "#0d3b2e"
bg2e   = "#dcfce7" if theme == "light" else "#1a5c45"
border2 = "#86efac" if theme == "light" else "#1e5c3a"
card_title = "#065f46" if theme == "light" else "#a8e6cf"
card_text  = "#047857" if theme == "light" else "#7ec8a0"
card_bg    = "#f0fdf4" if theme == "light" else "#111827"
card_border = "#bbf7d0" if theme == "light" else "#2d3748"

TIPOS_EMPRESA = {
    "reformas": "Reformas",
    "mudanzas": "Mudanzas",
    "gestoria": "Gestion y Contabilidad",
    "abogados": "Abogados",
}


def cargar_alianzas(filtro_tipo=None, filtro_estado=None):
    db = SessionLocal()
    try:
        query = db.query(Contacto).filter(Contacto.modulo == "alianzas")
        if filtro_tipo and filtro_tipo != "Todos":
            query = query.filter(Contacto.tipo_empresa.ilike(f"%{filtro_tipo}%"))
        if filtro_estado and filtro_estado != "Todos":
            query = query.filter(Contacto.estado == filtro_estado)
        return query.order_by(Contacto.fecha_captura.desc()).all()
    finally:
        db.close()


st.markdown(f"""
<div style="background:linear-gradient(135deg, {bg2s} 0%, {bg2e} 100%); border-radius:16px;
            padding:28px 32px; margin-bottom:28px; border:1px solid {border2};">
    <h1 style="color:{card_title}; font-size:1.8rem; font-weight:800; margin:0;">
        {t("alianzas_title")}
    </h1>
    <p style="color:{card_text}; margin:8px 0 0; font-size:0.95rem;">
        {t("alianzas_desc")}
    </p>
</div>
""", unsafe_allow_html=True)

with st.expander(t("synergy_expander")):
    cols = st.columns(2)
    tipos_lista = list(TIPOS_EMPRESA.items())
    for i, (tipo, desc) in enumerate(tipos_lista):
        col = cols[i % 2]
        with col:
            propuesta = t("synergy_proposal").format(tipo=desc.lower())
            st.markdown(f"""
            <div style="background:{card_bg}; border:1px solid {card_border}; border-radius:10px;
                        padding:16px; margin-bottom:12px;">
                <p style="color:{card_title}; font-weight:600; margin:0 0 6px;">{desc}</p>
                <p style="color:{muted}; font-size:0.85rem; margin:0;">{propuesta}</p>
            </div>
            """, unsafe_allow_html=True)

st.markdown(f"### {t('launch_alliance_search')}")

with st.form("form_alianzas"):
    col1, col2 = st.columns(2)

    with col1:
        tipos_seleccionados = st.multiselect(
            t("company_types"),
            options=list(TIPOS_EMPRESA.keys()),
            default=["reformas", "mudanzas"],
            format_func=lambda x: TIPOS_EMPRESA[x],
            key="ms_tipos_alianzas"
        )

        localidad = st.selectbox(
            t("alliance_search_zone"),
            ["Navarra", "Pamplona", "Tudela", "Estella", "Tafalla"],
            key="sel_localidad_alianzas"
        )

    with col2:
        enviar_emails = st.checkbox(
            t("send_proposals"),
            value=False,
            key="chk_emails_alianzas",
            help=t("requires_resend2")
        )

        nombre_campana = st.text_input(
            t("alliance_campaign"),
            placeholder=t("alliance_campaign_placeholder"),
            key="txt_campana_alianzas"
        )

    submitted = st.form_submit_button(
        t("btn_start_alliance"),
        use_container_width=True,
        type="primary"
    )

if submitted:
    if not tipos_seleccionados:
        st.warning(t("warn_select_type"))
    else:
        with st.spinner(f"{t('searching_alliance')} ({', '.join(tipos_seleccionados)})..."):
            try:
                from app.modules.alianzas.crew import ejecutar_pipeline_alianzas
                resultados = ejecutar_pipeline_alianzas(
                    tipos=tipos_seleccionados,
                    localidad=localidad,
                    enviar_emails=enviar_emails,
                    nombre_campana=nombre_campana,
                )

                st.success(f"""
                {t("alliance_done")}
                - {t("companies_found")}: **{resultados['contactos_encontrados']}**
                - {t("new_saved")}: **{resultados['contactos_guardados']}**
                - {t("proposals_sent")}: **{resultados['emails_enviados']}**
                """)

                if resultados.get("por_tipo"):
                    st.markdown(f"**{t('by_type')}:**")
                    cols = st.columns(len(resultados["por_tipo"]))
                    for i, (tipo, count) in enumerate(resultados["por_tipo"].items()):
                        with cols[i]:
                            st.metric(tipo.capitalize(), count)

                st.rerun()
            except Exception as e:
                st.error(f"{t('error_generic')}: {str(e)}")

st.divider()

st.markdown(f"### {t('db_alianzas')}")

col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    filtro_tipo = st.selectbox(
        t("company_type_filter"),
        ["Todos", "Reformas", "Mudanzas", "Gestoria", "Abogados"],
        key="filtro_tipo_alianzas"
    )
with col_f2:
    filtro_estado = st.selectbox(
        t("state_filter"),
        ["Todos", "nuevo", "email_enviado", "respondido", "descartado"],
        key="filtro_estado_alianzas"
    )
with col_f3:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button(t("btn_refresh_table2"), key="btn_refresh_alianzas"):
        st.rerun()

contactos = cargar_alianzas(filtro_tipo, filtro_estado)

if contactos:
    df = pd.DataFrame([{
        t("col_company"): c.empresa,
        t("col_type"): c.tipo_empresa or "-",
        t("col_phone"): c.telefono or "-",
        t("col_email"): c.email or "-",
        t("col_web"): c.web or "-",
        t("col_location"): c.localidad or "-",
        t("col_state"): c.estado,
        t("col_date"): c.fecha_captura.strftime("%d/%m/%Y") if c.fecha_captura else "-",
    } for c in contactos])

    st.markdown(f"*{t('n_alianzas').format(n=len(contactos))}*")
    st.dataframe(df, use_container_width=True, hide_index=True, height=450)

    col_exp, _ = st.columns([1, 5])
    with col_exp:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            t("export_csv"),
            data=csv,
            file_name=f"alianzas_b2b_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="btn_export_alianzas"
        )
else:
    st.info(t("no_alianzas"))
