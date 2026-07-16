"""
========================================================================
  DASHBOARD DE ANÁLISIS · ÁREA DE TRANSFUSIONES · BANCO DE SANGRE
========================================================================
Aplicación Streamlit para el análisis estadístico del servicio de
transfusiones. Carga archivos CSV/TXT, detecta automáticamente su
estructura y despliega indicadores, gráficos interactivos y reportes.

Ejecutar con:   streamlit run app.py
========================================================================
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.config import DATASETS, DATASET_ORDER, COLORS
from utils.data_loader import load_uploaded_files, unit_count
from utils.filters import render_sidebar_filters, filter_all
from utils.kpis import kpi_row
from utils.ui import inject_css, module_header
from utils.exporters import excel_download_button, pdf_download_button

st.set_page_config(
    page_title="Banco de Sangre · Transfusiones",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ---------------------------------------------------------------------------
# Barra lateral: carga de archivos
# ---------------------------------------------------------------------------
st.sidebar.markdown(
    f"<h2 style='color:{COLORS['primary']};margin-bottom:0'>🩸 Banco de Sangre</h2>"
    "<p style='color:#7f8c8d;margin-top:2px'>Análisis de Transfusiones</p>",
    unsafe_allow_html=True,
)
st.sidebar.divider()
st.sidebar.markdown("### 📂 Carga de archivos")
st.sidebar.caption(
    "Sube los archivos **PT, PA, DT, I, T, PC, RAI (RAIP), SU** "
    "(formato .csv o .txt). El nombre del archivo identifica el módulo."
)

uploaded = st.sidebar.file_uploader(
    "Selecciona uno o varios archivos",
    type=["csv", "txt"],
    accept_multiple_files=True,
)

if uploaded:
    data, report = load_uploaded_files(uploaded)
    st.session_state["data"] = data
    st.session_state["load_report"] = report

data = st.session_state.get("data", {})
report = st.session_state.get("load_report", [])

# ---------------------------------------------------------------------------
# Encabezado
# ---------------------------------------------------------------------------
module_header(
    "🩸", "Dashboard de Transfusiones",
    "Panel de control estadístico del Banco de Sangre",
)

if not data:
    st.info(
        "👋 **Bienvenido.** Para comenzar, carga tus archivos en el panel lateral.\n\n"
        "Archivos esperados: `PT.csv`, `PA.csv`, `DT.csv`, `I.csv`, `T.csv`, "
        "`PC.csv`, `RAI.csv` (o `RAIP`), `SU.csv`. También se aceptan `.txt`.\n\n"
        "La aplicación detecta automáticamente la codificación, el separador y "
        "los nombres de las columnas."
    )
    with st.expander("ℹ️ ¿Cómo funciona la detección automática?"):
        st.markdown(
            "- Se prueban codificaciones **UTF-8 / CP1252 / Latin-1** y separadores "
            "`, ; \\t |`.\n"
            "- Cada campo (servicio, hemocomponente, paciente, banco, fecha…) se "
            "resuelve por una lista de **alias** en orden de prioridad, por lo que "
            "la app funciona aunque cambien los nombres de las columnas.\n"
            "- Si falta un archivo, los demás módulos siguen funcionando."
        )
    st.stop()

# ---------------------------------------------------------------------------
# Reporte de carga
# ---------------------------------------------------------------------------
with st.expander("📋 Estado de la carga y mapeo de columnas", expanded=False):
    rep_df = pd.DataFrame(report)
    if not rep_df.empty:
        st.dataframe(
            rep_df[["archivo", "dataset", "filas", "estado"]],
            use_container_width=True, hide_index=True,
        )
    faltantes = [k for k in DATASET_ORDER if k not in data and k != "DNT"]
    if faltantes:
        nombres = ", ".join(f"{DATASETS[k]['label']} ({k})" for k in faltantes)
        st.warning(f"⚠️ Archivos no cargados: {nombres}. "
                   "Los módulos correspondientes se mostrarán vacíos.")
    # Detalle de mapeo por archivo
    for entry in report:
        if entry.get("mapeo"):
            st.markdown(f"**{entry['archivo']}** → columnas detectadas:")
            m = {k: (v or "— no encontrada —") for k, v in entry["mapeo"].items()}
            st.json(m, expanded=False)

# ---------------------------------------------------------------------------
# Filtros globales + aplicar a todos los datasets
# ---------------------------------------------------------------------------
filtros = render_sidebar_filters(data)
fdata = filter_all(data, filtros)


def uniq_patients(df):
    if df is None or "_paciente_norm" not in df.columns:
        return 0
    return int(df.loc[df["_paciente_norm"] != "", "_paciente_norm"].nunique())


def total_units(key):
    df = fdata.get(key)
    return unit_count(df) if df is not None else 0


# ---------------------------------------------------------------------------
# KPIs principales
# ---------------------------------------------------------------------------
st.markdown("### 📊 Indicadores generales")

kpi_row([
    {"label": "Pacientes transfundidos", "icon": "🩸",
     "value": uniq_patients(fdata.get("PT")), "help_text": "Únicos (PT)"},
    {"label": "Pacientes atendidos", "icon": "👥",
     "value": uniq_patients(fdata.get("PA")), "help_text": "Únicos (PA)",
     "color": COLORS["accent"]},
    {"label": "Hemocomp. transfundidos", "icon": "💉",
     "value": total_units("T"), "help_text": "Unidades (T)",
     "color": COLORS["success"]},
    {"label": "Hemocomp. descartados", "icon": "🗑️",
     "value": total_units("DT"), "help_text": "Unidades (DT)",
     "color": COLORS["danger"]},
])

st.write("")

kpi_row([
    {"label": "Hemocomp. ingresados", "icon": "📥",
     "value": total_units("I"), "help_text": "Unidades (I)",
     "color": COLORS["accent"]},
    {"label": "Solicitudes", "icon": "📋",
     "value": total_units("SU"), "help_text": "Unidades solicitadas (SU)",
     "color": COLORS["warning"]},
    {"label": "Pacientes RAI positivo", "icon": "⚠️",
     "value": uniq_patients(fdata.get("RAI")), "help_text": "Únicos (RAI)",
     "color": COLORS["warning"]},
    {"label": "Pruebas cruzadas", "icon": "🧪",
     "value": total_units("PC"), "help_text": "Registros (PC)",
     "color": COLORS["secondary"]},
])

st.divider()

# ---------------------------------------------------------------------------
# Resumen comparativo + navegación
# ---------------------------------------------------------------------------
col_a, col_b = st.columns([2, 1])

with col_a:
    st.markdown("#### 🧭 Volumen por módulo")
    resumen = []
    for k in DATASET_ORDER:
        df = fdata.get(k)
        if df is not None:
            resumen.append({
                "Módulo": f"{DATASETS[k]['icon']} {DATASETS[k]['label']}",
                "Registros": len(df),
                "Unidades / conteo": unit_count(df),
            })
    resumen_df = pd.DataFrame(resumen)
    if not resumen_df.empty:
        import plotly.express as px
        fig = px.bar(resumen_df, x="Registros", y="Módulo", orientation="h",
                     text="Registros", color="Registros",
                     color_continuous_scale="Reds")
        fig.update_layout(template="plotly_white", height=380,
                          margin=dict(l=10, r=10, t=10, b=10),
                          coloraxis_showscale=False)
        fig.update_traces(textposition="outside", cliponaxis=False)
        st.plotly_chart(fig, use_container_width=True)

with col_b:
    st.markdown("#### 📖 Módulos disponibles")
    for k in DATASET_ORDER:
        estado = "✅" if k in data else "⬜"
        st.markdown(f"{estado} {DATASETS[k]['icon']} **{DATASETS[k]['label']}** "
                    f"<span style='color:#7f8c8d'>({k})</span>",
                    unsafe_allow_html=True)
    st.caption("Usa el menú lateral de páginas para navegar los módulos.")

st.divider()

# ---------------------------------------------------------------------------
# Exportaciones globales
# ---------------------------------------------------------------------------
st.markdown("### 📤 Exportar consolidado")
c1, c2, _ = st.columns([1, 1, 2])
with c1:
    excel_download_button(
        {DATASETS[k]["label"][:31]: fdata[k] for k in fdata},
        key="global",
    )
with c2:
    kpis_pdf = [
        ("Pacientes transfundidos", uniq_patients(fdata.get("PT"))),
        ("Pacientes atendidos", uniq_patients(fdata.get("PA"))),
        ("Hemocomponentes transfundidos", total_units("T")),
        ("Hemocomponentes descartados", total_units("DT")),
        ("Hemocomponentes ingresados", total_units("I")),
        ("Solicitudes", total_units("SU")),
        ("Pacientes RAI positivo", uniq_patients(fdata.get("RAI"))),
        ("Pruebas cruzadas", total_units("PC")),
    ]
    pdf_download_button(
        "Dashboard de Transfusiones — Banco de Sangre",
        kpis_pdf,
        {"Resumen por módulo": resumen_df} if not resumen_df.empty else {},
        subtitle="Indicadores generales",
        key="global",
    )

st.caption("Desarrollado para el personal del Banco de Sangre · "
           "Datos procesados localmente en tu navegador/servidor Streamlit.")
