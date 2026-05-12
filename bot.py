import requests
from google import genai
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

def send_telegram_message(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }
    response = requests.post(url, json=payload)
    return response.json()

def build_prompt(run_data: dict) -> str:
    zones_text = "\n".join([f"Z{k[-1]}: {v} min" for k, v in run_data['hr_zones'].items()])
    laps_text = "\n".join([
        f"{l['odcinek']} | Tempo: {l['tempo']} | HR: {l['tetno']} | Kadencja: {l['kadencja']} | Profil: {l['gora_dol']}"
        for l in run_data['laps']
    ])

    return f"""
    Jesteś analitykiem sportowym. Analizujesz dane biegacza obiektywnie, chłodno i opierając się na faktach.
    Unikaj sztucznych pochwał, hiperboli (nie używaj słów typu 'fatalny', 'dramatyczny', 'wspaniały').
    Zwróć szczególną uwagę na profil trasy (podbiegi/zbiegi) w kontekście tętna i tempa.

    DANE:
    Trening: {run_data['name']}
    Data: {run_data['date']} | Temperatura: {run_data['temp']}°C
    Dystans: {run_data['distance_km']} km | Czas: {run_data['duration_mins']} min | Śr HR: {run_data['avg_hr']}

    CZAS W STREFACH (Custom):
    {zones_text}

    PRZEBIEG CO 500m:
    {laps_text}

    ZADANIE (Używaj formatowania HTML, np. <b>pogrubienie</b>):
    1. <b>Fakty:</b> Krótkie podsumowanie dystansu, stref i wpływu ukształtowania terenu na bieg.
    2. <b>Obserwacje:</b> Zależności. Jak zachowało się tętno na podbiegach? Czy kadencja była stabilna niezależnie od tempa? 
    3. <b>Wniosek:</b> Jeden konkretny wniosek techniczny bez motywacyjnego bullshitu.
    """


def generate_and_send_analysis(run_data):
    prompt = build_prompt(run_data)

    print("🤖 Generating analysis ...")
    ai_response = model.generate_content(prompt)
    send_telegram_message(f"🏃‍♂️ <b>Raport z biegu:</b>\n\n{ai_response.text}")
    print("✅ Analysis sent on Telegram!")
