from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict

from ekilibria.ml_logic.predict import predict_weektype, predict_burnoutindex, expected_features

# Definición del esquema del input
class FeaturesInput(BaseModel):
    features: Dict[str, float]

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
    return {"week_type": prediction1, "burnout_index": prediction2}
