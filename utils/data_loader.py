"""
Cargador y normalizador de datos.

Responsabilidades:
  1. Leer archivos CSV/TXT subidos, detectando codificación y delimitador.
  2. Identificar a qué dataset pertenece cada archivo por su nombre.
  3. Aplicar el mapeo dinámico de columnas (utils.config.FIELD_ALIASES)
     generando columnas canónicas con prefijo "_" (p. ej. "_servicio").
  4. Exponer helpers de medida (conteo de unidades) y normalización de nombres.

Ninguna función asume nombres de columna: todo se resuelve por alias.
"""
from __future__ import annotations

import io
import re
import unicodedata
from typing import Optional

import pandas as pd

from .config import (
    DATASETS,
    FIELD_ALIASES,
    RAI_POSITIVE_TOKENS,
    COMPATIBLE_TOKENS,
    INCOMPATIBLE_TOKENS,
)

ENCODINGS = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
DELIMITERS = [",", ";", "\t", "|"]


# ---------------------------------------------------------------------------
# Utilidades de texto
# ---------------------------------------------------------------------------
def _strip_accents(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", str(text))
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalize_colname(name: str) -> str:
    """Normaliza un nombre de columna para comparar alias."""
    name = _strip_accents(str(name)).upper()
    return re.sub(r"[^A-Z0-9]", "", name)


def normalize_name(value) -> str:
    """Normaliza nombres de pacientes para poder cruzar tablas (PT<->RAI)."""
    if value is None:
        return ""
    txt = _strip_accents(str(value)).upper().strip()
    txt = re.sub(r"\s+", " ", txt)
    return txt


# ---------------------------------------------------------------------------
# Lectura robusta de archivos
# ---------------------------------------------------------------------------
def _read_bytes(raw: bytes) -> pd.DataFrame:
    """Lee bytes probando codificaciones y delimitadores hasta lograr >1 columna."""
    last_err: Optional[Exception] = None
    for enc in ENCODINGS:
        try:
            text = raw.decode(enc)
        except (UnicodeDecodeError, LookupError) as exc:
            last_err = exc
            continue
        # Detectar delimitador por la primera línea
        first_line = text.splitlines()[0] if text.splitlines() else ""
        delim = max(DELIMITERS, key=lambda d: first_line.count(d))
        if first_line.count(delim) == 0:
            delim = ","
        try:
            df = pd.read_csv(
                io.StringIO(text),
                sep=delim,
                dtype=str,
                keep_default_na=False,
                skip_blank_lines=True,
                engine="python",
            )
            if df.shape[1] >= 1:
                df.columns = [str(c).strip() for c in df.columns]
                return df
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            continue
    raise ValueError(f"No se pudo leer el archivo: {last_err}")


def identify_dataset(filename: str) -> Optional[str]:
    """Devuelve la clave de dataset (PT, PA, ...) a partir del nombre de archivo."""
    stem = re.split(r"[./\\]", filename.strip())[-1] if "." not in filename else filename
    stem = filename.rsplit(".", 1)[0]
    stem_norm = normalize_colname(stem)
    # Coincidencia exacta primero
    for key, meta in DATASETS.items():
        for alias in meta["file_aliases"]:
            if stem_norm == normalize_colname(alias):
                return key
    # Coincidencia parcial (por si viene con sufijos como PT_junio)
    for key, meta in DATASETS.items():
        for alias in meta["file_aliases"]:
            an = normalize_colname(alias)
            if len(an) >= 2 and stem_norm.startswith(an):
                return key
    return None


# ---------------------------------------------------------------------------
# Mapeo dinámico de columnas
# ---------------------------------------------------------------------------
def _find_column(df: pd.DataFrame, aliases: list[str]) -> Optional[str]:
    """Busca la primera columna del df que coincida con la lista de alias
    y que además contenga al menos un valor no vacío."""
    norm_map = {normalize_colname(c): c for c in df.columns}
    for alias in aliases:
        an = normalize_colname(alias)
        if an in norm_map:
            col = norm_map[an]
            if df[col].astype(str).str.strip().replace("", pd.NA).notna().any():
                return col
    # Segunda pasada: aceptar aunque esté vacía (para conservar la columna)
    for alias in aliases:
        an = normalize_colname(alias)
        if an in norm_map:
            return norm_map[an]
    return None


def apply_mapping(df: pd.DataFrame, dataset_key: str) -> tuple[pd.DataFrame, dict]:
    """Agrega columnas canónicas (_paciente, _servicio, ...) y devuelve el mapa."""
    df = df.copy()
    meta = DATASETS[dataset_key]
    mapping: dict[str, Optional[str]] = {}
    for field in meta["fields"]:
        aliases = FIELD_ALIASES.get(field, [])
        col = _find_column(df, aliases)
        mapping[field] = col
        if col is not None:
            df[f"_{field}"] = df[col].astype(str).str.strip()
        else:
            df[f"_{field}"] = ""

    # Post-proceso de campos específicos
    if "_servicio" in df:
        df["_servicio"] = df["_servicio"].replace("", "SIN SERVICIO")
    if "_hemocomponente" in df:
        df["_hemocomponente"] = df["_hemocomponente"].replace("", "SIN CLASIFICAR")
    if "_banco" in df:
        df["_banco"] = df["_banco"].replace("", "SIN BANCO")
    if "_paciente" in df:
        df["_paciente_norm"] = df["_paciente"].map(normalize_name)

    # Fecha -> datetime
    if "fecha" in meta["fields"] and mapping.get("fecha"):
        df["_fecha_dt"] = pd.to_datetime(
            df["_fecha"], errors="coerce", dayfirst=True
        )

    # Cantidad -> numérico.
    # Solo se usa como MEDIDA de unidades cuando el dataset lo indica
    # (sum_cantidad=True, p. ej. Solicitudes). En otros casos (Ingresos,
    # donde CANTIDAD es volumen en mL) cada fila cuenta como una unidad.
    if "cantidad" in meta["fields"] and meta.get("sum_cantidad"):
        df["_cantidad_num"] = pd.to_numeric(
            df["_cantidad"].str.replace(",", ".", regex=False), errors="coerce"
        ).fillna(0)

    return df, mapping


def unit_count(df: pd.DataFrame) -> int:
    """Número de unidades/hemocomponentes de un dataframe ya mapeado.
    Usa la columna de cantidad si aporta valores >0; si no, cuenta filas."""
    if "_cantidad_num" in df.columns:
        total = df["_cantidad_num"].sum()
        if total > 0:
            return int(total)
    return int(len(df))


def unit_series(df: pd.DataFrame) -> pd.Series:
    """Serie de unidades por fila (cantidad si aplica, si no 1 por fila)."""
    if "_cantidad_num" in df.columns and df["_cantidad_num"].sum() > 0:
        s = df["_cantidad_num"].copy()
        s = s.where(s > 0, 1)
        return s
    return pd.Series(1, index=df.index)


def is_rai_positive(series: pd.Series) -> pd.Series:
    tokens = [t.upper() for t in RAI_POSITIVE_TOKENS]
    return series.astype(str).str.strip().str.upper().isin(tokens)


def classify_compatibility(value: str) -> str:
    v = _strip_accents(str(value)).upper().strip()
    for tok in INCOMPATIBLE_TOKENS:
        if _strip_accents(tok).upper() in v:
            return "Incompatible"
    for tok in COMPATIBLE_TOKENS:
        if _strip_accents(tok).upper() in v:
            return "Compatible"
    return "Otro" if v else "Sin dato"


# ---------------------------------------------------------------------------
# Punto de entrada usado por app.py
# ---------------------------------------------------------------------------
def load_uploaded_files(uploaded_files) -> tuple[dict, list[dict]]:
    """
    Procesa la lista de archivos subidos por Streamlit.

    Devuelve:
      data     -> {dataset_key: DataFrame mapeado}
      report   -> lista de dicts con el estado de cada archivo (para diagnóstico)
    """
    data: dict[str, pd.DataFrame] = {}
    report: list[dict] = []

    for up in uploaded_files:
        entry = {"archivo": up.name, "dataset": None, "filas": 0,
                 "estado": "", "mapeo": {}}
        try:
            raw = up.getvalue() if hasattr(up, "getvalue") else up.read()
            df = _read_bytes(raw)
            key = identify_dataset(up.name)
            if key is None:
                entry["estado"] = "⚠️ Nombre no reconocido (se omite)"
                report.append(entry)
                continue
            mapped, mapping = apply_mapping(df, key)
            data[key] = mapped
            entry.update({
                "dataset": key,
                "filas": len(mapped),
                "estado": "✅ Cargado",
                "mapeo": mapping,
            })
        except Exception as exc:  # noqa: BLE001
            entry["estado"] = f"❌ Error: {exc}"
        report.append(entry)

    return data, report
