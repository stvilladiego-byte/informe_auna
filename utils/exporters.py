"""
Exportadores: Excel (OpenPyXL), PDF (ReportLab) y utilidades de descarga.
"""
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import streamlit as st

from .config import COLORS


def _clean_for_export(df: pd.DataFrame) -> pd.DataFrame:
    """Quita columnas auxiliares internas (prefijo '_') para exportar limpio."""
    keep = [c for c in df.columns if not c.startswith("_")]
    return df[keep] if keep else df


def to_excel(sheets: dict[str, pd.DataFrame]) -> bytes:
    """Genera un .xlsx con una hoja por dataframe."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for name, df in sheets.items():
            safe = str(name)[:31]
            _clean_for_export(df).to_excel(writer, sheet_name=safe, index=False)
    return buffer.getvalue()


def excel_download_button(sheets: dict[str, pd.DataFrame], label="📊 Exportar a Excel",
                          filename="reporte_banco_sangre.xlsx", key="xlsx"):
    try:
        data = to_excel(sheets)
        st.download_button(
            label, data=data, file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"dl_{key}",
        )
    except Exception as exc:  # noqa: BLE001
        st.warning(f"No se pudo generar el Excel: {exc}")


def to_pdf(title: str, kpis: list[tuple], tables: dict[str, pd.DataFrame],
           subtitle: str = "") -> bytes:
    """Genera un PDF simple con KPIs y tablas resumidas."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            topMargin=1.2 * cm, bottomMargin=1.2 * cm,
                            leftMargin=1.2 * cm, rightMargin=1.2 * cm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("H", fontSize=18, textColor=colors.HexColor(COLORS["primary"]),
                              spaceAfter=6, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle("Sub", fontSize=10, textColor=colors.grey, spaceAfter=12))
    story = [Paragraph(title, styles["H"])]
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    story.append(Paragraph(f"{subtitle}  ·  Generado: {stamp}", styles["Sub"]))

    if kpis:
        kpi_data = [[str(k), str(v)] for k, v in kpis]
        t = Table([["Indicador", "Valor"]] + kpi_data, colWidths=[10 * cm, 6 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLORS["primary"])),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6fa")]),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        story += [t, Spacer(1, 14)]

    for name, df in tables.items():
        story.append(Paragraph(name, styles["H"]))
        df = _clean_for_export(df).head(25)
        if df.empty:
            story.append(Paragraph("Sin datos.", styles["Sub"]))
            continue
        data = [list(df.columns)] + df.astype(str).values.tolist()
        t = Table(data, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLORS["secondary"])),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6fa")]),
        ]))
        story += [t, Spacer(1, 16)]

    doc.build(story)
    return buffer.getvalue()


def pdf_download_button(title, kpis, tables, subtitle="", key="pdf",
                        filename="reporte_banco_sangre.pdf"):
    try:
        data = to_pdf(title, kpis, tables, subtitle)
        st.download_button(
            "📄 Exportar a PDF", data=data, file_name=filename,
            mime="application/pdf", key=f"dl_{key}",
        )
    except Exception as exc:  # noqa: BLE001
        st.warning(f"No se pudo generar el PDF: {exc}")
