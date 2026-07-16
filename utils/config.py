"""
Configuración central del dashboard del Banco de Sangre.

Define:
  - Identidad de cada dataset (nombre, icono, alias de archivo).
  - El sistema de MAPEO DINÁMICO de columnas: para cada campo canónico
    (paciente, servicio, hemocomponente, etc.) se listan los posibles
    nombres de columna en orden de prioridad. El cargador detecta cuál
    existe realmente en el archivo y la normaliza, de modo que la app
    funciona aunque cambien los nombres de las columnas.

No se asume ningún nombre de columna: todo se resuelve por alias.
"""

# ---------------------------------------------------------------------------
# Paleta corporativa (tonos clínicos / hematología)
# ---------------------------------------------------------------------------
# Paleta de marca AUNA COLOMBIA (extraída de la identidad corporativa)
COLORS = {
    "primary": "#00B0CA",      # turquesa Auna (color principal)
    "primary_dark": "#00788A",  # turquesa oscuro (degradados)
    "secondary": "#3C3834",    # carbón Auna (textos y encabezados)
    "accent": "#0050B5",       # azul Auna
    "success": "#8FB800",      # verde lima Auna (oscurecido para contraste)
    "lime": "#BED600",         # verde lima Auna (vivo)
    "warning": "#FFB81C",      # amarillo/ámbar Auna
    "danger": "#D50032",       # rojo Auna
    "purple": "#511E84",       # morado Auna
    "magenta": "#E31C79",      # magenta Auna
    "orange": "#FF6900",       # naranja Auna
    "muted": "#8A857F",
    "bg": "#F3F7F8",
}

# Secuencia de colores para gráficos categóricos (identidad Auna)
PLOTLY_SEQUENCE = [
    "#00B0CA", "#BED600", "#0050B5", "#511E84", "#E31C79",
    "#FF6900", "#FFB81C", "#D50032", "#3C3834", "#00788A",
]

# Escala continua de marca (para heatmaps, treemaps, sunburst)
AUNA_CONTINUOUS = [
    "#E6F7FA", "#99E0EA", "#33C4D6", "#00B0CA", "#00788A", "#005866",
]

# ---------------------------------------------------------------------------
# Campos canónicos y sus alias (en orden de prioridad).
# La comparación se hace normalizando (mayúsculas, sin espacios/underscores).
# ---------------------------------------------------------------------------
FIELD_ALIASES = {
    "paciente": [
        "NOMBREPACIENTE", "PACIENTEAPENOM", "APENOM", "NOMBRE",
        "PACIENTE", "NOMBRECOMPLETO",
    ],
    "documento": [
        "NUMDOCPACIENTE", "DOCUMENTO", "NUMDOC", "CEDULA", "IDENTIFICACION",
    ],
    # La descripción del servicio tiene prioridad sobre el código numérico
    "servicio": [
        "SERVICIODESCRIPCION", "SERVICIOPOBLADOR", "DESCSERVICIO",
        "SERVICIOPRUEBAC", "SERVICIO",
    ],
    # PRODUCTO suele traer el hemocomponente; HEMOCOMPONENTE como respaldo
    "hemocomponente": [
        "PRODUCTO", "HEMOCOMPONENTE", "COMPONENTE", "TIPOHEMOCOMPONENTE",
    ],
    "banco": [
        "HOSPITALBOLSA", "BANCODESANGRE", "BANCO", "PROVEEDOR",
    ],
    "fecha": [
        "FECHATRANSFUSION", "FECHADESCARTE", "FECHAINGRESO", "FECHASOLICITUD",
        "FECHAALTA", "FECHAALTACOMPATIBILIZA", "FECHA",
    ],
    "cantidad": [
        "CANTIDAD", "CANTIDADINGRESADA", "UNIDADES", "NUMUNIDADES",
    ],
    "resultado_pc": [
        "PRUEBASCRUZADAS", "RESULTADOPC", "RESULTADO", "COMPATIBILIDAD",
    ],
    "rai": [
        "RAIPOBLADOR", "RAIP", "RAI", "RESULTADORAI",
    ],
    "motivo": [
        "MOTIVODESCARTE", "MOTIVO", "CAUSADESCARTE",
    ],
    "abo": ["ABO", "GRUPOSANGUINEO", "GRUPO"],
    "rh": ["RH", "FACTORRH"],
}

