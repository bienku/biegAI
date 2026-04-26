import requests
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
CALLBACK_URL = "https://track-handbrake-acting.ngrok-free.dev/webhook"
VERIFY_TOKEN = os.getenv("STRAVA_VERIFY_TOKEN")

print("Request do stravy...")

response = requests.post(
    "https://www.strava.com/api/v3/push_subscriptions",
    data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "callback_url": CALLBACK_URL,
        "verify_token": VERIFY_TOKEN,
    }
)

print(response.json())
