import requests
from config import STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN

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
    keys = "distance,heartrate,velocity_smooth,cadence,altitude"
    url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams?keys={keys}&key_by_distance=true"
    headers = { "Authorization": f"Bearer {access_token}" }
    response = requests.get(url, headers=headers)
    return response.json()

def fetch_activity_zones(activity_id: int, access_token: str):
    url = f"https://www.strava.com/api/v3/activities/{activity_id}/zones"
    headers = { "Authorization": f"Bearer {access_token}" }
    response = requests.get(url, headers=headers)
    return response.json()
