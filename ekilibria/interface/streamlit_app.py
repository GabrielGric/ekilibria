import streamlit as st
import requests
import json
import datetime
import asyncio
from ekilibria.google_suite.services.extract_features import extract_all_features
from ekilibria.google_suite.auth.authenticate_google_user import authenticate_google_user
from ekilibria.google_suite.services.extract_features import save_features_to_json
from ekilibria.google_suite.services.extract_features import load_only_week_features
from ekilibria.microsoft_suite.api_microsoft_org import get_microsoft_graph_api_token, get_data
from ekilibria.microsoft_suite.time_zones import build_windows_to_iana_map

st.title("🧠 Predicción del tipo de semana")
st.write("Esta app predice tu tipo de semana en base a tu actividad digital.")

# Autenticación
st.subheader("🔐 Paso 1: Autenticar con Google Suite o Microsoft Suite")

if st.button("Autenticar con Google Suite"):
    try:
        token_path, user_email = authenticate_google_user() # Esta función debe abrir el navegador y guardar el token
        st.session_state.token_path = token_path
        st.session_state.user_email = user_email
        st.success(f"✅ Usuario autenticado: {user_email}")
    except Exception as e:
        st.error(f"❌ Error en la autenticación: {e}")

if st.button("Autenticar con Microsoft Suite"):
    try:
        st.write("Autenticando con Microsoft Suite...")

        # Create a new event async loop for Streamlit
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        user, client = loop.run_until_complete(get_microsoft_graph_api_token())  # Esta función debe abrir el navegador y guardar el token

        st.session_state.loop = loop
        st.session_state.client = client
        st.success(f"✅ Usuario autenticado con Microsoft Suite como: {user.display_name} ({user.mail})")
    except Exception as e:
        st.error(f"❌ Error en la autenticación: {e}")


# Paso 2: Predicción
st.subheader("🧠 Paso 2: Calcular tipo de semana")

col1, col2 = st.columns(2)
with col1:
    fecha_desde = st.date_input("Desde", datetime.date.today())
with col2:
    fecha_hasta = st.date_input("Hasta", datetime.date.today())


if st.button("Calcular tipo de semana"):
    if st.session_state.get("token_path"):
        try:
            # Asegurate que el token esté en el session_state
            if "token_path" not in st.session_state:
                st.error("⚠️ Primero debés autenticarte con Google.")
            else:
                token_path = st.session_state.token_path
                user_email = st.session_state.user_email

                # Convertir date → datetime
                fecha_desde = datetime.datetime.combine(fecha_desde, datetime.time.min)
                fecha_hasta = datetime.datetime.combine(fecha_hasta, datetime.time.min)

                st.write("token_path", token_path)
                st.write("fecha_desde", fecha_desde)
                st.write("fecha_hasta", fecha_hasta)

                # 1. Extraer todos los features
                result = extract_all_features(token_path, fecha_desde, fecha_hasta)
                st.write("Resultado de extract_all_features", result)

                # 2. Guardar JSON completo
                json_path = save_features_to_json(result, token_path, fecha_desde, fecha_hasta)
                st.success(f"✅ JSON guardado en: {json_path}")

                # 3. Cargar solo los 12 features requeridos para predicción
                st.write("json_path", json_path)
                features = load_only_week_features(json_path)

                json = {"features": features}

                st.write("Payload enviado a FastAPI:", json)

                response = requests.post("http://127.0.0.1:8000/predict", json=json)

                if response.status_code == 200:
                    st.write("Respuesta completa:", response.json())
                    pred = response.json()["week_type"]

                    # Mapeo de etiquetas
                    labels = {
                        0: "Semana saludable 🌱",
                        1: "Carga aceptable ⚖️",
                        2: "Carga excesiva 🚨",
                        3: "Riesgo de burnout 🔥"
                    }
                    st.success(f"🧠 Tipo de semana: {labels.get(pred, 'Desconocido')}")
                else:
                    st.error("❌ Error al predecir con FastAPI")

        except Exception as e:
            st.error(f"❌ Error: {e}")
    elif st.session_state.get("client"):
        st.write("autenticado con Microsoft Suite")
        try:
            client = st.session_state.client
             # Get data from Microsoft Graph API

            loop = st.session_state.loop
            features = loop.run_until_complete(get_data(client))
            st.write("Datos obtenidos de Microsoft Graph API:", features)

            json = {"features": features}

            st.write("Payload enviado a FastAPI:", json)

            ######### prueba
            response = requests.post("http://127.0.0.1:8000/predict", json=json)

            if response.status_code == 200:
                st.write("Respuesta completa:", response.json())
                pred = response.json()["week_type"]

                # 🔹 Extraer ambos valores
                # week_type = pred["week_type"]
                # burnout_index = pred["burnout_index"]

                # 🔹 Mapeo de etiquetas
                labels = {
                    0: "Semana saludable 🌱",
                    1: "Carga aceptable ⚖️",
                    2: "Carga excesiva 🚨",
                    3: "Riesgo de burnout 🔥"
                }

                # 🔹 Mostrar resultados
                # st.success(f"🧠 Tipo de semana: {labels.get(week_type, 'Desconocido')}")
                # st.success(f"💢 Burnout index estimado: {burnout_index:.2f}")
                st.success(f"🧠 Tipo de semana: {labels.get(pred, 'Desconocido')}")
            else:
                st.error("❌ Error al predecir con FastAPI")
            ######### fin de prueba


        except Exception as e:
            st.error(f"❌ Error: {e}")
