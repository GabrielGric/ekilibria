import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os

# Cargamos variables de entorno
load_dotenv()

# 1. Variables desde .env (rutas relativas al proyecto raíz)
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE")
TOKEN_DIR = os.getenv("TOKEN_DIR", "google_suite/auth")
SCOPES = os.getenv("SCOPES").split(',')

# ✅ Validación: chequeamos que las variables se hayan cargado correctamente
if not CREDENTIALS_FILE or not TOKEN_DIR or not SCOPES:
    raise ValueError("❌ Las variables de entorno no están definidas correctamente. Verifica el archivo .env.")

# Convertimos CREDENTIALS_FILE y TOKEN_DIR a rutas absolutas
CREDENTIALS_FILE = os.path.abspath(CREDENTIALS_FILE)
TOKEN_DIR = os.path.abspath(TOKEN_DIR)

def authenticate_google_user():
    # 2. Iniciamos el flujo de autenticación
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)

    # 3. Obtenemos el email del usuario
    gmail_service = build('gmail', 'v1', credentials=creds)
    profile = gmail_service.users().getProfile(userId='me').execute()
    user_email = profile['emailAddress']
    print(f"✅ Autenticado como: {user_email}")

    # 4. Guardamos el token con el nombre del usuario
    os.makedirs(TOKEN_DIR, exist_ok=True)  # Aseguramos que el dir exista
    token_filename = os.path.join(TOKEN_DIR, f'token_{user_email}.json')
    with open(token_filename, 'wb') as token_file:
        pickle.dump(creds, token_file)

    return token_filename, user_email

if __name__ == '__main__':
    authenticate_google_user()
