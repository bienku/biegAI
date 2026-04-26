import requests
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
TEMP_CODE = "f74af95145ce2a54604156554addcc9c7e3fab41"

response = requests.post(
    "https://www.strava.com/api/v3/oauth/token",
    data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": TEMP_CODE,
        "grant_type": "authorization_code",
    }
)

print(response.json())
