"""Componentes de tarjetas KPI para el dashboard."""
from __future__ import annotations

import streamlit as st

from .config import COLORS


def kpi_card(label: str, value, icon: str = "", help_text: str = "",
             color: str | None = None):
    color = color or COLORS["primary"]
    value_str = f"{value:,}".replace(",", ".") if isinstance(value, int) else str(value)
    html = f"""
    <div style="
        background:#ffffff;
        border-radius:14px;
        padding:18px 20px;
        box-shadow:0 2px 10px rgba(0,0,0,0.06);
        border-left:6px solid {color};
        height:100%;">
      <div style="font-size:13px;color:{COLORS['muted']};font-weight:600;
                  text-transform:uppercase;letter-spacing:.4px;">
        {icon} {label}
      </div>
      <div style="font-size:34px;font-weight:800;color:{COLORS['secondary']};
                  line-height:1.1;margin-top:6px;">
        {value_str}
      </div>
      <div style="font-size:12px;color:{COLORS['muted']};margin-top:2px;">
        {help_text}
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def kpi_row(cards: list[dict]):
    """cards: lista de dicts con claves label, value, icon, help_text, color."""
    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        with col:
            kpi_card(**card)
