"""
Scaffolding común para las páginas: cabeceras, guardas de datos y
agregaciones reutilizables.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from .config import COLORS, DATASETS
from .data_loader import unit_series
from .filters import render_sidebar_filters, apply_filters


def inject_css():
    st.markdown(
        f"""
        <style>
        .block-container {{ padding-top: 1.6rem; }}
        h1, h2, h3 {{ color: {COLORS['secondary']}; }}
        [data-testid="stSidebar"] {{ background: #fbfcfe; }}
        .module-header {{
            background: linear-gradient(90deg, {COLORS['primary']} 0%, {COLORS['primary_dark']} 100%);
            color: white; padding: 16px 22px; border-radius: 14px;
            margin-bottom: 18px;
        }}
        .module-header h1 {{ color: white; margin: 0; font-size: 26px; }}
        .module-header p {{ margin: 2px 0 0; opacity: .9; font-size: 14px; }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 6px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def module_header(icon: str, title: str, subtitle: str = ""):
    st.markdown(
        f"""<div class="module-header">
            <h1>{icon} {title}</h1>
            <p>{subtitle}</p>
        </div>""",
        unsafe_allow_html=True,
    )


def ensure_loaded() -> dict | None:
    """Devuelve los datos cargados o muestra un aviso y detiene la página."""
    data = st.session_state.get("data")
    if not data:
        st.info("⬅️ Primero carga los archivos en la página principal "
                "**Dashboard** para habilitar este módulo.")
        st.stop()
    return data


def get_filtered(data: dict, key: str) -> pd.DataFrame | None:
    """Devuelve el dataframe del dataset `key` con filtros globales aplicados."""
    filtros = render_sidebar_filters(data)
    df = data.get(key)
    if df is None:
        label = DATASETS[key]["label"]
        st.warning(f"No se cargó el archivo de **{label}** ({key}). "
                   "El módulo se muestra vacío.")
        return None
    return apply_filters(df, filtros)


def agg_by(df: pd.DataFrame, field: str, value_name="Cantidad") -> pd.DataFrame:
    """Agrupa por un campo canónico sumando unidades (o filas)."""
    col = f"_{field}"
    if col not in df.columns:
        return pd.DataFrame(columns=[field, value_name])
    tmp = df.copy()
    tmp["_u"] = unit_series(tmp)
    out = (tmp.groupby(col)["_u"].sum()
           .reset_index()
           .rename(columns={col: field.capitalize(), "_u": value_name})
           .sort_values(value_name, ascending=False))
    out[value_name] = out[value_name].astype(int)
    return out


def agg_two(df: pd.DataFrame, f1: str, f2: str, value_name="Cantidad") -> pd.DataFrame:
    c1, c2 = f"_{f1}", f"_{f2}"
    if c1 not in df.columns or c2 not in df.columns:
        return pd.DataFrame(columns=[f1, f2, value_name])
    tmp = df.copy()
    tmp["_u"] = unit_series(tmp)
    out = (tmp.groupby([c1, c2])["_u"].sum().reset_index()
           .rename(columns={c1: f1.capitalize(), c2: f2.capitalize(),
                            "_u": value_name}))
    out[value_name] = out[value_name].astype(int)
    return out.sort_values(value_name, ascending=False)


def searchable_table(df: pd.DataFrame, key: str, cols: list[str] | None = None):
    """Tabla con buscador de texto libre y descarga CSV."""
    display = df.copy()
    if cols:
        display = display[[c for c in cols if c in display.columns]]
    else:
        display = display[[c for c in display.columns if not c.startswith("_")]]
    q = st.text_input("🔍 Buscar en la tabla", key=f"srch_{key}").strip()
    if q:
        mask = display.astype(str).apply(
            lambda r: r.str.contains(q, case=False, na=False)).any(axis=1)
        display = display[mask]
    st.dataframe(display, use_container_width=True, hide_index=True)
    st.caption(f"{len(display):,} registros".replace(",", "."))
    return display
