"""Módulo 3 · Descartes de Transfusiones (DT)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.config import COLORS
from utils.data_loader import unit_series
from utils.ui import (inject_css, module_header, ensure_loaded, get_filtered,
                      agg_by, agg_two, searchable_table)
from utils.kpis import kpi_row
from utils import charts
from utils.exporters import excel_download_button, pdf_download_button

st.set_page_config(page_title="Descartes", page_icon="🗑️", layout="wide")
inject_css()
module_header("🗑️", "Descartes de Transfusiones (DT)",
              "Hemocomponentes descartados por servicio, tipo y motivo.")

data = ensure_loaded()
df = get_filtered(data, "DT")
if df is None or df.empty:
    st.stop()

df = df.copy()
df["_u"] = unit_series(df)
total = int(df["_u"].sum())

kpi_row([
    {"label": "Hemocomponentes descartados", "icon": "🗑️", "value": total,
     "color": COLORS["danger"]},
    {"label": "Servicios afectados", "icon": "🏥",
     "value": int(df["_servicio"].nunique()), "color": COLORS["accent"]},
    {"label": "Tipos de hemocomponente", "icon": "🧫",
     "value": int(df["_hemocomponente"].nunique()), "color": COLORS["secondary"]},
    {"label": "Motivos de descarte", "icon": "❓",
     "value": int(df["_motivo"].replace("", pd.NA).dropna().nunique()),
     "color": COLORS["warning"]},
])
st.divider()

por_serv = agg_by(df, "servicio", "Descartes")
por_hemo = agg_by(df, "hemocomponente", "Descartes")
serv_hemo = agg_two(df, "servicio", "hemocomponente", "Descartes")

tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Barras", "🌳 Treemap", "🔀 Sankey", "🏆 Ranking"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        charts.show_chart(
            charts.bar(por_serv, "Servicio", "Descartes",
                       "Descartes por servicio", color="Descartes"), "dt_serv")
    with c2:
        charts.show_chart(
            charts.bar(por_hemo, "Hemocomponente", "Descartes",
                       "Descartes por tipo de hemocomponente",
                       color="Descartes"), "dt_hemo")
    charts.show_chart(
        charts.pie(por_hemo, "Hemocomponente", "Descartes",
                   "Distribución por tipo de hemocomponente"), "dt_pie")

with tab2:
    st.markdown("#### 🌳 Treemap · Servicio → Hemocomponente")
    tm = serv_hemo[serv_hemo["Descartes"] > 0]
    if not tm.empty:
        charts.show_chart(
            charts.treemap(tm, ["Servicio", "Hemocomponente"], "Descartes",
                           "Descartes por servicio y hemocomponente"), "dt_tree")
    else:
        st.info("Sin datos suficientes para el treemap.")

with tab3:
    st.markdown("#### 🔀 Sankey · Hemocomponente → Motivo de descarte")
    tmp = df.copy()
    tmp["_motivo"] = tmp["_motivo"].replace("", "SIN MOTIVO")
    flow = tmp.groupby(["_hemocomponente", "_motivo"])["_u"].sum().reset_index()
    flow = flow[flow["_u"] > 0]
    if not flow.empty:
        hemos = list(flow["_hemocomponente"].unique())
        motivos = list(flow["_motivo"].unique())
        labels = hemos + motivos
        idx = {l: i for i, l in enumerate(labels)}
        source = flow["_hemocomponente"].map(idx).tolist()
        target = flow["_motivo"].map(lambda m: idx[m]).tolist()
        charts.show_chart(
            charts.sankey(labels, source, target, flow["_u"].tolist(),
                          "Flujo de descartes: hemocomponente → motivo"),
            "dt_sankey")
    else:
        st.info("Sin datos suficientes para el diagrama Sankey.")

with tab4:
    st.markdown("#### 🏆 Ranking de servicios con más descartes")
    rank = por_serv.reset_index(drop=True)
    rank.index += 1
    st.dataframe(rank, use_container_width=True)
    charts.show_chart(
        charts.bar(por_serv.head(10), "Servicio", "Descartes",
                   "Top 10 servicios con más descartes", color="Descartes"),
        "dt_top10")

st.divider()
st.markdown("### 📋 Detalle de descartes")
searchable_table(df, "dt",
                 ["_paciente", "_servicio", "_hemocomponente", "_banco",
                  "_motivo", "_fecha"])

st.divider()
c1, c2, _ = st.columns([1, 1, 2])
with c1:
    excel_download_button({"Por servicio": por_serv, "Por hemocomponente": por_hemo,
                           "Servicio x Hemocomp": serv_hemo, "Detalle": df}, key="dt")
with c2:
    pdf_download_button(
        "Módulo · Descartes de Transfusiones (DT)",
        [("Total descartados", total),
         ("Servicios afectados", int(df["_servicio"].nunique()))],
        {"Descartes por servicio": por_serv,
         "Descartes por hemocomponente": por_hemo}, key="dt")
