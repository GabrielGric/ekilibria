from flask import Flask, send_from_directory, jsonify, session
import random
import os
import datetime
import requests
import asyncio

from ekilibria.google_suite.auth.authenticate_google_user import authenticate_google_user
from ekilibria.google_suite.services.extract_features import extract_all_features
from ekilibria.microsoft_suite.api_microsoft_org import get_microsoft_graph_api_token, get_data, create_graph_client_from_token

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')

FRONTEND_APP = '../frontend/ekilibria-front'

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

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    if path != "" and os.path.exists(f"{FRONTEND_APP}/dist/{path}"):
        return send_from_directory(f"{FRONTEND_APP}/dist", path)
    return send_from_directory(f"{FRONTEND_APP}/dist", "index.html")


@app.route("/hello")
def hello():
    return f"{random.randint(1, 100)} Hello World!"

@app.route("/auth/microsoft")
def auth_microsoft():
    print("Authenticating with Microsoft Graph API...")
    result = asyncio.run(get_microsoft_graph_api_token())
    
    if result is None:
        return jsonify({"error": "Authentication failed"}), 401
    
    user, token_dict = result
    session["ms_token"] = token_dict
    session["user"] = user.mail
    return jsonify({
        "user_email": user.mail
    })

@app.route("/extract_features_microsoft/")
def get_features_microsoft():
    print("Extracting features from Microsoft Graph API...")
    try:
        if "ms_token" not in session:
            return jsonify({"error": "Microsoft client not authenticated"}), 401
        client = create_graph_client_from_token(session["ms_token"])
        features_result = asyncio.run(get_data(client))
                
        json = { "features": features_result } if isinstance(features_result, dict) else { "features": {} }

        response = requests.post("http://127.0.0.1:8000/predict", json=json)
        if response.status_code == 200:
            prediction = response.json()
        else:
            prediction = {"error": "Failed to get prediction from the model"}
        contributions = prediction.get("contributions", {})
        contributions = {k: v for k, v in contributions.items() if k in features}
        print(f"Extracted features: {prediction}")
        res = {
            "burnout": prediction.get("burnout_index", 0),
            "contributions": contributions,
            "features": features_result,
        }
        return jsonify(res)
    except Exception as e:
        print(f"Error extracting features from Microsoft: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/auth/google")
def auth_google():
    token_path, user_email = authenticate_google_user()
    session["token_path"] = token_path
    return jsonify({'user_email': user_email})

@app.route("/extract_features_google/")
def get_features_google():
    token_filename = session.get("token_path")
    fecha_hasta = datetime.datetime.now()
    fecha_desde = fecha_hasta - datetime.timedelta(days=7)
    features_result = extract_all_features(
                token_filename,
                fecha_desde,
                fecha_hasta
            )
    
    json = { "features": features_result } if isinstance(features_result, dict) else { "features": {} }

    response = requests.post("http://127.0.0.1:8000/predict", json=json)
    if response.status_code == 200:
        prediction = response.json()
    else:
        prediction = {"error": "Failed to get prediction from the model"}
        

    contributions = prediction.get("contributions", {})
    contributions = {k: v for k, v in contributions.items() if k in features}
    print(f"Extracted features: {prediction}")
    res = {
        "burnout": prediction.get("burnout_index", 0),
        "contributions": contributions,
        "features": features_result,
    }
    return jsonify(res)

if __name__ == "__main__":
    app.run(debug=True)