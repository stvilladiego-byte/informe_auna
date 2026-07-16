"""Módulo 2 · Pacientes Atendidos (PA)."""
from __future__ import annotations

import streamlit as st

from utils.config import COLORS
from utils.ui import (inject_css, module_header, ensure_loaded, get_filtered,
                      searchable_table)
from utils.kpis import kpi_row
from utils import charts
from utils.exporters import excel_download_button, pdf_download_button

st.set_page_config(page_title="Pacientes Atendidos", page_icon="👥", layout="wide")
inject_css()
module_header("👥", "Pacientes Atendidos (PA)",
              "Registros de atención; un paciente puede aparecer varias veces.")

data = ensure_loaded()
df = get_filtered(data, "PA")
if df is None or df.empty:
    st.stop()

pac_unicos = df.loc[df["_paciente_norm"] != "", "_paciente_norm"].nunique()
n_reg = len(df)
n_serv = df["_servicio"].nunique()
# Pares únicos paciente + servicio: un paciente atendido en 2 servicios cuenta 2 veces.
# Este total coincide con la suma de las barras "por servicio".
pac_x_serv = int(df[df["_paciente_norm"] != ""]
                 .drop_duplicates(["_paciente_norm", "_servicio"]).shape[0])
multi_serv = pac_x_serv - int(pac_unicos)  # pacientes atendidos en más de un servicio

kpi_row([
    {"label": "Pacientes únicos (personas)", "icon": "👥", "value": int(pac_unicos),
     "help_text": "Nombres distintos"},
    {"label": "Atendidos por servicio", "icon": "🏥", "value": pac_x_serv,
     "color": COLORS["accent"],
     "help_text": "Únicos por servicio (suma de las barras)"},
    {"label": "Atenciones (registros)", "icon": "🗂️", "value": int(n_reg),
     "color": COLORS["secondary"]},
    {"label": "Servicios", "icon": "🩺", "value": int(n_serv),
     "color": COLORS["success"]},
])
if multi_serv > 0:
    st.caption(
        f"ℹ️ Hay **{int(pac_unicos)} pacientes distintos**, pero **{pac_x_serv} "
        f"atendidos por servicio**: {multi_serv} paciente(s) fueron atendidos en "
        "más de un servicio y por eso se cuentan en cada uno. La diferencia entre "
        "ambos totales corresponde a esos casos."
    )
st.divider()

# Pacientes únicos por servicio y atenciones por servicio
pac_serv = (df[df["_paciente_norm"] != ""]
            .groupby("_servicio")["_paciente_norm"].nunique()
            .reset_index().rename(columns={"_servicio": "Servicio",
                                            "_paciente_norm": "Pacientes"})
            .sort_values("Pacientes", ascending=False))
aten_serv = (df.groupby("_servicio").size().reset_index(name="Atenciones")
             .rename(columns={"_servicio": "Servicio"})
             .sort_values("Atenciones", ascending=False))

tab1, tab2 = st.tabs(["📊 Visualizaciones", "🏆 Ranking / Top 10"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        charts.show_chart(
            charts.bar(pac_serv, "Servicio", "Pacientes",
                       "Pacientes atendidos por servicio", color="Pacientes"),
            "pa_bar")
    with c2:
        charts.show_chart(
            charts.pie(pac_serv, "Servicio", "Pacientes",
                       "Distribución de pacientes por servicio"),
            "pa_pie")

with tab2:
    st.markdown("#### 🏆 Top 10 servicios por pacientes atendidos")
    top = pac_serv.head(10)
    charts.show_chart(
        charts.bar(top, "Servicio", "Pacientes", "Top 10 servicios",
                   color="Pacientes", orientation="v"),
        "pa_top10")
    ranking = pac_serv.merge(aten_serv, on="Servicio", how="outer").fillna(0)
    ranking[["Pacientes", "Atenciones"]] = ranking[["Pacientes", "Atenciones"]].astype(int)
    ranking = ranking.reset_index(drop=True)
    ranking.index += 1
    st.dataframe(ranking, use_container_width=True)

st.divider()
st.markdown("### 📋 Tabla dinámica de pacientes atendidos")
searchable_table(df, "pa", ["_paciente", "_servicio"])

st.divider()
c1, c2, _ = st.columns([1, 1, 2])
with c1:
    excel_download_button({"Pacientes por servicio": pac_serv,
                           "Detalle": df}, key="pa")
with c2:
    pdf_download_button(
        "Módulo · Pacientes Atendidos (PA)",
        [("Pacientes únicos", int(pac_unicos)),
         ("Atenciones", int(n_reg)), ("Servicios", int(n_serv))],
        {"Pacientes por servicio": pac_serv}, key="pa")
