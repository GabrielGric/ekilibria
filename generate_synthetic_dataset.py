import os
import random
import json
import numpy as np
import pandas as pd
from pathlib import Path

# ========================
# CONFIGURACIÓN GENERAL
# ========================

N_ROWS = 1000
TYPICAL_RATIO = 0.6
AMBIGUOUS_RATIO = 0.3
COHERENT_RATIO = 0.1

# Ruta absoluta al directorio actual (donde está este script)
BASE_DIR = Path(__file__).resolve().parent
RAW_DATA_PATH = BASE_DIR / "raw_data"
RAW_DATA_PATH.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = RAW_DATA_PATH / "synthetic_burnout_dataset.csv"

# ========================
# UMBRALES POR CLASE
# ========================

CLASS_THRESHOLDS = {
    "semana_saludable": {
        "num_events": (0, 9),
        "num_events_outside_hours": (0, 1),
        "total_meeting_hours": (0, 9),
        "avg_meeting_duration": (0, 44),
        "meetings_weekend": (0, 0),
        "emails_sent": (0, 10),
        "emails_sent_out_of_hours": (0, 2),
        "docs_created": (0, 2),
        "docs_edited": (0, 3),
        "num_meetings_no_breaks": (0, 0),
        "emails_received": (0, 20),
        "num_overlapping_meetings": (0, 0)
    },
    "semana_carga_aceptable": {
        "num_events": (10, 14),
        "num_events_outside_hours": (2, 3),
        "total_meeting_hours": (10, 14),
        "avg_meeting_duration": (45, 59),
        "meetings_weekend": (1, 1),
        "emails_sent": (11, 20),
        "emails_sent_out_of_hours": (3, 5),
        "docs_created": (3, 4),
        "docs_edited": (4, 7),
        "num_meetings_no_breaks": (1, 2),
        "emails_received": (21, 35),
        "num_overlapping_meetings": (1, 1)
    },
    "semana_carga_excesiva": {
        "num_events": (15, 24),
        "num_events_outside_hours": (4, 5),
        "total_meeting_hours": (15, 24),
        "avg_meeting_duration": (60, 74),
        "meetings_weekend": (2, 2),
        "emails_sent": (21, 30),
        "emails_sent_out_of_hours": (6, 8),
        "docs_created": (5, 9),
        "docs_edited": (8, 14),
        "num_meetings_no_breaks": (3, 5),
        "emails_received": (46, 50),
        "num_overlapping_meetings": (2, 3)
    },
    "semana_agotamiento_extremo": {
        "num_events": (25, 40),
        "num_events_outside_hours": (6, 10),
        "total_meeting_hours": (25, 40),
        "avg_meeting_duration": (75, 120),
        "meetings_weekend": (3, 5),
        "emails_sent": (31, 50),
        "emails_sent_out_of_hours": (9, 15),
        "docs_created": (10, 15),
        "docs_edited": (15, 20),
        "num_meetings_no_breaks": (6, 10),
        "emails_received": (51, 80),
        "num_overlapping_meetings": (4, 10)
    }
}

# ========================
# PESOS PARA BURNOUT INDEX
# ========================

# FEATURE_WEIGHTS = {
#     "num_events": 0.7,
#     "num_events_outside_hours": 1.2,
#     "total_meeting_hours": 1.0,
#     "avg_meeting_duration": 0.5,
#     "meetings_weekend": 1.0,
#     "emails_sent": 0.8,
#     "emails_sent_out_of_hours": 1.3,
#     "docs_created": 0.6,
#     "docs_edited": 0.6,
#     "num_meetings_no_breaks": 1.0,
#     "emails_received": 0.7,
#     "num_overlapping_meetings": 1.1
# }

# Nuevo diccionario de pesos el valor total es 10.0
# Cada feature tiene un peso que refleja su impacto relativo en el índice de burnout
# Los pesos están normalizados para que la suma total sea 10.0
# Estos valores son arbitrarios y pueden ajustarse según la importancia relativa de cada feature.
FEATURE_WEIGHTS = {
    "meetings_weekend": 5.002,
    "num_events_outside_hours": 2.501,
    "emails_sent_out_of_hours": 1.25,
    "num_overlapping_meetings": 0.625,
    "num_meetings_no_breaks": 0.313,
    "num_events": 0.156,
    "emails_received": 0.078,
    "emails_sent": 0.039,
    "total_meeting_hours": 0.020,
    "avg_meeting_duration": 0.010,
    "docs_edited": 0.005,
    "docs_created": 0.002
}

CLASS_INDEX_RANGES = {
    "semana_saludable": (1.0, 3.0),
    "semana_carga_aceptable": (3.1, 5.0),
    "semana_carga_excesiva": (5.1, 7.5),
    "semana_agotamiento_extremo": (7.6, 10.0)
}

# ========================
# FUNCIONES
# ========================

def sample_feature(feature, week_type):
    lo, hi = CLASS_THRESHOLDS[week_type][feature]
    return round(random.uniform(lo, hi), 2)

# def determine_week_type_from_features(row):
#     counts = {key: 0 for key in CLASS_THRESHOLDS.keys()}
#     for feature, value in row.items():
#         for week_type, thresholds in CLASS_THRESHOLDS.items():
#             lo, hi = thresholds[feature]
#             if lo <= value <= hi:
#                 counts[week_type] += 1
#                 break
#     return random.choices(list(counts.keys()), weights=[counts[k] for k in counts])[0]

