"""Módulo 5 · Transfusiones (T)."""
from __future__ import annotations

import streamlit as st

from utils.config import COLORS
from utils.data_loader import unit_series
from utils.ui import (inject_css, module_header, ensure_loaded, get_filtered,
                      agg_by, agg_two, searchable_table)
from utils.kpis import kpi_row
from utils import charts
from utils.exporters import excel_download_button, pdf_download_button

st.set_page_config(page_title="Transfusiones", page_icon="💉", layout="wide")
inject_css()
module_header("💉", "Transfusiones (T)",
              "Hemocomponentes transfundidos por servicio.")

data = ensure_loaded()
df = get_filtered(data, "T")
if df is None or df.empty:
    st.stop()

df = df.copy()
df["_u"] = unit_series(df)
total = int(df["_u"].sum())

kpi_row([
    {"label": "Hemocomponentes transfundidos", "icon": "💉", "value": total,
     "color": COLORS["success"]},
    {"label": "Servicios", "icon": "🏥",
     "value": int(df["_servicio"].nunique()), "color": COLORS["accent"]},
    {"label": "Tipos de hemocomponente", "icon": "🧫",
     "value": int(df["_hemocomponente"].nunique()), "color": COLORS["secondary"]},
])
st.divider()

por_serv = agg_by(df, "servicio", "Transfundidos")
por_hemo = agg_by(df, "hemocomponente", "Transfundidos")
serv_hemo = agg_two(df, "servicio", "hemocomponente", "Transfundidos")

tab1, tab2, tab3 = st.tabs(["📊 Barras / Circular", "🔥 Heatmap", "🏆 Ranking"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        charts.show_chart(
            charts.bar(por_serv, "Servicio", "Transfundidos",
                       "Hemocomponentes transfundidos por servicio",
                       color="Transfundidos"), "t_serv")
    with c2:
        charts.show_chart(
            charts.pie(por_hemo, "Hemocomponente", "Transfundidos",
                       "Distribución por tipo de hemocomponente"), "t_pie")

with tab2:
    st.markdown("#### 🔥 Servicio × Hemocomponente")
    if not serv_hemo.empty:
        matrix = serv_hemo.pivot_table(index="Servicio", columns="Hemocomponente",
                                       values="Transfundidos", aggfunc="sum",
                                       fill_value=0)
        charts.show_chart(
            charts.heatmap(matrix, "Unidades transfundidas por servicio y hemocomponente",
                           "Hemocomponente", "Servicio"), "t_heat")
    else:
        st.info("Sin datos suficientes para el heatmap.")

with tab3:
    st.markdown("#### 🏆 Ranking de servicios")
    rank = por_serv.reset_index(drop=True)
    rank.index += 1
    st.dataframe(rank, use_container_width=True)
    charts.show_chart(
        charts.bar(por_serv.head(10), "Servicio", "Transfundidos",
                   "Top 10 servicios por transfusiones", color="Transfundidos"),
        "t_top10")

st.divider()
st.markdown("### 📋 Detalle de transfusiones")
searchable_table(df, "t",
                 ["_paciente", "_servicio", "_hemocomponente", "_banco",
                  "_resultado_pc", "_rai"])

st.divider()
c1, c2, _ = st.columns([1, 1, 2])
with c1:
    excel_download_button({"Por servicio": por_serv, "Por hemocomponente": por_hemo,
                           "Detalle": df}, key="t")
with c2:
    pdf_download_button(
        "Módulo · Transfusiones (T)",
        [("Total transfundidos", total),
         ("Servicios", int(df["_servicio"].nunique()))],
        {"Transfusiones por servicio": por_serv}, key="t")
