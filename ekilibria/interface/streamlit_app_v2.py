import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import datetime
import asyncio
import requests
from pathlib import Path

# Módulos propios
from ekilibria.google_suite.auth.authenticate_google_user import authenticate_google_user
from ekilibria.google_suite.services.extract_features import extract_all_features
from ekilibria.microsoft_suite.api_microsoft_org import get_microsoft_graph_api_token, get_data

# =========================
# Configurar la página
# =========================
st.set_page_config(page_title="Burnout Dashboard", layout="wide")

st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        .element-container {
            margin-bottom: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

# =========================
# Inicializar variables
# =========================
if "burnout_index" not in st.session_state:
    st.session_state.burnout_index = 0
if "feature_values" not in st.session_state:
    st.session_state.feature_values = [0, 0, 8.62, 0, 0, 0]
if "history" not in st.session_state:
    st.session_state.history = [1.2, 1.4, 1.7, 1.9, 2.2, 3.1, 2.1, 2.4, 2.7, 3.0]

features = [
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
st.session_state.feature_values = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

st.session_state.importances = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# =======================
# 🧩 Panel lateral
# =======================
with st.sidebar:
    st.markdown("### 🔐 Autenticación")
    proveedor = st.radio("Seleccioná proveedor", ["Google", "Microsoft"], index=0)
    st.session_state.proveedor = proveedor

    if st.button("🔐 Autenticar"):
        if proveedor == "Google":
            try:
                token_path, user_email = authenticate_google_user()
                st.session_state.token_path = token_path
                st.session_state.user_email = user_email
                st.success(f"✅ Usuario autenticado: {user_email}")
            except Exception as e:
                st.error(f"❌ Error en la autenticación con Google: {e}")
        elif proveedor == "Microsoft":
            try:
                asyncio.set_event_loop(asyncio.new_event_loop())
                loop = asyncio.get_event_loop()
                user, client = loop.run_until_complete(get_microsoft_graph_api_token())
                st.session_state.loop = loop
                st.session_state.client = client
                st.success(f"✅ Usuario autenticado con Microsoft como: {user.display_name} ({user.mail})")
            except Exception as e:
                st.error(f"❌ Error en la autenticación con Microsoft: {e}")

    st.markdown("### 🗓️ Rango temporal")
    periodo = st.radio("Seleccionar periodo", ["Última semana", "Último mes", "Último año"], index=2)
    st.session_state.periodo = periodo

    if st.button("📊 Ver datos"):
        try:
            fecha_hasta = datetime.datetime.now()
            if periodo == "Última semana":
                fecha_desde = fecha_hasta - datetime.timedelta(days=7)
            elif periodo == "Último mes":
                fecha_desde = fecha_hasta - datetime.timedelta(days=30)
            else:
                fecha_desde = fecha_hasta - datetime.timedelta(days=365)

            if proveedor == "Google":
                if "token_path" not in st.session_state:
                    st.warning("⚠️ Primero debes autenticarte con Google.")
                else:
                    result = extract_all_features(
                        st.session_state.token_path,
                        fecha_desde,
                        fecha_hasta
                    )
                    st.success("✅ Datos extraídos desde Google.")
                    result = {feature: result.get(feature, 0) for feature in features}
                    st.session_state.feature_values = list(result.values())

            elif proveedor == "Microsoft":
                if "client" not in st.session_state:
                    st.warning("⚠️ Primero debes autenticarte con Microsoft.")
                else:
                    loop = st.session_state.loop
                    client = st.session_state.client
                    result = loop.run_until_complete(get_data(client))
                    st.success("✅ Datos extraídos desde Microsoft.")
                    # order the result to match the features
                    result = {feature: result.get(feature, 0) for feature in features}
                    st.session_state.feature_values = list(result.values())

            else:
                st.warning("⚠️ Proveedor no reconocido.")

            if st.session_state.feature_values != [0] * len(features):
                # Get index from api
                json = { "features": result } if isinstance(result, dict) else { "features": {} }

                response = requests.post("http://127.0.0.1:8000/predict", json=json)
                if response.status_code == 200:
                    prediction = response.json()
                    st.session_state.burnout_index = prediction.get("burnout_index", 1.6)
                    st.session_state.history.append(st.session_state.burnout_index)
                    st.session_state.importances = prediction.get("contributions", [0] * len(features))

        except Exception as e:
            st.error(f"❌ Error extrayendo datos: {e}")

# =======================
# 🧠 Título
# =======================
st.markdown("## 🧠 Burnout Dashboard 🔥 Resultado de la semana")

# =======================
# 📊 Gráficos principales
# =======================
col1, col2, col3 = st.columns([1.2, 1.3, 1.3], gap="large")

with col1:
    st.markdown("#### Burnout Index")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=st.session_state.burnout_index,
        gauge={
            'axis': {'range': [0, 10]},
            'bar': {'color': "darkgray"},
            'steps': [
                {'range': [0, 2.5], 'color': "green"},
                {'range': [2.5, 5], 'color': "yellow"},
                {'range': [5, 7.5], 'color': "orange"},
                {'range': [7.5,10], 'color': "red"}
            ],
        },
        number={'font': {'size': 48}},
        domain={'x': [0, 1], 'y': [0, 1]}
    ))
    fig.update_layout(height=220, margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### 🧾 Variables de la semana")
    df = pd.DataFrame({"Feature": features, "Valor": st.session_state.feature_values})
    st.dataframe(df, hide_index=True, use_container_width=True)

with col3:
    st.markdown("### Incidencia estimada")
    fig2, ax = plt.subplots(figsize=(6, 8))
    ax.barh(st.session_state.importances.keys(), st.session_state.importances.values(), color='skyblue')
    ax.set_xlabel("Importancia")
    ax.set_ylabel("Features")
    st.pyplot(fig2)

# =======================
# 📈 Evolución temporal
# =======================
if st.session_state.periodo in ["Último mes", "Último año"]:
    st.markdown("#### 📈 Evolución temporal del burnout")
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=list(range(len(st.session_state.history))),
        y=st.session_state.history,
        mode='lines+markers',
        line=dict(color='royalblue'),
        marker=dict(size=8),
        name="Burnout Index",
        hovertemplate='Semana %{x}<br>Burnout Index %{y:.2f}<extra></extra>'
    ))
    fig3.update_layout(
        xaxis_title='Semana',
        yaxis_title='Burnout Index',
        margin=dict(l=40, r=20, t=20, b=40),
        height=300,
        template='simple_white'
    )
    st.plotly_chart(fig3, use_container_width=True)
