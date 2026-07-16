# 🩸 Dashboard de Análisis · Área de Transfusiones (Banco de Sangre)

Aplicación web desarrollada en **Python + Streamlit** para el análisis
estadístico del servicio de transfusiones de un Banco de Sangre. Diseño moderno
tipo Power BI, con KPIs, gráficos interactivos (Plotly), filtros globales,
tablas dinámicas y exportación a Excel, PDF y PNG.

La aplicación es **totalmente dinámica**: detecta automáticamente la
codificación, el separador y los nombres de las columnas de cada archivo, por lo
que sigue funcionando aunque las columnas cambien de nombre.

---

## 🚀 Ejecución local

```bash
# 1. Clonar / descargar el proyecto y entrar a la carpeta
cd app_banco_sangre

# 2. (Opcional) crear entorno virtual
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
streamlit run app.py
```

La app se abre en `http://localhost:8501`.

---

## 📂 Archivos de entrada

Se cargan desde la barra lateral (formato `.csv` o `.txt`). El **nombre del
archivo** identifica el módulo:

| Archivo        | Módulo                          |
|----------------|---------------------------------|
| `PT`           | Pacientes Transfundidos         |
| `PA`           | Pacientes Atendidos             |
| `DT`           | Descartes de Transfusiones      |
| `DNT`          | Descartes No Transfundidos (opc.) |
| `I`            | Ingresos                        |
| `T`            | Transfusiones                   |
| `PC`           | Pruebas Cruzadas                |
| `RAI` / `RAIP` | RAI Positivo                    |
| `SU`           | Solicitudes de Unidades         |

Si falta algún archivo, los demás módulos siguen funcionando y se avisa
claramente en el panel de estado de carga.

### Detección automática de columnas

No se asume ningún nombre de columna. Cada campo lógico se resuelve mediante una
lista de **alias** en orden de prioridad (ver `utils/config.py → FIELD_ALIASES`).
Por ejemplo, el "servicio" se toma de `SERVICIODESCRIPCION`, y si no existe, de
`SERVICIOPOBLADOR` o `SERVICIO`. Para agregar un nuevo alias basta con editar esa
lista, sin tocar el resto del código.

---

## 🧭 Módulos

- **Dashboard principal** — KPIs generales, volumen por módulo, exportación consolidada.
- **1 · Pacientes Transfundidos (PT)** — por servicio, ranking, heatmap y cruce con RAI.
- **2 · Pacientes Atendidos (PA)** — por servicio, top 10, tabla dinámica.
- **3 · Descartes (DT)** — por servicio y tipo, treemap, sankey (hemocomponente → motivo).
- **4 · Ingresos (I)** — por banco de sangre y tipo, sunburst.
- **5 · Transfusiones (T)** — por servicio, heatmap servicio × hemocomponente.
- **6 · Pruebas Cruzadas (PC)** — compatibles vs. incompatibles, barras apiladas.
- **7 · RAI Positivo** — por servicio, porcentajes y relación con PT.
- **8 · Solicitudes de Unidades (SU)** — por servicio y tipo, treemap, sunburst.
- **9 · Análisis Comparativo** — comparación entre servicios, tops, pacientes con
  más transfusiones e indicadores porcentuales.

Todos los módulos comparten **filtros globales** (fecha, servicio, hemocomponente,
banco de sangre y buscador de paciente) en la barra lateral.

---

## ☁️ Despliegue en Streamlit Community Cloud

1. Sube este proyecto a un repositorio de **GitHub**.
2. Entra a [share.streamlit.io](https://share.streamlit.io) y conecta el repo.
3. Indica `app.py` como archivo principal.
4. Streamlit instalará `requirements.txt` automáticamente y publicará la app.

> ⚠️ **Datos de pacientes:** el `.gitignore` excluye los archivos de datos
> (`data/*.csv`, `*.txt`, etc.) para evitar subir información sensible a GitHub.
> Los archivos se cargan siempre desde la interfaz.

---

## 🏗️ Estructura del proyecto

```
app_banco_sangre/
├── app.py                     # Dashboard principal + carga de archivos
├── pages/                     # Un archivo por módulo (Streamlit multipage)
│   ├── 1_🩸_Pacientes_Transfundidos.py
│   ├── 2_👥_Pacientes_Atendidos.py
│   ├── 3_🗑️_Descartes.py
│   ├── 4_📥_Ingresos.py
│   ├── 5_💉_Transfusiones.py
│   ├── 6_🧪_Pruebas_Cruzadas.py
│   ├── 7_⚠️_RAI_Positivo.py
│   ├── 8_📋_Solicitudes_Unidades.py
│   └── 9_📈_Análisis_Comparativo.py
├── utils/
│   ├── config.py              # Paleta, alias de columnas y metadatos de datasets
│   ├── data_loader.py         # Lectura robusta + mapeo dinámico de columnas
│   ├── filters.py             # Filtros globales
│   ├── charts.py              # Helpers Plotly (barras, pie, heatmap, treemap, sankey…)
│   ├── kpis.py                # Tarjetas KPI
│   ├── exporters.py           # Exportación Excel / PDF / PNG
│   └── ui.py                  # Scaffolding común de páginas
├── data/                      # (vacío) para datos locales — ignorado por git
├── assets/                    # Recursos estáticos
├── .streamlit/config.toml     # Tema visual
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🛠️ Tecnologías

Pandas · Plotly · Streamlit · OpenPyXL · ReportLab · Kaleido

---

## 📌 Notas de mantenimiento

- **Nuevos alias de columnas:** editar `utils/config.py → FIELD_ALIASES`.
- **Nuevo dataset/módulo:** añadir la entrada en `DATASETS` y crear el archivo en `pages/`.
- **Medida de "unidades":** `utils/data_loader.unit_series` usa la columna de
  cantidad si aporta valores > 0; de lo contrario cuenta una unidad por fila.
```
