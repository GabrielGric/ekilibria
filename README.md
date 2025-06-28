# 🧠 Ekilibria – Detección temprana de burnout

Proyecto final del bootcamp de Data Science: sistema de detección no invasiva de burnout basado en rutinas digitales (Calendar, Gmail, Drive).

## 🚀 Cambios incluidos en esta versión (commit del 28/06/2025)

**🔧 Estructura general:**
- Reorganización del código en paquete Python: `ekilibria/` contiene toda la lógica.
- Inclusión de `Makefile` y `setup.py` para facilitar instalación y automatización.

**🧠 Machine Learning:**
- Modelo entrenado con Random Forest (`models/weektype_predictor.joblib`).
- Clasificación del tipo de semana en 4 categorías.

**🧪 Dataset sintético:**
- Dataset generado en `raw_data/synthetic_burnout_dataset.csv`.

**⚙️ API y Frontend:**
- FastAPI con endpoint `/predict` operativo.
- Interfaz de usuario en Streamlit conectada a FastAPI.

**🔐 Autenticación y extracción de features:**
- Conexión con APIs de Google Calendar, Drive y Gmail para extracción automática.
- Requiere archivos de credenciales en `google_suite/auth/` (no subidos al repo).

**📦 Configuración:**
- `.gitignore` actualizado (excluye notebooks, credenciales y carpetas temporales).
- Manejo de variables sensibles mediante `.env`.

---
