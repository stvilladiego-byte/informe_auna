"""Módulo 7 · RAI Positivo."""
from __future__ import annotations

import streamlit as st

from utils.config import COLORS
from utils.data_loader import is_rai_positive
from utils.ui import (inject_css, module_header, ensure_loaded, get_filtered,
                      searchable_table)
from utils.kpis import kpi_row
from utils import charts
from utils.exporters import excel_download_button, pdf_download_button

st.set_page_config(page_title="RAI Positivo", page_icon="⚠️", layout="wide")
inject_css()
module_header("⚠️", "RAI Positivo",
              "Pacientes con Rastreo de Anticuerpos Irregulares positivo.")

data = ensure_loaded()
df = get_filtered(data, "RAI")
if df is None or df.empty:
    st.stop()

df = df.copy()
# Solo positivos (por si el archivo trae mezclados)
if "_rai" in df.columns and df["_rai"].str.strip().ne("").any():
    df = df[is_rai_positive(df["_rai"])]

pac_pos = df.loc[df["_paciente_norm"] != "", "_paciente_norm"].nunique()
n_serv = df["_servicio"].nunique()

# Relación con PT
pt = data.get("PT")
transf_pos = 0
if pt is not None:
    pt_names = set(pt.loc[pt["_paciente_norm"] != "", "_paciente_norm"].unique())
    rai_names = set(df.loc[df["_paciente_norm"] != "", "_paciente_norm"].unique())
    transf_pos = len(pt_names & rai_names)

kpi_row([
    {"label": "Pacientes RAI positivo", "icon": "⚠️", "value": int(pac_pos),
     "color": COLORS["danger"]},
    {"label": "Servicios involucrados", "icon": "🏥", "value": int(n_serv),
     "color": COLORS["accent"]},
    {"label": "RAI+ también transfundidos", "icon": "🩸", "value": int(transf_pos),
     "color": COLORS["warning"], "help_text": "Cruce con PT"},
])
st.divider()

por_serv = (df[df["_paciente_norm"] != ""]
            .groupby("_servicio")["_paciente_norm"].nunique()
            .reset_index().rename(columns={"_servicio": "Servicio",
                                            "_paciente_norm": "Pacientes RAI+"})
            .sort_values("Pacientes RAI+", ascending=False))
if pac_pos:
    por_serv["% del total"] = (100 * por_serv["Pacientes RAI+"] / pac_pos).round(1)

tab1, tab2 = st.tabs(["📊 Visualizaciones", "🏆 Ranking"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        charts.show_chart(
            charts.bar(por_serv, "Servicio", "Pacientes RAI+",
                       "Pacientes con RAI+ por servicio",
                       color="Pacientes RAI+"), "rai_bar")
    with c2:
        charts.show_chart(
            charts.pie(por_serv, "Servicio", "Pacientes RAI+",
                       "Distribución de RAI+ por servicio"), "rai_pie")

with tab2:
    st.markdown("#### 🏆 Ranking de servicios (RAI+)")
    rank = por_serv.reset_index(drop=True)
    rank.index += 1
    st.dataframe(rank, use_container_width=True)

st.divider()
st.markdown("### 📋 Pacientes con RAI positivo")
searchable_table(df.drop_duplicates(subset=["_paciente_norm", "_servicio"]),
                 "rai", ["_paciente", "_servicio", "_rai"])

st.divider()
c1, c2, _ = st.columns([1, 1, 2])
with c1:
    excel_download_button({"RAI+ por servicio": por_serv, "Detalle": df}, key="rai")
with c2:
    pdf_download_button(
        "Módulo · RAI Positivo",
        [("Pacientes RAI+", int(pac_pos)),
         ("Servicios", int(n_serv)),
         ("RAI+ transfundidos (cruce PT)", int(transf_pos))],
        {"RAI+ por servicio": por_serv}, key="rai")
