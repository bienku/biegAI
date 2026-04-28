from strava import fetch_active_token, fetch_training_details, fetch_activity_streams
from analysis import process_run_data
from bot import build_prompt

ACTIVITY_ID = 18281925703

def dry_run_test():
    print(f"🚀 Fetching data for activity: {ACTIVITY_ID}...")
    access_token = fetch_active_token()
    summary = fetch_training_details(ACTIVITY_ID, access_token)
    streams = fetch_activity_streams(ACTIVITY_ID, access_token)

    print("⚙️ Processing data (Calculating zones, altitude, cadence)...")
    run_data = process_run_data(summary, streams)

    prompt = build_prompt(run_data)

    print("🔥 FINAL PROMPT:" + "\n")
    print(prompt)


if __name__ == "__main__":
    dry_run_test()
