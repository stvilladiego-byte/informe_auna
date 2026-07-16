"""Módulo 8 · Solicitudes de Unidades (SU)."""
from __future__ import annotations

import streamlit as st

from utils.config import COLORS
from utils.data_loader import unit_series
from utils.ui import (inject_css, module_header, ensure_loaded, get_filtered,
                      agg_by, agg_two, searchable_table)
from utils.kpis import kpi_row
from utils import charts
from utils.exporters import excel_download_button, pdf_download_button

st.set_page_config(page_title="Solicitudes de Unidades", page_icon="📋", layout="wide")
inject_css()
module_header("📋", "Solicitudes de Unidades (SU)",
              "Hemocomponentes solicitados por servicio y tipo.")

data = ensure_loaded()
df = get_filtered(data, "SU")
if df is None or df.empty:
    st.stop()

df = df.copy()
df["_u"] = unit_series(df)
total = int(df["_u"].sum())

kpi_row([
    {"label": "Unidades solicitadas", "icon": "📋", "value": total},
    {"label": "Servicios solicitantes", "icon": "🏥",
     "value": int(df["_servicio"].nunique()), "color": COLORS["accent"]},
    {"label": "Tipos de hemocomponente", "icon": "🧫",
     "value": int(df["_hemocomponente"].nunique()), "color": COLORS["success"]},
    {"label": "Solicitudes (registros)", "icon": "🗂️",
     "value": int(len(df)), "color": COLORS["secondary"]},
])
st.divider()

por_serv = agg_by(df, "servicio", "Solicitado")
por_hemo = agg_by(df, "hemocomponente", "Solicitado")
serv_hemo = agg_two(df, "servicio", "hemocomponente", "Solicitado")

tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Barras", "🌳 Treemap", "☀️ Sunburst", "🏆 Ranking"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        charts.show_chart(
            charts.bar(por_serv, "Servicio", "Solicitado",
                       "Unidades solicitadas por servicio", color="Solicitado"),
            "su_serv")
    with c2:
        charts.show_chart(
            charts.bar(por_hemo, "Hemocomponente", "Solicitado",
                       "Unidades solicitadas por tipo", color="Solicitado"),
            "su_hemo")

with tab2:
    tm = serv_hemo[serv_hemo["Solicitado"] > 0]
    if not tm.empty:
        charts.show_chart(
            charts.treemap(tm, ["Servicio", "Hemocomponente"], "Solicitado",
                           "Solicitudes por servicio y hemocomponente"), "su_tree")
    else:
        st.info("Sin datos suficientes para el treemap.")

with tab3:
    sb = serv_hemo[serv_hemo["Solicitado"] > 0]
    if not sb.empty:
        charts.show_chart(
            charts.sunburst(sb, ["Hemocomponente", "Servicio"], "Solicitado",
                            "Solicitudes por hemocomponente y servicio"), "su_sun")
    else:
        st.info("Sin datos suficientes para el sunburst.")

with tab4:
    st.markdown("#### 🏆 Ranking de servicios solicitantes")
    rank = por_serv.reset_index(drop=True)
    rank.index += 1
    st.dataframe(rank, use_container_width=True)
    charts.show_chart(
        charts.bar(por_serv.head(10), "Servicio", "Solicitado",
                   "Top 10 servicios solicitantes", color="Solicitado"), "su_top10")

st.divider()
st.markdown("### 📋 Tabla dinámica de solicitudes")
searchable_table(df, "su",
                 ["_servicio", "_hemocomponente", "_abo", "_rh", "_fecha"])

st.divider()
c1, c2, _ = st.columns([1, 1, 2])
with c1:
    excel_download_button({"Por servicio": por_serv, "Por hemocomponente": por_hemo,
                           "Servicio x Hemocomp": serv_hemo, "Detalle": df}, key="su")
with c2:
    pdf_download_button(
        "Módulo · Solicitudes de Unidades (SU)",
        [("Unidades solicitadas", total),
         ("Servicios", int(df["_servicio"].nunique()))],
        {"Solicitudes por servicio": por_serv,
         "Solicitudes por hemocomponente": por_hemo}, key="su")
