# generate_synthetic_dataset.py

import pandas as pd
import numpy as np
import random
import time
from typing import Dict, Tuple

# =============================
# Rango de burnout index por tipo de semana
# =============================
RANGO_INDEX = {
    1: (1.0, 3.0),
    2: (3.1, 5.0),
    3: (5.1, 7.5),
    4: (7.6, 10.0),
}

# =============================
# Pesos por feature para el burnout index
# =============================
PESOS = {
    'num_events': 0.7,
    'num_events_outside_hours': 1.2,
    'total_meeting_hours': 1.0,
    'avg_meeting_duration': 0.5,
    'meetings_weekend': 1.0,
    'emails_sent': 0.8,
    'emails_sent_out_of_hours': 1.3,
    'docs_created': 0.6,
    'docs_edited': 0.6,
    'num_meetings_no_breaks': 1.0
}

# =============================
# Rango por feature según tipo de semana
# =============================
RANGOS: Dict[str, Dict[int, Tuple[int, int]]] = {
    'num_events': {
        1: (0, 9), 2: (10, 14), 3: (15, 24), 4: (25, 40),
    },
    'num_events_outside_hours': {
        1: (0, 1), 2: (2, 3), 3: (4, 5), 4: (6, 10),
    },
    'total_meeting_hours': {
        1: (0, 9), 2: (10, 14), 3: (15, 24), 4: (25, 40),
    },
    'avg_meeting_duration': {
        1: (0, 44), 2: (45, 59), 3: (60, 74), 4: (75, 120),
    },
    'meetings_weekend': {
        1: (0, 0), 2: (1, 1), 3: (2, 2), 4: (3, 6),
    },
    'emails_sent': {
        1: (0, 10), 2: (11, 20), 3: (21, 30), 4: (31, 60),
    },
    'emails_sent_out_of_hours': {
        1: (0, 2), 2: (3, 5), 3: (6, 8), 4: (9, 20),
    },
    'docs_created': {
        1: (0, 2), 2: (3, 4), 3: (5, 9), 4: (10, 20),
    },
    'docs_edited': {
        1: (0, 3), 2: (4, 7), 3: (8, 14), 4: (15, 30),
    },
    'num_meetings_no_breaks': {
        1: (0, 1), 2: (2, 3), 3: (4, 5), 4: (6, 10),
    },
}

# =============================
# Funciones auxiliares
# =============================
def normalizar(valor: float, tipo: int, feature: str) -> float:
    rango = RANGOS[feature][tipo]
    min_val, max_val = rango
    if max_val == min_val:
        return RANGO_INDEX[tipo][0]  # Valor mínimo del burnout index para esa categoría
    escala_min, escala_max = RANGO_INDEX[tipo]
    return escala_min + (valor - min_val) * (escala_max - escala_min) / (max_val - min_val)

def calcular_burnout_index(registro: dict, tipo: int) -> float:
    score_total = 0
    suma_pesos = 0
    for f, val in registro.items():
        if f not in PESOS:
            continue
        peso = PESOS[f]
        score = normalizar(val, tipo, f)
        score_total += peso * score
        suma_pesos += peso
    return round(score_total / suma_pesos, 2)

def generar_valor(f: str, tipo: int, dentro: bool = True) -> int:
    if dentro:
        rango = RANGOS[f][tipo]
    else:
        otros = [t for t in RANGOS[f] if t != tipo]
        tipo_fuera = random.choice(otros)
        rango = RANGOS[f][tipo_fuera]
    return random.randint(*rango)

# =============================
# Generación de registros
# =============================
features = list(PESOS.keys())
NUM_REGISTROS = 1000
REG_POR_TIPO = NUM_REGISTROS // 4
TIPOS = [1, 2, 3, 4]

# Lista de tipos ya mezclada
tipos_lista = [t for t in TIPOS for _ in range(REG_POR_TIPO)]
random.shuffle(tipos_lista)

dataset = []

for tipo in tipos_lista:
    while True:
        dentro = random.sample(features, 7)
        fuera = [f for f in features if f not in dentro]
        registro = {}

        for f in dentro:
            registro[f] = generar_valor(f, tipo, dentro=True)
        for f in fuera:
            registro[f] = generar_valor(f, tipo, dentro=False)

        burnout = calcular_burnout_index(registro, tipo)
        min_idx, max_idx = RANGO_INDEX[tipo]

        if min_idx <= burnout <= max_idx:
            registro["burnout_index"] = burnout
            registro["tipo_semana"] = tipo
            dataset.append(registro)
            print(f"✅ Registro {len(dataset)} de {NUM_REGISTROS} generado para tipo {tipo} (index: {burnout:.2f})")
            time.sleep(0.05)
            break
        else:
            print("🔁 Recalculando...")

# Guardar como CSV
df = pd.DataFrame(dataset)
df.to_csv("raw_data/synthetic_burnout_dataset.csv", index=False)
print("\n✅ Dataset completo generado y guardado en 'raw_data/synthetic_burnout_dataset.csv'")
