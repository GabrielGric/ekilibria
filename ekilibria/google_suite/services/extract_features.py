import json
import os
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

load_dotenv()

TOKEN_DIR = os.getenv("TOKEN_DIR", "google_suite/auth")
TOKEN_FILENAME = os.getenv("TOKEN_FILENAME")
token_file = os.path.join(TOKEN_DIR, TOKEN_FILENAME)

def extract_email_features(token_file, fecha_desde, fecha_hasta, hora_inicio_laboral=9, hora_fin_laboral=18):
    # Cargar token
    with open(token_file, 'r') as token:
        token_data = json.load(token)

    creds = Credentials(
        token=token_data['access_token'],
        refresh_token=token_data.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
    )
    
    service = build('gmail', 'v1', credentials=creds)

    # Asegurar que fecha_desde y fecha_hasta sean datetime
    if not isinstance(fecha_desde, datetime) or not isinstance(fecha_hasta, datetime):
        raise ValueError("fecha_desde y fecha_hasta deben ser objetos datetime.datetime")

    # Calcular días totales (ambos inclusive)
    total_dias = (fecha_hasta - fecha_desde).days + 1

    # Formatear para query Gmail (inclusive fecha_hasta)
    start_str = fecha_desde.strftime('%Y/%m/%d')
    end_str = (fecha_hasta + timedelta(days=1)).strftime('%Y/%m/%d')

    # --- Correos enviados ---
    query_sent = f"after:{start_str} before:{end_str} in:sent"
    results_sent = service.users().messages().list(userId='me', q=query_sent).execute()
    sent_messages = results_sent.get('messages', [])

    emails_sent = 0
    emails_sent_out_of_hours = 0

    for msg in sent_messages:
        msg_detail = service.users().messages().get(userId='me', id=msg['id'], format='metadata').execute()
        internal_date = int(msg_detail['internalDate']) / 1000
        dt = datetime.fromtimestamp(internal_date)
        emails_sent += 1
        if dt.hour < hora_inicio_laboral or dt.hour >= hora_fin_laboral:
            emails_sent_out_of_hours += 1

    # --- Correos recibidos (inbox) ---
    query_received = f"after:{start_str} before:{end_str} in:inbox category:primary"
    results_received = service.users().messages().list(userId='me', q=query_received).execute()
    received_messages = results_received.get('messages', [])
    emails_received = len(received_messages)

    # --- Promedios diarios ---
    emails_sent_prom = round(emails_sent / total_dias, 2)
    emails_sent_out_hours_prom = round(emails_sent_out_of_hours / total_dias, 2)
    emails_received_prom = round(emails_received / total_dias, 2)

    return {
        "emails_sent": emails_sent_prom,
        "emails_sent_out_of_hours": emails_sent_out_hours_prom,
        "emails_received": emails_received_prom
    }

def extract_calendar_features(token_file, fecha_desde, fecha_hasta, hora_inicio_laboral=9, hora_fin_laboral=18):
    # Cargar credenciales desde token
    with open(token_file, 'r') as token:
        token_data = json.load(token)

    creds = Credentials(
        token=token_data['access_token'],
        refresh_token=token_data.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
    )

    service = build('calendar', 'v3', credentials=creds)

    # Formatear rangos para consulta
    start_time = fecha_desde.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
    end_time = (fecha_hasta + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'

    # print(f"\n🔎 Querying events from {start_time} to {end_time}\n")

    # Obtener eventos
    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_time,
        timeMax=end_time,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    # print(f"📒 Total events fetched from calendar: {len(events)}")

    # Inicializar variables
    num_events = 0
    events_out_of_hours = 0
    total_meeting_hours = 0.0
    meeting_durations = []
    meetings_weekend = 0
    num_meetings_no_breaks = 0
    num_overlapping_meetings = 0

    # Convertir eventos a lista de tuplas (inicio, fin)
    parsed_events = []

    for event in events:
        try:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))

            if 'T' not in start or 'T' not in end:
                continue  # Evento sin hora, tipo "día completo" → se omite

            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))

            duration_hours = (end_dt - start_dt).total_seconds() / 3600.0

            num_events += 1
            total_meeting_hours += duration_hours
            meeting_durations.append(duration_hours)

            if start_dt.hour < hora_inicio_laboral or end_dt.hour > hora_fin_laboral:
                events_out_of_hours += 1

            if start_dt.weekday() >= 5:
                meetings_weekend += 1

            parsed_events.append((start_dt, end_dt))

            # print(f"🗓️ Event: {event.get('summary', 'Sin título')} | Start: {start_dt} | End: {end_dt}")
        except Exception as e:
            print(f"⚠️ Error procesando evento: {e}")
            continue

    # Ordenar eventos por inicio para detectar solapamientos y falta de pausas
    parsed_events.sort(key=lambda x: x[0])

    for i in range(1, len(parsed_events)):
        prev_end = parsed_events[i - 1][1]
        current_start = parsed_events[i][0]

        if current_start < prev_end:
            num_overlapping_meetings += 1
            continue  # Si se solapan, no evalúes si hay descanso
        elif (current_start - prev_end).total_seconds() / 60.0 < 15:
            num_meetings_no_breaks += 1

    avg_meeting_duration = (sum(meeting_durations) / len(meeting_durations)) * 60 if meeting_durations else 0  # en minutos

    return {
        'num_events': num_events,
        'num_events_outside_hours': events_out_of_hours,
        'total_meeting_hours': round(total_meeting_hours, 2),
        'avg_meeting_duration': round(avg_meeting_duration, 2),
        'meetings_weekend': meetings_weekend,
        'num_meetings_no_breaks': num_meetings_no_breaks,
        'num_overlapping_meetings': num_overlapping_meetings
    }

