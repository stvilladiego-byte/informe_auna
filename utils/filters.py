"""
Filtros globales del dashboard.

Los filtros se guardan en st.session_state y se aplican a cualquier dataframe
mapeado. Cada filtro solo actúa sobre los datasets que contienen el campo
correspondiente, de modo que nunca "vacía" tablas que no tienen esa dimensión.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st


def _union_values(data: dict, field: str) -> list:
    vals: set = set()
    for df in data.values():
        col = f"_{field}"
        if col in df.columns:
            vals.update(v for v in df[col].dropna().unique() if str(v).strip())
    return sorted(vals)


def _date_bounds(data: dict):
    mn, mx = None, None
    for df in data.values():
        if "_fecha_dt" in df.columns:
            s = df["_fecha_dt"].dropna()
            if not s.empty:
                mn = s.min() if mn is None else min(mn, s.min())
                mx = s.max() if mx is None else max(mx, s.max())
    return mn, mx


def render_sidebar_filters(data: dict) -> dict:
    """Dibuja los filtros globales en la barra lateral y devuelve el dict de
    selección. Debe llamarse en cada página."""
    st.sidebar.markdown("### 🔎 Filtros globales")

    servicios = _union_values(data, "servicio")
    hemos = _union_values(data, "hemocomponente")
    bancos = _union_values(data, "banco")
    pacientes = _union_values(data, "paciente")

    filtros = {}

    # Fecha
    mn, mx = _date_bounds(data)
    if mn is not None and mx is not None and mn != mx:
        rango = st.sidebar.date_input(
            "📅 Rango de fechas",
            value=(mn.date(), mx.date()),
            min_value=mn.date(),
            max_value=mx.date(),
        )
        if isinstance(rango, (list, tuple)) and len(rango) == 2:
            filtros["fecha"] = (
                pd.Timestamp(rango[0]),
                pd.Timestamp(rango[1]) + pd.Timedelta(days=1),
            )

    if servicios:
        filtros["servicio"] = st.sidebar.multiselect("🏥 Servicio", servicios)
    if hemos:
        filtros["hemocomponente"] = st.sidebar.multiselect(
            "🧫 Hemocomponente", hemos
        )
    if bancos:
        filtros["banco"] = st.sidebar.multiselect("🏦 Banco de sangre", bancos)
    if pacientes:
        filtros["paciente"] = st.sidebar.text_input(
            "🔍 Buscar paciente (contiene)"
        ).strip()

    if st.sidebar.button("♻️ Limpiar filtros"):
        st.session_state.pop("_filtros", None)
        st.rerun()

    st.session_state["_filtros"] = filtros
    return filtros


def apply_filters(df: pd.DataFrame, filtros: dict | None) -> pd.DataFrame:
    """Aplica los filtros globales a un dataframe mapeado."""
    if df is None or df.empty or not filtros:
        return df
    out = df

    if "fecha" in filtros and "_fecha_dt" in out.columns:
        ini, fin = filtros["fecha"]
        mask = out["_fecha_dt"].between(ini, fin) | out["_fecha_dt"].isna()
        # Solo filtramos si el dataset realmente tiene fechas válidas
        if out["_fecha_dt"].notna().any():
            out = out[out["_fecha_dt"].between(ini, fin)]

    for field in ("servicio", "hemocomponente", "banco"):
        sel = filtros.get(field)
        col = f"_{field}"
        if sel and col in out.columns:
            out = out[out[col].isin(sel)]

    texto = filtros.get("paciente")
    if texto and "_paciente" in out.columns:
        out = out[out["_paciente"].str.contains(texto, case=False, na=False)]

    return out


def filter_all(data: dict, filtros: dict | None) -> dict:
    """Aplica filtros a todos los datasets a la vez."""
    return {k: apply_filters(v, filtros) for k, v in data.items()}
