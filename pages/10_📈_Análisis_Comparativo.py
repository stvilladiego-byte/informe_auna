"""Módulo 9 · Análisis comparativo y funciones avanzadas."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.config import COLORS, DATASETS
from utils.data_loader import unit_series
from utils.ui import inject_css, module_header, ensure_loaded
from utils.filters import render_sidebar_filters, filter_all
from utils.kpis import kpi_row
from utils import charts
from utils.exporters import excel_download_button

st.set_page_config(page_title="Análisis Comparativo", page_icon="📈", layout="wide")
inject_css()
module_header("📈", "Análisis Comparativo",
              "Comparación entre servicios, rankings y pacientes destacados.")

data = ensure_loaded()
filtros = render_sidebar_filters(data)
fdata = filter_all(data, filtros)


def by_service(df, name):
    if df is None or "_servicio" not in df.columns:
        return pd.DataFrame(columns=["Servicio", name])
    tmp = df.copy()
    tmp["_u"] = unit_series(tmp)
    return (tmp.groupby("_servicio")["_u"].sum().reset_index()
            .rename(columns={"_servicio": "Servicio", "_u": name}))


# ---------------------------------------------------------------------------
# Comparación entre servicios (matriz consolidada)
# ---------------------------------------------------------------------------
st.markdown("### 🏥 Comparación entre servicios")

frames = [
    by_service(fdata.get("T"), "Transfundidos"),
    by_service(fdata.get("DT"), "Descartados"),
    by_service(fdata.get("SU"), "Solicitados"),
    by_service(fdata.get("PC"), "Pruebas cruzadas"),
]
comp = None
for f in frames:
    if not f.empty:
        comp = f if comp is None else comp.merge(f, on="Servicio", how="outer")
# pacientes atendidos/transfundidos (únicos)
for key, col in [("PA", "Atendidos"), ("PT", "Transf. (pac.)")]:
    df = fdata.get(key)
    if df is not None and "_paciente_norm" in df.columns:
        g = (df[df["_paciente_norm"] != ""]
             .groupby("_servicio")["_paciente_norm"].nunique()
             .reset_index().rename(columns={"_servicio": "Servicio",
                                             "_paciente_norm": col}))
        comp = g if comp is None else comp.merge(g, on="Servicio", how="outer")

if comp is not None and not comp.empty:
    comp = comp.fillna(0)
    num_cols = [c for c in comp.columns if c != "Servicio"]
    comp[num_cols] = comp[num_cols].astype(int)
    comp["Total"] = comp[num_cols].sum(axis=1)
    comp = comp.sort_values("Total", ascending=False)
    st.dataframe(comp, use_container_width=True, hide_index=True)

    # Barras agrupadas comparativas (top servicios)
    melt = comp.head(10).melt(id_vars="Servicio", value_vars=num_cols,
                              var_name="Métrica", value_name="Valor")
    charts.show_chart(
        charts.bar(melt, "Servicio", "Valor", "Comparativa por servicio (Top 10)",
                   color="Métrica"), "cmp_bar")
else:
    st.info("Carga los archivos T, DT, SU, PC, PA o PT para comparar servicios.")

st.divider()

# ---------------------------------------------------------------------------
# Top 10 servicios y hemocomponentes
# ---------------------------------------------------------------------------
c1, c2 = st.columns(2)

with c1:
    st.markdown("#### 🏆 Top 10 servicios (transfusiones)")
    t = by_service(fdata.get("T"), "Unidades").sort_values("Unidades", ascending=False)
    if not t.empty:
        charts.show_chart(
            charts.bar(t.head(10), "Servicio", "Unidades", "", color="Unidades"),
            "top_serv")
    else:
        st.info("Sin datos de Transfusiones (T).")

with c2:
    st.markdown("#### 🧫 Top 10 hemocomponentes (todas las fuentes)")
    rows = []
    for key in ("T", "I", "SU", "DT"):
        df = fdata.get(key)
        if df is not None and "_hemocomponente" in df.columns:
            tmp = df.copy()
            tmp["_u"] = unit_series(tmp)
            g = tmp.groupby("_hemocomponente")["_u"].sum()
            for h, v in g.items():
                rows.append({"Hemocomponente": h, "Unidades": int(v)})
    if rows:
        hem = (pd.DataFrame(rows).groupby("Hemocomponente")["Unidades"].sum()
               .reset_index().sort_values("Unidades", ascending=False))
        charts.show_chart(
            charts.bar(hem.head(10), "Hemocomponente", "Unidades", "",
                       color="Unidades"), "top_hemo")
    else:
        st.info("Sin datos de hemocomponentes.")

st.divider()

# ---------------------------------------------------------------------------
# Pacientes con mayor número de transfusiones
# ---------------------------------------------------------------------------
st.markdown("### 🩸 Pacientes con mayor número de transfusiones")
pt = fdata.get("PT")
if pt is not None:
    top_pac = (pt[pt["_paciente"] != ""]
               .groupby(["_paciente"]).size()
               .reset_index(name="Transfusiones")
               .rename(columns={"_paciente": "Paciente"})
               .sort_values("Transfusiones", ascending=False))
    c1, c2 = st.columns([1, 1])
    with c1:
        st.dataframe(top_pac.head(20), use_container_width=True, hide_index=True)
    with c2:
        charts.show_chart(
            charts.bar(top_pac.head(10), "Paciente", "Transfusiones",
                       "Top 10 pacientes por transfusiones",
                       color="Transfusiones", orientation="h"), "top_pac")
else:
    st.info("Carga el archivo de Pacientes Transfundidos (PT).")

st.divider()

# ---------------------------------------------------------------------------
# Indicadores porcentuales
# ---------------------------------------------------------------------------
st.markdown("### ％ Indicadores porcentuales")


def units(key):
    df = fdata.get(key)
    if df is None:
        return 0
    tmp = df.copy()
    tmp["_u"] = unit_series(tmp)
    return int(tmp["_u"].sum())


ing = units("I")
tra = units("T")
des = units("DT")
sol = units("SU")

kpi_row([
    {"label": "% Transfundido / ingresado", "icon": "💉",
     "value": f"{100 * tra / ing:.1f}%" if ing else "N/D",
     "color": COLORS["success"], "help_text": "T / I"},
    {"label": "% Descartado / ingresado", "icon": "🗑️",
     "value": f"{100 * des / ing:.1f}%" if ing else "N/D",
     "color": COLORS["danger"], "help_text": "DT / I"},
    {"label": "% Solicitado / ingresado", "icon": "📋",
     "value": f"{100 * sol / ing:.1f}%" if ing else "N/D",
     "color": COLORS["warning"], "help_text": "SU / I"},
    {"label": "% Transfundido / solicitado", "icon": "🔁",
     "value": f"{100 * tra / sol:.1f}%" if sol else "N/D",
     "color": COLORS["accent"], "help_text": "T / SU"},
])

st.divider()
if comp is not None and not comp.empty:
    excel_download_button({"Comparación servicios": comp}, key="cmp")
