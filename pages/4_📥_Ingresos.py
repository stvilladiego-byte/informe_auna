"""Módulo 4 · Ingresos de hemocomponentes (I)."""
from __future__ import annotations

import streamlit as st

from utils.config import COLORS
from utils.data_loader import unit_series
from utils.ui import (inject_css, module_header, ensure_loaded, get_filtered,
                      agg_by, agg_two, searchable_table)
from utils.kpis import kpi_row
from utils import charts
from utils.exporters import excel_download_button, pdf_download_button

st.set_page_config(page_title="Ingresos", page_icon="📥", layout="wide")
inject_css()
module_header("📥", "Ingresos (I)",
              "Hemocomponentes ingresados por banco de sangre y tipo.")

data = ensure_loaded()
df = get_filtered(data, "I")
if df is None or df.empty:
    st.stop()

df = df.copy()
df["_u"] = unit_series(df)
total = int(df["_u"].sum())

kpi_row([
    {"label": "Hemocomponentes ingresados", "icon": "📥", "value": total},
    {"label": "Bancos de sangre", "icon": "🏦",
     "value": int(df["_banco"].nunique()), "color": COLORS["accent"]},
    {"label": "Tipos de hemocomponente", "icon": "🧫",
     "value": int(df["_hemocomponente"].nunique()), "color": COLORS["success"]},
])
st.divider()

por_banco = agg_by(df, "banco", "Ingresos")
por_hemo = agg_by(df, "hemocomponente", "Ingresos")
banco_hemo = agg_two(df, "banco", "hemocomponente", "Ingresos")

tab1, tab2, tab3 = st.tabs(["📊 Barras", "☀️ Sunburst", "🏆 Ranking"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        charts.show_chart(
            charts.bar(por_banco, "Banco", "Ingresos",
                       "Ingresos por banco de sangre", color="Ingresos"),
            "i_banco")
    with c2:
        charts.show_chart(
            charts.bar(por_hemo, "Hemocomponente", "Ingresos",
                       "Ingresos por tipo de hemocomponente", color="Ingresos"),
            "i_hemo")
    charts.show_chart(
        charts.pie(por_hemo, "Hemocomponente", "Ingresos",
                   "Distribución por tipo de hemocomponente"), "i_pie")

with tab2:
    st.markdown("#### ☀️ Sunburst · Banco → Hemocomponente")
    sb = banco_hemo[banco_hemo["Ingresos"] > 0]
    if not sb.empty:
        charts.show_chart(
            charts.sunburst(sb, ["Banco", "Hemocomponente"], "Ingresos",
                            "Ingresos por banco y hemocomponente"), "i_sun")
    else:
        st.info("Sin datos suficientes para el sunburst.")

with tab3:
    st.markdown("#### 🏆 Ranking de bancos de sangre")
    rank = por_banco.reset_index(drop=True)
    rank.index += 1
    st.dataframe(rank, use_container_width=True)
    charts.show_chart(
        charts.bar(por_banco.head(10), "Banco", "Ingresos",
                   "Top 10 bancos por ingresos", color="Ingresos"), "i_top10")

st.divider()
st.markdown("### 📋 Detalle de ingresos")
searchable_table(df, "i",
                 ["_hemocomponente", "_banco", "_abo", "_rh", "_fecha"])

st.divider()
c1, c2, _ = st.columns([1, 1, 2])
with c1:
    excel_download_button({"Por banco": por_banco, "Por hemocomponente": por_hemo,
                           "Banco x Hemocomp": banco_hemo, "Detalle": df}, key="i")
with c2:
    pdf_download_button(
        "Módulo · Ingresos (I)",
        [("Total ingresados", total),
         ("Bancos de sangre", int(df["_banco"].nunique()))],
        {"Ingresos por banco": por_banco,
         "Ingresos por hemocomponente": por_hemo}, key="i")
