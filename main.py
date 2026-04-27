from fastapi import FastAPI, Request, Query, HTTPException, BackgroundTasks
import google.generativeai as genai
import requests
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")
STRAVA_VERIFY_TOKEN = os.getenv("STRAVA_VERIFY_TOKEN")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')
app = FastAPI()

def send_telegram_message(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }
    response = requests.post(url, json=payload)
    return response.json()

def fetch_active_token():
    url = "https://www.strava.com/api/v3/oauth/token"
    payload = {
        "client_id": STRAVA_CLIENT_ID,
        "client_secret": STRAVA_CLIENT_SECRET,
        "refresh_token": STRAVA_REFRESH_TOKEN,
        "grant_type": "refresh_token",
    }
    response = requests.post(url, data=payload)
    return response.json().get("access_token")

def fetch_training_details(activity_id: int, access_token: str):
    url = f"https://www.strava.com/api/v3/activities/{activity_id}"
    headers = { "Authorization": f"Bearer {access_token}" }
    response = requests.get(url, headers=headers)
    return response.json()

def fetch_activity_streams(activity_id: int, access_token: str):
    keys = "distance,heartrate,velocity_smooth,cadence"
    url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams?keys={keys}&key_by_distance=true"
    headers = { "Authorization": f"Bearer {access_token}" }
    response = requests.get(url, headers=headers)
    return response.json()

def fetch_activity_zones(activity_id: int, access_token: str):
    url = f"https://www.strava.com/api/v3/activities/{activity_id}/zones"
    headers = { "Authorization": f"Bearer {access_token}" }
    response = requests.get(url, headers=headers)
    return response.json()

def get_enhanced_activity_data(activity_id: int, access_token: str):
    summary = fetch_training_details(activity_id, access_token)
    streams = fetch_activity_streams(activity_id, access_token)
    zones = fetch_activity_zones(activity_id, access_token)

    data = {
        "name": summary.get("name", "Brak nazwy"),
        "distance_km": round(summary.get("distance", 0) / 1000, 2),
        "duration_mins": round(summary.get("moving_time", 0) / 60, 2),
        "avg_hr": summary.get("average_heartrate"),
        "max_hr": summary.get("max_heartrate"),
        "avg_cadence": summary.get("average_cadence"),
    }

    hr_zones = []
    if isinstance(zones, list):
        hr_zones_dict = next((z for z in zones if z.get('type') == 'heartrate'), {})
        hr_zones = hr_zones_dict.get('distribution_buckets', [])
    else:
        print(f"⚠️ [DEBUG] Problem ze strefami tętna. Odpowiedź Stravy: {zones}")

    data["hr_zones"] = [
        {"zone": i + 1, "time_mins": round(b.get('time', 0) / 60, 1)}
        for i, b in enumerate(hr_zones)
    ]

    stream_map = {}
    if isinstance(streams, list):
        stream_map = {s.get('type'): s.get('data', []) for s in streams}
    else:
        print(f"⚠️ [DEBUG] Problem ze strumieniami. Odpowiedź Stravy: {streams}")

    hr_s = stream_map.get('heartrate', [])
    dist_s = stream_map.get('distance', [])
    vel_s = stream_map.get('velocity_smooth', [])
    cad_s = stream_map.get('cadence', [])

    laps = []
    current_checkpoint = 500  # co 500m
    for i in range(len(dist_s)):
        if dist_s[i] >= current_checkpoint:
            pace_str = "0:00"
            if vel_s[i] > 0:
                pace_decimal = 16.666 / vel_s[i]
                pace_mins = int(pace_decimal)
                pace_secs = int((pace_decimal - pace_mins) * 60)
                pace_str = f"{pace_mins}:{pace_secs:02d}"

            cadence_val = cad_s[i] if i < len(cad_s) else None

            laps.append({
                "odcinek": f"{current_checkpoint}m",
                "tempo": pace_str,
                "tetno": hr_s[i] if i < len(hr_s) else None,
                "kadencja": cadence_val
            })
            current_checkpoint += 500

    data["laps"] = laps
    return data

def analyze_and_send(activity_id: int):
    access_token = fetch_active_token()

    run = get_enhanced_activity_data(activity_id, access_token)

    if run.get('hr_zones'):
        zones_summary = "\n".join([f"Z{z['zone']}: {z['time_mins']} min" for z in run['hr_zones']])
    else:
        zones_summary = "Brak dostępu do stref tętna (brak Strava Premium)."

    laps_summary = "\n".join([
        f"Odcinek {l['odcinek']}: Tempo {l['tempo']}, HR {l['tetno']}, Kadencja {l['kadencja']}"
        for l in run['laps']
    ])

    prompt = f"""
        Jesteś profesjonalnym trenerem biegowym, analizującym dane ze smartwatcha podopiecznego.
        Bądź bezpośredni, konkretny i używaj żargonu biegowego, ale bez zbytniego "słodzenia". 
        Twoim celem jest optymalizacja jego formy i ochrona przed kontuzjami.

        DANE OGÓLNE:
        - Trening: {run['name']}
        - Dystans: {run['distance_km']} km, Czas: {run['duration_mins']} min
        - Tętno (śr/max): {run['avg_hr']} / {run['max_hr']} bpm
        - Średnia kadencja: {run['avg_cadence']} kroków/min

        CZAS W STREFACH TĘTNA:
        {zones_summary}

        ANALIZA ODCINKÓW (co 500 metrów):
        {laps_summary}

        TWOJE ZADANIE - Wygeneruj wiadomość na Telegram (użyj Markdown, pogrubień i emoji) w 3 sekcjach:
        1. 🎯 Szybka ocena (1-2 zdania): Jak oceniasz ten trening ogólnie na podstawie dystansu i czasu w strefach?
        2. 🔬 Analiza głęboka: Zwróć uwagę na korelację między tempem, tętnem a kadencją. Czy pod koniec widać "dryf tętna" (rośnie HR, a tempo spada/stoi)? Czy kadencja była równa?
        3. 💡 Wskazówka na następny bieg: Konkretna rada (np. "zwolnij na pierwszych 2km", "pilnuj kadencji, bo spada po 4km", "świetna robota w strefie tlenowej").
    """


    ai_response = model.generate_content(prompt)
    print(f"prompt: {prompt}")
    print(f"ai_response: {ai_response.text}")
    send_telegram_message(f"🏃‍♂️ **Analiza szczegółowa:**\n\n{ai_response.text}")

@app.get('/webhook')
def verify_strava_webhook(
        hub_mode: str = Query(None, alias="hub.mode"),
        hub_challenge: str = Query(None, alias="hub.challenge"),
        hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    if hub_mode == 'subscribe' and hub_verify_token == STRAVA_VERIFY_TOKEN:
        return { "hub.challenge": hub_challenge }
    raise HTTPException(status_code=403, detail="Incorrect auth token")

@app.post('/webhook')
async def receive_strava_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()

    if payload.get("object_type") == 'activity' and payload.get("aspect_type") == "create":
        training_id = payload.get("object_id")
        background_tasks.add_task(analyze_and_send, training_id)

    return {"status": "success"}

@app.get("/")
def home():
    return { "status": "BiegAI jest gotowy!" }