def extract_drive_features(token_file, fecha_desde, fecha_hasta):
    # Cargar credenciales desde token
    with open(token_file, 'r') as token:
        token_data = json.load(token)

    creds = Credentials(
        token=token_data['access_token'],
        refresh_token=token_data.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
    )
    # Crear servicio de Google Drive
    service = build('drive', 'v3', credentials=creds)

    # Convertir fechas a formato RFC3339 (UTC ISO format)
    time_min = fecha_desde.isoformat()
    time_max = fecha_hasta.isoformat()

    # print(f"🔍 Querying Drive files from {time_min} to {time_max}")

    # Obtener información del usuario autenticado
    user_info = service.about().get(fields="user(emailAddress)").execute()
    user_email = user_info['user']['emailAddress']

    # Buscar archivos modificados en el rango de fechas
    results = service.files().list(
        q=f"modifiedTime >= '{time_min}' and modifiedTime < '{time_max}' and trashed = false",
        fields="files(id, name, createdTime, modifiedTime, owners, lastModifyingUser)",
        pageSize=1000
    ).execute()

    files = results.get('files', [])

    archivos_creados = []
    archivos_editados = []

    for file in files:
        created = file.get('createdTime')
        modified = file.get('modifiedTime')
        owner_email = file.get('owners')[0]['emailAddress'] if file.get('owners') else None
        last_editor_email = file.get('lastModifyingUser', {}).get('emailAddress')

        # Validar creación por el usuario autenticado
        if created >= time_min and created < time_max and owner_email == user_email:
            archivos_creados.append(file['name'])

        # Validar edición por el usuario autenticado, pero solo si NO fue creado en este mismo rango
        elif modified >= time_min and modified < time_max and last_editor_email == user_email:
            if not (created >= time_min and created < time_max and owner_email == user_email):
                archivos_editados.append(file['name'])

    # print(f"📂 Analizando actividad del usuario: {user_email}")
    # print(f"🆕 Archivos creados por el usuario: {archivos_creados}")
    # print(f"✏️ Archivos editados por el usuario: {archivos_editados}")

    return {
        'docs_created': len(archivos_creados),
        'docs_edited': len(archivos_editados)
    }

def extract_all_features(token_file, fecha_desde, fecha_hasta):
    features = {}
    features.update(extract_email_features(token_file, fecha_desde, fecha_hasta))
    features.update(extract_calendar_features(token_file, fecha_desde, fecha_hasta))
    features.update(extract_drive_features(token_file, fecha_desde, fecha_hasta))
    return features


if __name__ == "__main__":
    # fecha_desde = datetime(2025, 6, 16)
    # fecha_hasta = datetime(2025, 6, 25)

    from argparse import ArgumentParser
    token_file = os.path.abspath(os.path.join(TOKEN_DIR, TOKEN_FILENAME))


    parser = ArgumentParser()
    parser.add_argument("--from", dest="fecha_desde", help="Fecha desde (YYYY-MM-DD)", required=False)
    parser.add_argument("--to", dest="fecha_hasta", help="Fecha hasta (YYYY-MM-DD)", required=False)
    args = parser.parse_args()

    fecha_desde = datetime.fromisoformat(args.fecha_desde) if args.fecha_desde else datetime(2025, 6, 16)
    fecha_hasta = datetime.fromisoformat(args.fecha_hasta) if args.fecha_hasta else datetime(2025, 6, 25)

    # result_mail = extract_email_features(token_file, fecha_desde, fecha_hasta)
    # result_calendar = extract_calendar_features(token_file, fecha_desde, fecha_hasta)
    # result_drive = extract_drive_features(token_file, fecha_desde, fecha_hasta)
    # print(result_mail)
    # print(result_calendar)
    # print(result_drive)

    result = extract_all_features(token_file, fecha_desde, fecha_hasta)
    # # print(result)
    # print(json.dumps(result, indent=2, ensure_ascii=False))

