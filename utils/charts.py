"""
Helpers de visualización con Plotly.

Todas las funciones devuelven una figura Plotly ya tematizada. `show_chart`
la renderiza en Streamlit e incluye el botón de descarga PNG.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from .config import COLORS, PLOTLY_SEQUENCE

LAYOUT = dict(
    template="plotly_white",
    font=dict(family="Segoe UI, sans-serif", size=13, color=COLORS["secondary"]),
    margin=dict(l=20, r=20, t=50, b=20),
    colorway=PLOTLY_SEQUENCE,
    title_font=dict(size=17, color=COLORS["secondary"]),
    hoverlabel=dict(bgcolor="white", font_size=12),
)


def _apply(fig, title=""):
    fig.update_layout(**LAYOUT)
    if title:
        fig.update_layout(title=title)
    return fig


def bar(df, x, y, title="", color=None, orientation="v", text_auto=True):
    fig = px.bar(df, x=x, y=y, color=color, orientation=orientation,
                 text_auto=".0f" if text_auto else False)
    fig.update_traces(textposition="outside", cliponaxis=False)
    return _apply(fig, title)


def stacked_bar(df, x, y, color, title=""):
    fig = px.bar(df, x=x, y=y, color=color, barmode="stack", text_auto=".0f")
    return _apply(fig, title)


def pie(df, names, values, title="", hole=0.45):
    fig = px.pie(df, names=names, values=values, hole=hole)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return _apply(fig, title)


def heatmap(matrix: pd.DataFrame, title="", xlabel="", ylabel=""):
    fig = go.Figure(
        data=go.Heatmap(
            z=matrix.values,
            x=list(matrix.columns),
            y=list(matrix.index),
            colorscale="Reds",
            text=matrix.values,
            texttemplate="%{text}",
            hovertemplate=f"{ylabel}: %{{y}}<br>{xlabel}: %{{x}}<br>Valor: %{{z}}<extra></extra>",
        )
    )
    return _apply(fig, title)


def treemap(df, path, values, title=""):
    fig = px.treemap(df, path=path, values=values,
                     color=values, color_continuous_scale="Reds")
    fig.update_traces(textinfo="label+value+percent root")
    return _apply(fig, title)


def sunburst(df, path, values, title=""):
    fig = px.sunburst(df, path=path, values=values,
                      color=values, color_continuous_scale="Reds")
    fig.update_traces(textinfo="label+value")
    return _apply(fig, title)


def sankey(labels, source, target, value, title=""):
    fig = go.Figure(data=[go.Sankey(
        node=dict(label=labels, pad=15, thickness=18,
                  color=COLORS["accent"],
                  line=dict(color="white", width=0.5)),
        link=dict(source=source, target=target, value=value,
                  color="rgba(192,57,43,0.35)"),
    )])
    return _apply(fig, title)


def line(df, x, y, title="", color=None, markers=True):
    fig = px.line(df, x=x, y=y, color=color, markers=markers)
    return _apply(fig, title)


def show_chart(fig, key: str):
    """Renderiza la figura y ofrece descarga PNG (si kaleido está disponible)."""
    st.plotly_chart(fig, use_container_width=True, key=f"plot_{key}")
    try:
        png = fig.to_image(format="png", scale=2, width=1100, height=600)
        st.download_button(
            "🖼️ Descargar gráfico (PNG)",
            data=png,
            file_name=f"{key}.png",
            mime="image/png",
            key=f"png_{key}",
        )
    except Exception:
        st.caption("💡 Para exportar PNG instala `kaleido` (ya incluido en requirements).")
