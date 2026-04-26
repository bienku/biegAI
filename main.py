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

def analyze_and_send(activity_id: int):
    access_token = fetch_active_token()
    running_data = fetch_training_details(activity_id, access_token)

    name = running_data.get("name", "Bieg bez nazwy")
    distance_km = round(running_data.get("distance", 0) / 1000, 2)
    duration_mins = round(running_data.get("moving_time", 0) / 60, 2)
    hr = running_data.get("average_heartrate", "Brak danych o tętnie")
    print(f"📊 Dane wyciągnięte: {distance_km}km w {duration_mins}min, HR: {hr}")

    prompt = f"""
        Jesteś wirtualnym trenerem biegowym. Twój podopieczny właśnie skończył trening.
        Oto dane z zegarka (Strava):
        - Nazwa: {name}
        - Dystans: {distance_km} km
        - Czas: {duration_mins} minut
        - Średnie tętno: {hr} bpm

        Napisz mu krótką (max 3-4 zdania), motywującą wiadomość na Telegram. 
        Zwróć uwagę na jego tętno i dystans. Używaj emoji. Bądź bezpośredni.
        """

    ai_response = model.generate_content(prompt)
    send_telegram_message(f"🏃‍♂️ **Nowy trening:** {name}\n\n🤖 **Komentarz Trenera:**\n{ai_response.text}")

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
