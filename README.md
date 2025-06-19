# 📊 Synthetic Burnout Dataset

Este repositorio contiene una rutina de generación automática de datos sintéticos para modelar distintos niveles de ago
tamiento laboral semanal (`burnout_index`), con base en señales digitales del entorno de trabajo (calendario, correo, documentos).

---

### 🔍 ¿Qué incluye este dataset?

- `10` variables semanales (`features`) que simulan el comportamiento digital:
  - Eventos, mails, documentos, reuniones, etc.
- `1` índice continuo (`burnout_index`) entre `1.0` y `10.0`.
- `1` etiqueta categórica (`tipo_semana`) que clasifica la semana en:
  1. Semana saludable
  2. Carga aceptable
  3. Carga excesiva
  4. Agotamiento extremo

---

### 🧠 ¿Cómo se generó?

- Cada fila representa una semana laboral simulada.
- Se elige aleatoriamente un tipo de semana (`tipo_semana`).
- Se generan 7 variables dentro del rango esperado y 3 fuera.
- Se calcula el `burnout_index` aplicando una fórmula ponderada.
- Si el valor cae en el rango correcto para esa semana, se guarda.

> Ver código fuente: [`generate_synthetic_dataset.py`](generate_synthetic_dataset.py)

---

### 📂 Archivos incluidos

| Archivo                          | Descripción                                   |
|----------------------------------|-----------------------------------------------|
| `generate_synthetic_dataset.py` | Script para generar el dataset CSV            |
| `ekilibria_synthetic_dataset.ipynb` | Notebook con documentación y validaciones |
| `requirements.txt`              | Dependencias mínimas (solo `pandas`, `numpy`) |
| `README.md`                     | Este archivo                                  |

---

### 🔗 Referencia de diseño

Los rangos por variable, pesos y categorías están documentados en esta hoja de diseño colaborativa:
👉 [Hoja de diseño en Google Sheets](https://docs.google.com/spreadsheets/d/1XGnYfmlciyIsoUXT2XwYzwOj1E_ziqLzvIS85oTRTDE/edit#gid=1806434176)

---

### 🧪 Uso sugerido

Este dataset es ideal para entrenar modelos de Machine Learning supervisado de clasificación, por ejemplo:

- Predecir `tipo_semana` a partir de las 10 variables.
- Analizar la importancia relativa de cada feature.
- Evaluar técnicas de clustering, PCA, etc.

---

### ✨ Versión actual: `1.0`