def determine_week_type_from_features(row):
    scores = {key: {"count": 0, "weight_sum": 0.0} for key in CLASS_THRESHOLDS.keys()}

    for feature, value in row.items():
        for week_type, thresholds in CLASS_THRESHOLDS.items():
            lo, hi = thresholds[feature]
            if lo <= value <= hi:
                scores[week_type]["count"] += 1
                scores[week_type]["weight_sum"] += FEATURE_WEIGHTS.get(feature, 0.0)
                break

    # Calcular score final como cantidad * suma de pesos
    final_scores = {
        k: v["count"] * v["weight_sum"]
        for k, v in scores.items()
    }

    return random.choices(
        population=list(final_scores.keys()),
        weights=list(final_scores.values()),
        k=1
    )[0]

# def calculate_burnout_index(row, week_type, mode):
#     lo, hi = CLASS_INDEX_RANGES[week_type]
#     if mode == "deterministic":
#         return round(random.uniform(lo, hi), 2)
#     elif mode == "formula":
#         max_weights = sum(FEATURE_WEIGHTS.values())
#         norm = sum(min(row[f]/(CLASS_THRESHOLDS["semana_agotamiento_extremo"][f][1] or 1), 1) * w
#                    for f, w in FEATURE_WEIGHTS.items()) / max_weights
#         noise = np.random.normal(loc=0.0, scale=0.2)
#         return round(min(max(lo, norm * (hi - lo) + lo + noise), hi), 2)
#     elif mode == "random":
#         return round(random.uniform(lo, hi), 2)

def calculate_burnout_index(row, week_type, mode):
    """
    Calcula el índice de burnout en función del tipo de semana y el modo de cálculo seleccionado.

    Parámetros:
    - row: dict con las features para una semana.
    - week_type: tipo de semana (clave de CLASS_INDEX_RANGES).
    - mode: puede ser 'deterministic', 'deterministic_con_ruido' o 'random'.

    Retorna:
    - Índice de burnout (float redondeado a 2 decimales), siempre dentro del rango correspondiente al tipo de semana.
    """

    lo, hi = CLASS_INDEX_RANGES[week_type]

    if mode == "deterministic":
        # Calcula un índice proporcional sin ruido
        max_weights = sum(FEATURE_WEIGHTS.values())
        norm = sum(
            min(row[f] / (CLASS_THRESHOLDS["semana_agotamiento_extremo"][f][1] or 1), 1) * w
            for f, w in FEATURE_WEIGHTS.items()
        ) / max_weights
        return round(min(max(lo, norm * (hi - lo) + lo), hi), 2)

    elif mode == "deterministic_con_ruido":
        # Igual que el modo determinista pero agrega ruido gaussiano
        max_weights = sum(FEATURE_WEIGHTS.values())
        norm = sum(
            min(row[f] / (CLASS_THRESHOLDS["semana_agotamiento_extremo"][f][1] or 1), 1) * w
            for f, w in FEATURE_WEIGHTS.items()
        ) / max_weights
        noise = np.random.normal(loc=0.0, scale=0.2)
        return round(min(max(lo, norm * (hi - lo) + lo + noise), hi), 2)

    elif mode == "random":
        # Elige un valor aleatorio dentro del rango correspondiente al tipo de semana
        return round(random.uniform(lo, hi), 2)

    else:
        raise ValueError(f"Modo de cálculo desconocido: '{mode}'")

# ========================
# GENERACIÓN DE FILAS
# ========================

def generate_rows():
    rows = []
    for i in range(N_ROWS):
        if i < N_ROWS * TYPICAL_RATIO:
            base_type = random.choice(list(CLASS_THRESHOLDS.keys()))
            features = {}
            primary_features = random.sample(list(CLASS_THRESHOLDS[base_type].keys()), 6)
            for feature in CLASS_THRESHOLDS[base_type]:
                assigned_type = base_type if feature in primary_features else random.choice(list(CLASS_THRESHOLDS.keys()))
                features[feature] = sample_feature(feature, assigned_type)
            final_week = determine_week_type_from_features(features)
        elif i < N_ROWS * (TYPICAL_RATIO + AMBIGUOUS_RATIO):
            # Ambiguous: completamente aleatorio
            features = {f: sample_feature(f, random.choice(list(CLASS_THRESHOLDS.keys()))) for f in FEATURE_WEIGHTS}
            final_week = determine_week_type_from_features(features)
        else:
            # Coherente: todas las variables de un solo tipo
            base_type = random.choice(list(CLASS_THRESHOLDS.keys()))
            features = {f: sample_feature(f, base_type) for f in FEATURE_WEIGHTS}
            final_week = base_type

        # Burnout index con modo aleatorio controlado
        mode = random.choices(["deterministic", "deterministic_con_ruido", "random"], weights=[0.1, 0.6, 0.3])[0]
        burnout_index = calculate_burnout_index(features, final_week, mode)

        row = features.copy()
        row["tipo_de_semana"] = final_week
        row["burnout_index"] = burnout_index
        rows.append(row)
    return rows

# ========================
# MAIN
# ========================

if __name__ == "__main__":
    dataset = generate_rows()
    print(f"Filas generadas: {len(dataset)}")
    df = pd.DataFrame(dataset)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Dataset generado con éxito: {OUTPUT_FILE}")
