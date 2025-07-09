from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Union

from ekilibria.ml_logic.predict import predict_weektype, predict_burnoutindex, compute_burnout_contributions, expected_features

# Definición del esquema del input
# class FeaturesInput(BaseModel):
#     features: Dict[str, float]

class FeaturesInput(BaseModel):
    features: List[Dict[str, Union[int, float, str]]]

# Crear la app FastAPI
app = FastAPI()

@app.get("/")
def root():
    return {"message": "Servidor levantado. API activa"}

@app.post("/predict")
def predict(input_data: FeaturesInput):
    features_dict = input_data.features

    # Verificamos que estén todas las features esperadas
    missing = [feat for feat in expected_features if feat not in features_dict]
    if missing:
        return {"error": f"Faltan las siguientes features: {missing}"}

    # Realizar la predicción
    prediction1 = predict_weektype(features_dict)
    prediction2 = predict_burnoutindex(features_dict)

    #Calcular la contibución de cada feature
    explanations = compute_burnout_contributions(features_dict)

    return {"week_type": prediction1,
            "burnout_index": prediction2,
            "contributions": explanations}

@app.post("/predict_new")
def predict_new(input_data: FeaturesInput):
    semanas = input_data.features  # Ahora es una lista de dicts
    resultados = []

    for semana in semanas:
        # Verificamos que estén todas las features esperadas
        features_dict = semana.copy()  # No modificar el original
        missing = [feat for feat in expected_features if feat not in features_dict]
        if missing:
            resultados.append({
                "fecha_desde": semana.get("fecha_desde"),
                "fecha_hasta": semana.get("fecha_hasta"),
                "error": f"Faltan las siguientes features: {missing}"
            })
            continue

        # Realizar predicciones
        prediction1 = predict_weektype(features_dict)
        prediction2 = predict_burnoutindex(features_dict)
        explanations = compute_burnout_contributions(features_dict)

        resultados.append({
            "fecha_desde": semana.get("fecha_desde"),
            "fecha_hasta": semana.get("fecha_hasta"),
            "week_type": prediction1,
            "burnout_index": prediction2,
            "contributions": explanations
        })

    return {"resultados": resultados}
