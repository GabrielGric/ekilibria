from flask import Flask, send_from_directory, jsonify, session, request, url_for, redirect
from authlib.integrations.flask_client import OAuth
import random
import os
import datetime
import requests
import asyncio
import json

from ekilibria.google_suite.services.extract_features import extract_all_features
from ekilibria.microsoft_suite.api_microsoft_org import get_data, create_graph_client_from_token, get_microsoft_graph_api_token
from utils import get_last_n_weeks_range

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')

# ENV variables
FRONTEND_APP = 'ekilibria/frontend/ekilibria-front'
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
SCOPES = os.getenv("GOOGLE_SCOPES", "")
ENV = os.getenv("VITE_ENV", "development")

# OAuth configuration
oauth = OAuth(app)
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',  # <-- Use this!
    client_kwargs={'scope': SCOPES},
    prompt='consent',
    redirect_uri=os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8080/auth/callback")
)

# Features to consider for contribution analysis
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

# Serve React App
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    if path != "" and os.path.exists(f"{FRONTEND_APP}/dist/{path}"):
        return send_from_directory(f"{FRONTEND_APP}/dist", path)
    return send_from_directory(f"{FRONTEND_APP}/dist", "index.html")

## Microsoft
# Microsoft Graph API Authentication
@app.route("/auth/microsoft", methods=["POST"])
def auth_microsoft():
    session["login_type"] = "microsoft"
    input = request.json
    # Extract the login information from the post request
    token_dict = {"token": input["token"], "expires_on": input["expires_on"]}
    print(f"Token received: {token_dict}")
    user, token_info = asyncio.run(get_microsoft_graph_api_token(token_dict))
    if user is None:
        return jsonify({"error": "Authentication failed"}), 401
    print(f"User authenticated: {user.display_name}")
    session["ms_token"] = token_info
    session["user"] = user.mail
    session['user_name'] = user.display_name or user.mail or 'Unknown User'
    return jsonify({
        "user_email": user.mail
    })

# Endpoint to extract features from Microsoft Graph API
@app.route("/extract_features_microsoft/<int:weeks>")
def get_features_microsoft(weeks):
    token_filename = session.get("token_path")

    client = create_graph_client_from_token(session["ms_token"])
    week_ranges = get_last_n_weeks_range(n=weeks)
    features_result = []

    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()


    for i, (date_from, date_to) in enumerate(week_ranges):
        print(f"🗓️ Semana {i+1}: desde {date_from} hasta {date_to}")

        features = loop.run_until_complete(
            get_data(
                client,
                datetime.datetime.combine(date_from, datetime.datetime.min.time()),
                datetime.datetime.combine(date_to, datetime.datetime.max.time())))

        features['fecha_desde'] = str(date_from)
        features['fecha_hasta'] = str(date_to)

        print("✅ Features extraídos:", features)

        features_result.append(features)

    print(features_result)

    json = {"features": features_result}

    # Send the features to the prediction API
    if ENV == "development":
        print("development API")
        response = requests.post("http://localhost:8000/predict_new", json=json)
    else:
        print("production API")
        response = requests.post("https://ekilibria-49509618656.us-central1.run.app/predict_new", json=json)

    if response.status_code == 200:
        prediction = response.json()
    else:
        prediction = {"error": "Failed to get prediction from the model"}

    print(f"Predicción obtenida: {prediction}")

    return jsonify(prediction,features_result)


## Google
# Google Suite Authentication
@app.route('/auth/google')
def authenticate_google_user():
    session["login_type"] = "google"
    return oauth.google.authorize_redirect(url_for('auth_callback', _external=True))

# Endpoint to extract features from Google Suite
@app.route("/extract_features_google/<int:weeks>")
def get_features_google(weeks):
    token_filename = session.get("token_path")

    week_ranges = get_last_n_weeks_range(n=weeks)
    features_result = []

    for i, (date_from, date_to) in enumerate(week_ranges):
        print(f"🗓️ Semana {i+1}: desde {date_from} hasta {date_to}")

        features = extract_all_features(
            token_filename,
            fecha_desde=datetime.datetime.combine(date_from, datetime.datetime.min.time()),
            fecha_hasta=datetime.datetime.combine(date_to, datetime.datetime.max.time())
        )

        features['fecha_desde'] = str(date_from)
        features['fecha_hasta'] = str(date_to)

        print("✅ Features extraídos:", features)

        features_result.append(features)

    print(features_result)

    json = {"features": features_result}


    # Send the features to the prediction API
    if ENV == "development":
        print("development API")
        response = requests.post("http://localhost:8000/predict_new", json=json)
    else:
        print("production API")
        response = requests.post("https://ekilibria-49509618656.us-central1.run.app/predict_new", json=json)

    if response.status_code == 200:
        prediction = response.json()
    else:
        prediction = {"error": "Failed to get prediction from the model"}

    print(f"Predicción obtenida: {prediction}")

    return jsonify(prediction,features_result)

# Callback for Google OAuth
@app.route('/auth/callback')
def auth_callback():
    print("Callback received from Google OAuth")
    token = oauth.google.authorize_access_token()
    print("Token received:", token)
    # Use the token to get user info
    userinfo_url = 'https://openidconnect.googleapis.com/v1/userinfo'
    resp = oauth.google.get(userinfo_url, token=token)
    user_info = resp.json()
    print(f"User info received: {user_info}")
    session['user'] = user_info
    session['user_name'] = user_info.get('name') or user_info.get('email', 'Unknown User')
    TOKEN_DIR = os.getenv("TOKEN_DIR", "google_suite/auth")
    os.makedirs(TOKEN_DIR, exist_ok=True)
    user_email = user_info['email']
    token_filename = os.path.join(TOKEN_DIR, f'token_{user_email}.json')
    with open(token_filename, 'w') as token_file:
        json.dump(token, token_file)

    session['token_path'] = token_filename

    return redirect("/#/show")


## MISC API Endpoints
# Endpoint to get prediction based on given values
@app.route("/predict_given_values", methods=["POST"])
def get_prediction_given_values():
    data = request.get_json() or {}
    # Esperamos una lista de features dicts
    features_result = data.get("features", [])
    if isinstance(features_result, dict):
        # por si vino un dict suelto, lo normalizamos a lista
        features_result = [features_result]

    # Armamos el payload para la API de predicción (idéntico a week_info)
    json_payload = {"features": features_result}

    response = requests.post(
        "https://ekilibria-49509618656.us-central1.run.app/predict_new",
        json=json_payload,
        timeout=30
    )

    if response.status_code == 200:
        prediction = response.json()  # esto es un dict con "result": [...]
    else:
        prediction = {"error": "Failed to get prediction from the model"}

    # DEVOLVEMOS EL MISMO SHAPE QUE week_info():
    # jsonify(prediction, features_result)
    return jsonify(prediction, features_result)

# Endpoint to get the login method(google or microsoft)
@app.route('/get_login_method')
def get_login_method():
    login_method = session.get('login_type')
    return jsonify({'login_method': login_method})

# Endpoint to get the logged-in user's email
@app.route('/get_login_user_email')
def get_login_user_email():
    user_name = session.get('user_name')
    print(f"User name in session: {user_name}")
    if not user_name:
        return jsonify({'error': 'User not authenticated'}), 401
    return jsonify({'user_name': user_name})

# Endpoint to log out the user
@app.route('/logout')
def logout():
    session.clear()
    print("User logged out successfully")
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
