from fastapi import FastAPI, Request, Query, HTTPException, BackgroundTasks
from config import STRAVA_VERIFY_TOKEN
from strava import fetch_active_token, fetch_training_details, fetch_activity_streams
from analysis import process_run_data
from bot import generate_and_send_analysis

app = FastAPI()

def background_analysis_task(activity_id: int):
    print(f"🔄 Processing activity ID: {activity_id}...")
    try:
        access_token = fetch_active_token()
        summary = fetch_training_details(activity_id, access_token)
        streams = fetch_activity_streams(activity_id, access_token)

        # 1. Przetworzenie danych (strefy, góry, kadencja)
        run_data = process_run_data(summary, streams)

        # 2. Wysłanie do AI i na Telegram
        generate_and_send_analysis(run_data)
    except Exception as e:
        print(f"❌ Error during processing: {str(e)}")


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
        background_tasks.add_task(background_analysis_task, training_id)

    return {"status": "success"}

@app.get("/")
def home():
    return { "status": "BiegAI jest gotowy!" }
