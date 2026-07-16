"""Módulo 1 · Pacientes Transfundidos (PT) + relación con RAI positivo."""
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

st.set_page_config(page_title="Pacientes Transfundidos", page_icon="🩸", layout="wide")
inject_css()
module_header("🩸", "Pacientes Transfundidos (PT)",
              "Un paciente puede transfundirse varias veces; cada fila es una transfusión.")

data = ensure_loaded()
df = get_filtered(data, "PT")
if df is None or df.empty:
    st.stop()

# --- Métricas ---
pac_unicos = df.loc[df["_paciente_norm"] != "", "_paciente_norm"].nunique()
n_transf = len(df)
n_serv = df["_servicio"].nunique()

kpi_row([
    {"label": "Pacientes únicos", "icon": "🩸", "value": int(pac_unicos)},
    {"label": "Transfusiones (registros)", "icon": "💉", "value": int(n_transf),
     "color": COLORS["success"]},
    {"label": "Servicios", "icon": "🏥", "value": int(n_serv),
     "color": COLORS["accent"]},
    {"label": "Prom. transf./paciente", "icon": "📈",
     "value": f"{n_transf / pac_unicos:.1f}" if pac_unicos else "0",
     "color": COLORS["warning"]},
])
st.divider()

# --- Agregados por servicio ---
pac_serv = (df[df["_paciente_norm"] != ""]
            .groupby("_servicio")["_paciente_norm"].nunique()
            .reset_index().rename(columns={"_servicio": "Servicio",
                                            "_paciente_norm": "Pacientes"})
            .sort_values("Pacientes", ascending=False))
transf_serv = agg_by(df, "servicio", "Transfusiones")

tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Por servicio", "🏆 Ranking", "🔥 Heatmap", "⚠️ Relación con RAI"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        charts.show_chart(
            charts.bar(pac_serv, "Servicio", "Pacientes",
                       "Pacientes transfundidos por servicio", color="Pacientes"),
            "pt_pac_serv")
    with c2:
        charts.show_chart(
            charts.pie(transf_serv, "Servicio", "Transfusiones",
                       "Distribución de transfusiones por servicio"),
            "pt_pie")
    charts.show_chart(
        charts.bar(transf_serv, "Servicio", "Transfusiones",
                   "Total de transfusiones por servicio", color="Transfusiones"),
        "pt_transf_serv")

with tab2:
    st.markdown("#### 🏆 Ranking de servicios")
    ranking = transf_serv.merge(pac_serv, on="Servicio", how="outer").fillna(0)
    ranking[["Transfusiones", "Pacientes"]] = ranking[["Transfusiones", "Pacientes"]].astype(int)
    ranking = ranking.sort_values("Transfusiones", ascending=False).reset_index(drop=True)
    ranking.index += 1
    st.dataframe(ranking, use_container_width=True)
    charts.show_chart(
        charts.bar(ranking.head(10), "Servicio", "Transfusiones",
                   "Top 10 servicios por transfusiones", color="Transfusiones"),
        "pt_top10")

with tab3:
    st.markdown("#### 🔥 Mapa de calor")
    # Si existe el dataset de Transfusiones, cruzamos servicio × hemocomponente
    tdf = data.get("T")
    if tdf is not None and "_hemocomponente" in tdf.columns:
        base = agg_two(tdf, "servicio", "hemocomponente", "Unidades")
        matrix = base.pivot_table(index="Servicio", columns="Hemocomponente",
                                   values="Unidades", aggfunc="sum", fill_value=0)
        charts.show_chart(
            charts.heatmap(matrix, "Unidades transfundidas · Servicio × Hemocomponente",
                           "Hemocomponente", "Servicio"),
            "pt_heat")
    else:
        # Alternativa: intensidad de transfusiones por servicio
        m = transf_serv.set_index("Servicio")[["Transfusiones"]]
        charts.show_chart(
            charts.heatmap(m, "Intensidad de transfusiones por servicio",
                           "Métrica", "Servicio"),
            "pt_heat2")

with tab4:
    st.markdown("#### ⚠️ Pacientes transfundidos con RAI positivo")
    rai = data.get("RAI")
    if rai is None:
        st.warning("No se cargó el archivo **RAI/RAIP**. No es posible cruzar la información.")
    else:
        rai_names = set(rai.loc[rai["_paciente_norm"] != "", "_paciente_norm"].unique())
        pt_pac = df[df["_paciente_norm"] != ""].copy()
        pt_pac["RAI positivo"] = pt_pac["_paciente_norm"].isin(rai_names)

        pac_pos = pt_pac.loc[pt_pac["RAI positivo"], "_paciente_norm"].nunique()
        kpi_row([
            {"label": "Transfundidos c/ RAI+", "icon": "⚠️", "value": int(pac_pos),
             "color": COLORS["danger"]},
            {"label": "% del total transfundidos", "icon": "％",
             "value": f"{100 * pac_pos / pac_unicos:.1f}%" if pac_unicos else "0%",
             "color": COLORS["warning"]},
        ])

        # % por servicio (pacientes únicos y RAI+ por servicio)
        pos = (pt_pac[pt_pac["RAI positivo"]]
               .groupby("_servicio")["_paciente_norm"].nunique())
        by_serv = (pt_pac.groupby("_servicio")["_paciente_norm"].nunique()
                   .reset_index().rename(columns={"_servicio": "Servicio",
                                                  "_paciente_norm": "Pacientes"}))
        by_serv["RAI positivos"] = by_serv["Servicio"].map(pos).fillna(0).astype(int)
        by_serv["% RAI+"] = (100 * by_serv["RAI positivos"] /
                             by_serv["Pacientes"]).round(1)
        by_serv = by_serv.sort_values("RAI positivos", ascending=False)

        c1, c2 = st.columns(2)
        with c1:
            charts.show_chart(
                charts.bar(by_serv, "Servicio", "RAI positivos",
                           "Pacientes con RAI+ por servicio", color="RAI positivos"),
                "pt_rai_serv")
        with c2:
            charts.show_chart(
                charts.bar(by_serv[by_serv["% RAI+"] > 0], "Servicio", "% RAI+",
                           "Porcentaje de RAI+ por servicio", color="% RAI+"),
                "pt_rai_pct")

        st.markdown("##### 📋 Pacientes transfundidos con RAI positivo")
        tabla = (pt_pac[pt_pac["RAI positivo"]]
                 [["_paciente", "_servicio"]]
                 .drop_duplicates()
                 .rename(columns={"_paciente": "Paciente", "_servicio": "Servicio"}))
        st.dataframe(tabla, use_container_width=True, hide_index=True)
        st.dataframe(by_serv, use_container_width=True, hide_index=True)

st.divider()
st.markdown("### 📋 Tabla de pacientes transfundidos")
tabla_pt = searchable_table(df, "pt", ["_paciente", "_documento", "_servicio"])

st.divider()
c1, c2, _ = st.columns([1, 1, 2])
with c1:
    excel_download_button({"Pacientes por servicio": pac_serv,
                           "Transfusiones por servicio": transf_serv,
                           "Detalle": df}, key="pt")
with c2:
    pdf_download_button(
        "Módulo · Pacientes Transfundidos (PT)",
        [("Pacientes únicos", int(pac_unicos)),
         ("Transfusiones", int(n_transf)),
         ("Servicios", int(n_serv))],
        {"Transfusiones por servicio": transf_serv,
         "Pacientes por servicio": pac_serv},
        key="pt")
