# 🔥 ekilibria: Dataset sintético y extracción real de burnout digital

Este repositorio permite generar y recolectar datos semanales sobre agotamiento laboral (`burnout_index`) a partir de señales digitales del entorno de trabajo (calendario, correo, documentos).

---

## 🔍 ¿Qué incluye este proyecto?

- 🧪 **Generación de datos sintéticos**:
  - 12 variables semanales (`features`) simuladas: mails, reuniones, documentos, etc.
  - 1 índice continuo (`burnout_index`) entre `1.0` y `10.0`.
  - 1 etiqueta categórica (`tipo_semana`) con 4 niveles: saludable, carga aceptable, excesiva o agotamiento extremo.

- 🔐 **Extracción real desde APIs de Google Workspace**:
  - `Gmail`: mails enviados, fuera de horario y recibidos.
  - `Calendar`: cantidad de reuniones, duración, solapamientos, eventos fuera de horario, fines de semana, sin pausas.
  - `Drive`: archivos creados o editados por el usuario.

⚠️ **Importante:** los features se calculan sobre los 7 días de la semana (lunes a domingo), salvo que se indique lo contrario.

---

## 🎯 ¿Cómo se genera el `burnout_index`?

Una vez asignado el tipo de semana (`tipo_semana`), se genera el índice mediante una **estrategia mixta** que combina:

| Método                              | Porcentaje |
|-------------------------------------|------------|
| 🎲 Aleatorio acotado al rango       | 60%        |
| 📉 Fórmula probabilística (suave)   | 30%        |
| 🧠 Determinístico puro (lineal)     | 10%        |

Cada método genera un valor continuo dentro del rango correspondiente (por ejemplo, 1.0–3.0 para semanas saludables).

> Ver detalles en el notebook: [`ekilibria_synthetic_dataset.ipynb`](ekilibria_synthetic_dataset.ipynb)

---

## 📊 Variables (features)

Las 12 variables semanales utilizadas, con alta probabilidad de extracción desde Google Workspace:

| Feature                      | Descripción breve                                                    |
|------------------------------|------------------------------------------------------------------------|
| `num_events`                 | Total de eventos en calendario semanal                                 |
| `num_events_outside_hours`  | Eventos fuera del horario laboral (antes de 9h o después de 18h)       |
| `total_meeting_hours`       | Suma total de horas en reuniones                                       |
| `avg_meeting_duration`      | Duración promedio de reuniones                                         |
| `meetings_weekend`          | Cantidad de reuniones sábado y domingo                                 |
| `emails_sent`               | Promedio diario de correos enviados                                    |
| `emails_sent_out_of_hours`  | Correos enviados fuera de horario laboral                              |
| `docs_created`              | Documentos creados en la semana                                        |
| `docs_edited`               | Documentos editados en la semana                                       |
| `num_meetings_no_breaks`    | Reuniones sin pausas de al menos 15 minutos                            |
| `emails_received`           | Promedio diario de correos recibidos (sin spam/promos)                 |
| `num_overlapping_meetings`  | Reuniones que se solapan (sin contarse dos veces con `no_breaks`)      |

---

## 🛠️ Archivos incluidos

| Archivo                             | Descripción                                                         |
|-------------------------------------|---------------------------------------------------------------------|
| `generate_synthetic_dataset.py`     | Rutina para generar datos sintéticos de burnout                    |
| `extract_google_features.py`        | Script para extraer features reales desde Gmail, Calendar y Drive |
| `ekilibria_synthetic_dataset.ipynb` | Notebook con visualizaciones, tests y documentación                |
| `requirements.txt`                  | Librerías necesarias (`pandas`, `numpy`, `google-api-python-client`, etc.) |
| `README.md`                         | Este archivo                                                       |

---

## 🔑 Autenticación Google Workspace

Para usar la extracción real de datos se requiere:

1. Crear credenciales OAuth 2.0 en Google Cloud Console
2. Descargar el `token.json` y colocarlo en la carpeta `google_suite/auth`
3. Definir variables de entorno:
   - `TOKEN_DIR` (path a la carpeta)
   - `TOKEN_FILENAME` (ej: `token.json`)

---

## 🧪 Casos de uso

- Entrenar modelos supervisados para predecir `tipo_semana`
- Analizar la importancia relativa de cada variable
- Evaluar técnicas de clasificación, clustering o PCA
- Comparar datos reales vs. datos sintéticos
- Prototipar soluciones de bienestar organizacional con IA

---

## 🔗 Referencia de diseño

Todos los umbrales por variable, los rangos de cada tipo de semana y la estrategia de generación están documentados en:
👉 [Hoja de diseño en Google Sheets](https://docs.google.com/spreadsheets/d/1XGnYfmlciyIsoUXT2XwYzwOj1E_ziqLzvIS85oTRTDE/edit#gid=1806434176)

---

## ✨ Versión actual: `2.0`

Incluye autenticación, extracción real desde Google y estrategia avanzada de generación sintética.

### 🔐 Autenticación con Google

1. Crea un archivo `.env` a partir del `.env.example`.
2. Coloca allí la ruta a tus credenciales JSON descargadas de Google Cloud Console.
3. Este archivo está ignorado por `.gitignore` y no se subirá al repositorio.
