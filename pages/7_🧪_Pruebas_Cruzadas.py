"""Módulo 6 · Pruebas Cruzadas (PC)."""
from __future__ import annotations

import streamlit as st

from utils.config import COLORS
from utils.data_loader import classify_compatibility
from utils.ui import (inject_css, module_header, ensure_loaded, get_filtered,
                      searchable_table)
from utils.kpis import kpi_row
from utils import charts
from utils.exporters import excel_download_button, pdf_download_button

st.set_page_config(page_title="Pruebas Cruzadas", page_icon="🧪", layout="wide")
inject_css()
module_header("🧪", "Pruebas Cruzadas (PC)",
              "Pruebas cruzadas por servicio: compatibles vs. incompatibles.")

data = ensure_loaded()
df = get_filtered(data, "PC")
if df is None or df.empty:
    st.stop()

df = df.copy()
df["Resultado"] = df["_resultado_pc"].map(classify_compatibility)

total = len(df)
compat = int((df["Resultado"] == "Compatible").sum())
incompat = int((df["Resultado"] == "Incompatible").sum())

kpi_row([
    {"label": "Pruebas cruzadas", "icon": "🧪", "value": total},
    {"label": "Compatibles", "icon": "✅", "value": compat,
     "color": COLORS["success"]},
    {"label": "Incompatibles", "icon": "⛔", "value": incompat,
     "color": COLORS["danger"]},
    {"label": "% Incompatibilidad", "icon": "％",
     "value": f"{100 * incompat / total:.1f}%" if total else "0%",
     "color": COLORS["warning"]},
])
st.divider()

# Servicio × Resultado
serv_res = (df.groupby(["_servicio", "Resultado"]).size()
            .reset_index(name="Pruebas")
            .rename(columns={"_servicio": "Servicio"}))
por_serv_total = (df.groupby("_servicio").size().reset_index(name="Pruebas")
                  .rename(columns={"_servicio": "Servicio"})
                  .sort_values("Pruebas", ascending=False))

tab1, tab2, tab3 = st.tabs(["📊 Barras apiladas", "🥧 Circular", "🏆 Ranking"])

with tab1:
    charts.show_chart(
        charts.stacked_bar(serv_res, "Servicio", "Pruebas", "Resultado",
                           "Pruebas cruzadas por servicio (compatibles vs incompatibles)"),
        "pc_stack")

with tab2:
    res_tot = df.groupby("Resultado").size().reset_index(name="Pruebas")
    charts.show_chart(
        charts.pie(res_tot, "Resultado", "Pruebas",
                   "Distribución global de resultados"), "pc_pie")

with tab3:
    st.markdown("#### 🏆 Servicios con más pruebas cruzadas")
    pivot = serv_res.pivot_table(index="Servicio", columns="Resultado",
                                 values="Pruebas", aggfunc="sum", fill_value=0)
    pivot["Total"] = pivot.sum(axis=1)
    if "Incompatible" in pivot.columns:
        pivot["% Incompat."] = (100 * pivot["Incompatible"] / pivot["Total"]).round(1)
    pivot = pivot.sort_values("Total", ascending=False)
    st.dataframe(pivot, use_container_width=True)
    charts.show_chart(
        charts.bar(por_serv_total.head(10), "Servicio", "Pruebas",
                   "Top 10 servicios por pruebas cruzadas", color="Pruebas"),
        "pc_top10")

st.divider()
st.markdown("### 📋 Detalle de pruebas cruzadas")
searchable_table(df, "pc",
                 ["_paciente", "_servicio", "_hemocomponente", "Resultado", "_fecha"])

st.divider()
c1, c2, _ = st.columns([1, 1, 2])
with c1:
    excel_download_button({"Servicio x Resultado": serv_res,
                           "Por servicio": por_serv_total, "Detalle": df}, key="pc")
with c2:
    pdf_download_button(
        "Módulo · Pruebas Cruzadas (PC)",
        [("Total pruebas", total), ("Compatibles", compat),
         ("Incompatibles", incompat)],
        {"Pruebas por servicio": por_serv_total}, key="pc")
