import numpy as np
import joblib
from pathlib import Path

# Ruta a los modelos
MODEL1_PATH = Path(__file__).resolve().parent.parent.parent / "models" / "weektype_predictor.joblib"
MODEL2_PATH = Path(__file__).resolve().parent.parent.parent / "models" / "burnout_index_predictor.joblib"

if not MODEL1_PATH.exists():
    raise FileNotFoundError(f"El modelo de clasificación no se encuentra en la ruta: {MODEL1_PATH}")

if not MODEL2_PATH.exists():
    raise FileNotFoundError(f"El modelo de regresión no se encuentra en la ruta: {MODEL2_PATH}")

model1 = joblib.load(MODEL1_PATH)
model2 = joblib.load(MODEL2_PATH)

# Orden esperado de features (el mismo del entrenamiento)
expected_features = [
    'num_events',
    'num_events_outside_hours',
    'total_meeting_hours',
    'avg_meeting_duration',
    'meetings_weekend',
    'emails_sent',
    'emails_sent_out_of_hours',
    'docs_created',
    'docs_edited',
    'num_meetings_no_breaks',
    'emails_received',
    'num_overlapping_meetings'
]

def predict_weektype(features_dict: dict) -> int:
    """Devuelve el tipo de semana predicho (0 a 3) a partir del dict de features."""

    # Verificamos que estén todos los features esperados
    missing = [feat for feat in expected_features if feat not in features_dict]
    if missing:
        raise ValueError(f"Faltan las siguientes features: {missing}")

    # Reordenar los valores en el orden esperado
    X = np.array([[features_dict[feat] for feat in expected_features]])

    # Predicción
    prediction = model1.predict(X)
    return int(prediction[0])

def predict_burnoutindex(features_dict: dict) -> int:
    """Devuelve el burnout index predicho (1 a 10) a partir del dict de features."""

    # Verificamos que estén todos los features esperados
    missing = [feat for feat in expected_features if feat not in features_dict]
    if missing:
        raise ValueError(f"Faltan las siguientes features: {missing}")

    # Reordenar los valores en el orden esperado
    X = np.array([[features_dict[feat] for feat in expected_features]])

    # Predicción
    prediction = model2.predict(X)
    return prediction[0]
