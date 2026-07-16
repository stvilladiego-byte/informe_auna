"""Módulo · Descartes No Transfundidos (DNT).

Unidades descartadas que no llegaron a transfundirse. A diferencia de DT,
este archivo no trae servicio ni paciente; el análisis se centra en el tipo
de hemocomponente, el banco de sangre de origen y el motivo del descarte.
"""
from __future__ import annotations

import streamlit as st

from utils.config import COLORS
from utils.data_loader import unit_series
from utils.ui import (inject_css, module_header, ensure_loaded, get_filtered,
                      agg_by, agg_two, searchable_table)
from utils.kpis import kpi_row
from utils import charts
from utils.exporters import excel_download_button, pdf_download_button

st.set_page_config(page_title="Descartes No Transfundidos", page_icon="♻️", layout="wide")
inject_css()
module_header("♻️", "Descartes No Transfundidos (DNT)",
              "Unidades descartadas sin transfundir, por hemocomponente, banco y motivo.")

data = ensure_loaded()
df = get_filtered(data, "DNT")
if df is None or df.empty:
    st.stop()

df = df.copy()
df["_u"] = unit_series(df)
df["_motivo"] = df["_motivo"].replace("", "SIN MOTIVO")
total = int(df["_u"].sum())

kpi_row([
    {"label": "Descartados no transfundidos", "icon": "♻️", "value": total,
     "color": COLORS["danger"]},
    {"label": "Tipos de hemocomponente", "icon": "🧫",
     "value": int(df["_hemocomponente"].nunique()), "color": COLORS["accent"]},
    {"label": "Bancos de sangre", "icon": "🏦",
     "value": int(df["_banco"].nunique()), "color": COLORS["secondary"]},
    {"label": "Motivos de descarte", "icon": "❓",
     "value": int(df["_motivo"].nunique()), "color": COLORS["warning"]},
])
st.divider()

por_hemo = agg_by(df, "hemocomponente", "Descartes")
por_banco = agg_by(df, "banco", "Descartes")
por_motivo = (df.groupby("_motivo")["_u"].sum().reset_index()
              .rename(columns={"_motivo": "Motivo", "_u": "Descartes"})
              .sort_values("Descartes", ascending=False))
por_motivo["Descartes"] = por_motivo["Descartes"].astype(int)
banco_hemo = agg_two(df, "banco", "hemocomponente", "Descartes")

tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Barras", "🌳 Treemap", "🔀 Sankey", "🏆 Ranking"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        charts.show_chart(
            charts.bar(por_hemo, "Hemocomponente", "Descartes",
                       "Descartes por tipo de hemocomponente", color="Descartes"),
            "dnt_hemo")
    with c2:
        charts.show_chart(
            charts.bar(por_motivo, "Motivo", "Descartes",
                       "Descartes por motivo", color="Descartes"), "dnt_motivo")
    charts.show_chart(
        charts.pie(por_motivo, "Motivo", "Descartes",
                   "Distribución por motivo de descarte"), "dnt_pie")

with tab2:
    st.markdown("#### 🌳 Treemap · Banco → Hemocomponente")
    tm = banco_hemo[banco_hemo["Descartes"] > 0]
    if not tm.empty:
        charts.show_chart(
            charts.treemap(tm, ["Banco", "Hemocomponente"], "Descartes",
                           "Descartes por banco y hemocomponente"), "dnt_tree")
    else:
        st.info("Sin datos suficientes para el treemap.")

with tab3:
    st.markdown("#### 🔀 Sankey · Hemocomponente → Motivo de descarte")
    flow = df.groupby(["_hemocomponente", "_motivo"])["_u"].sum().reset_index()
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
            "dnt_sankey")
    else:
        st.info("Sin datos suficientes para el diagrama Sankey.")

with tab4:
    st.markdown("#### 🏆 Ranking por banco de sangre")
    rank = por_banco.reset_index(drop=True)
    rank.index += 1
    st.dataframe(rank, use_container_width=True)
    charts.show_chart(
        charts.bar(por_banco.head(10), "Banco", "Descartes",
                   "Top bancos con más descartes no transfundidos",
                   color="Descartes"), "dnt_top")

st.divider()
st.markdown("### 📋 Detalle de descartes no transfundidos")
searchable_table(df, "dnt",
                 ["_hemocomponente", "_banco", "_motivo", "_fecha"])

st.divider()
c1, c2, _ = st.columns([1, 1, 2])
with c1:
    excel_download_button({"Por hemocomponente": por_hemo, "Por motivo": por_motivo,
                           "Por banco": por_banco, "Detalle": df}, key="dnt")
with c2:
    pdf_download_button(
        "Módulo · Descartes No Transfundidos (DNT)",
        [("Total descartados no transfundidos", total),
         ("Tipos de hemocomponente", int(df["_hemocomponente"].nunique())),
         ("Motivos de descarte", int(df["_motivo"].nunique()))],
        {"Descartes por hemocomponente": por_hemo,
         "Descartes por motivo": por_motivo}, key="dnt")
