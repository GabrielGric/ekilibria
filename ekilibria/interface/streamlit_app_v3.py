import streamlit as st
import requests
import json
import datetime
import asyncio
import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
from ekilibria.google_suite.services.extract_features import (
    extract_all_features, save_features_to_json, load_only_week_features
)
from ekilibria.google_suite.auth.authenticate_google_user import authenticate_google_user
from ekilibria.microsoft_suite.api_microsoft_org import get_microsoft_graph_api_token, get_data

# Título principal
st.set_page_config(layout="wide")
st.title("🧠 Burnout Dashboard 🔥 Resultado de la semana")

# Autenticación
st.sidebar.header("🔐 Autenticación")
st.session_state.setdefault("auth_provider", None)
st.session_state.setdefault("burnout_index", None)

auth_provider = st.sidebar.radio("Seleccioná proveedor", ["Google", "Microsoft"])

if st.sidebar.button("🔐 Autenticar"):
    try:
        if auth_provider == "Google":
            token_path, user_email = authenticate_google_user()
            st.session_state.token_path = token_path
            st.session_state.user_email = user_email
            st.session_state.auth_provider = "Google"
            st.success(f"✅ Usuario autenticado con Google: {user_email}")
        else:
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop()
            user, client = loop.run_until_complete(get_microsoft_graph_api_token())
            st.session_state.client = client
            st.session_state.loop = loop
            st.session_state.auth_provider = "Microsoft"
            st.success(f"✅ Usuario autenticado con Microsoft: {user.display_name} ({user.mail})")
    except Exception as e:
        st.error(f"❌ Error en la autenticación: {e}")

# Rango temporal
st.sidebar.header("📅 Rango temporal")
periodo = st.sidebar.radio("Seleccionar periodo", ["Última semana", "Último mes", "Último año"])

hoy = datetime.date.today()
if periodo == "Última semana":
    fecha_desde = hoy - datetime.timedelta(days=7)
elif periodo == "Último mes":
    fecha_desde = hoy - datetime.timedelta(days=30)
else:
    fecha_desde = hoy - datetime.timedelta(days=365)
fecha_hasta = hoy

# Convertir a datetime
try:
    fecha_desde = datetime.datetime.combine(fecha_desde, datetime.time.min)
    fecha_hasta = datetime.datetime.combine(fecha_hasta, datetime.time.max)
except:
    st.error("❌ Error extrayendo datos: fecha_desde y fecha_hasta deben ser objetos datetime.datetime")
    st.stop()

# Botón de ver datos
if st.sidebar.button("📊 Ver datos"):
    try:
        if st.session_state.auth_provider == "Google":
            token_path = st.session_state.token_path
            result = extract_all_features(token_path, fecha_desde, fecha_hasta)
            json_path = save_features_to_json(result, token_path, fecha_desde, fecha_hasta)
            features = load_only_week_features(json_path)
        elif st.session_state.auth_provider == "Microsoft":
            loop = st.session_state.loop
            client = st.session_state.client
            features = loop.run_until_complete(get_data(client))
        else:
            st.warning("⚠️ Primero debés autenticarte.")
            st.stop()

        json_payload = {"features": features}
        response = requests.post("http://127.0.0.1:8000/predict", json=json_payload)

        if response.status_code == 200:
            response_data = response.json()
            burnout_index = response_data.get("burnout_index", 0)
            week_type = response_data.get("week_type", 0)
            st.session_state.burnout_index = burnout_index

            col1, col2, col3 = st.columns([1.2, 1, 1])

            with col1:
                st.markdown("## Burnout Index")
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = burnout_index,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': ""},
                    gauge = {
                        'axis': {'range': [0, 5]},
                        'bar': {'color': "#5e5e5e"},
                        'steps' : [
                            {'range': [0, 1.5], 'color': "#c7f2a4"},
                            {'range': [1.5, 3], 'color': "#f9e79f"},
                            {'range': [3, 5], 'color': "#f1948a"}
                        ]
                    }
                ))
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("## 🧾 Variables de la semana")
                df = pd.DataFrame(list(features.items()), columns=["Feature", "Valor"])
                st.dataframe(df)

            with col3:
                st.markdown("## 📊 Incidencia estimada")
                importances = response_data.get("importances", {})
                if importances:
                    imp_df = pd.DataFrame(list(importances.items()), columns=["features", "importancia"])
                    fig_bar, ax = plt.subplots()
                    sns.barplot(x="importancia", y="features", data=imp_df, ax=ax)
                    st.pyplot(fig_bar)
                else:
                    st.warning("No se recibieron importancias desde el modelo.")

            st.markdown("## 📈 Evolución temporal del burnout")
            if "burnout_history" in response_data:
                history = response_data["burnout_history"]
                df_hist = pd.DataFrame(history)
                fig_line = go.Figure()
                fig_line.add_trace(go.Scatter(
                    x=df_hist["date"],
                    y=df_hist["burnout_index"],
                    mode='lines+markers'
                ))
                fig_line.update_layout(title="Burnout Index en el tiempo", xaxis_title="Fecha", yaxis_title="Burnout Index")
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("No hay historial de burnout disponible.")

            # Etiqueta descriptiva
            labels = {
                0: "Semana saludable 🌱",
                1: "Carga aceptable ⚖️",
                2: "Carga excesiva 🚨",
                3: "Riesgo de burnout 🔥"
            }
            st.success(f"🧠 Tipo de semana: {labels.get(week_type, 'Desconocido')}")

        else:
            st.error("❌ Error al predecir con FastAPI")

    except FileNotFoundError as e:
        st.error(f"❌ Error extrayendo datos: {e}")
    except Exception as e:
        st.error(f"❌ Error general: {e}")