# ---------------------------------------------------------------------------
# Datasets esperados. `file_aliases` son los nombres de archivo (sin extensión)
# que se aceptan para identificar cada dataset al cargar.
# ---------------------------------------------------------------------------
DATASETS = {
    "PT": {
        "label": "Pacientes Transfundidos",
        "icon": "🩸",
        "file_aliases": ["PT", "PACIENTESTRANSFUNDIDOS"],
        "fields": ["paciente", "documento", "servicio"],
        "measure": "count_rows",  # cada fila = una transfusión
    },
    "PA": {
        "label": "Pacientes Atendidos",
        "icon": "👥",
        "file_aliases": ["PA", "PACIENTESATENDIDOS"],
        "fields": ["paciente", "servicio"],
        "measure": "count_rows",
    },
    "DT": {
        "label": "Descartes de Transfusiones",
        "icon": "🗑️",
        "file_aliases": ["DT", "DESCARTES"],
        "fields": ["paciente", "servicio", "hemocomponente", "banco", "fecha", "motivo"],
        "measure": "units",
    },
    "DNT": {
        "label": "Descartes No Transfundidos",
        "icon": "♻️",
        "file_aliases": ["DNT"],
        "fields": ["servicio", "hemocomponente", "banco", "fecha", "motivo"],
        "measure": "units",
    },
    "I": {
        "label": "Ingresos",
        "icon": "📥",
        "file_aliases": ["I", "INGRESOS"],
        "fields": ["hemocomponente", "banco", "fecha", "cantidad", "abo", "rh"],
        "measure": "units",
    },
    "T": {
        "label": "Transfusiones",
        "icon": "💉",
        "file_aliases": ["T", "TRANSFUSIONES"],
        "fields": ["paciente", "servicio", "hemocomponente", "banco", "resultado_pc", "rai"],
        "measure": "units",
    },
    "PC": {
        "label": "Pruebas Cruzadas",
        "icon": "🧪",
        "file_aliases": ["PC", "PRUEBASCRUZADAS"],
        "fields": ["paciente", "servicio", "hemocomponente", "fecha", "resultado_pc"],
        "measure": "count_rows",
    },
    "RAI": {
        "label": "RAI Positivo",
        "icon": "⚠️",
        "file_aliases": ["RAI", "RAIP", "RAIPOSITIVO"],
        "fields": ["paciente", "servicio", "rai"],
        "measure": "count_rows",
    },
    "SU": {
        "label": "Solicitudes de Unidades",
        "icon": "📋",
        "file_aliases": ["SU", "SOLICITUDES", "SOLICITUDESUNIDADES"],
        "fields": ["servicio", "hemocomponente", "fecha", "cantidad", "abo", "rh"],
        "measure": "units",
        # En SU la columna CANTIDAD sí representa nº de unidades solicitadas.
        # (En I, en cambio, CANTIDAD es el volumen en mL, por lo que NO se suma
        #  y cada fila cuenta como una unidad ingresada.)
        "sum_cantidad": True,
    },
}

# Orden de aparición en el dashboard
DATASET_ORDER = ["PT", "PA", "DT", "DNT", "I", "T", "PC", "RAI", "SU"]

# Valores que representan "compatibilidad positiva/negativa" en pruebas cruzadas
COMPATIBLE_TOKENS = ["COMPATIBLE"]
INCOMPATIBLE_TOKENS = ["INCOMPATIBLE", "MENOS INCOMPATIBLE", "NO COMPATIBLE"]

# Tokens que indican RAI positivo
RAI_POSITIVE_TOKENS = ["+", "POSITIVO", "POS", "SI", "S"]
