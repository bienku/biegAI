from datetime import datetime

def calculate_custom_hr_zones(hr_stream):
    """Liczy strefy na podstawie dokładnych progów z zegarka Suunto"""
    zones = {"Z1": 0, "Z2": 0, "Z3": 0, "Z4": 0, "Z5": 0}

    for hr in hr_stream:
        if hr == 0: continue

        # Zones base on the suunto watch:
        if hr > 172: zones["Z5"] += 1
        elif hr >= 162: zones["Z4"] += 1
        elif hr >= 152: zones["Z3"] += 1
        elif hr >= 143: zones["Z2"] += 1
        else: zones["Z1"] += 1

    return {k: f"{v//60}:{v%60:02d}" for k, v in zones.items() if v > 0}

def process_run_data(summary, streams):
    """Główne formatowanie danych przed wysłaniem do AI"""

    # 1. Rozpakowanie strumieni
    stream_map = {s.get('type'): s.get('data', []) for s in streams} if isinstance(streams, list) else {}

    raw_date = summary.get("start_date_local", "")
    run_date = "Brak daty"
    if raw_date:
        try:
            dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
            run_date = dt.strftime("%d.%m.%Y %H:%M")
        except Exception:
            run_date = raw_date

    hr_s = stream_map.get('heartrate', [])
    dist_s = stream_map.get('distance', [])
    vel_s = stream_map.get('velocity_smooth', [])
    cad_s = stream_map.get('cadence', [])
    alt_s = stream_map.get('altitude', [])  # WYSOKOŚĆ (N.P.M)

    # 2. Sprytny fix kadencji
    valid_cadences = [c for c in cad_s if c > 0]
    is_single_leg = max(valid_cadences) <= 110 if valid_cadences else False

    # 3. Własne strefy tętna (Koniec z Paywallem!)
    custom_zones = calculate_custom_hr_zones(hr_s)

    data = {
        "name": summary.get("name", "Trening"),
        "date": run_date,
        "distance_km": round(summary.get("distance", 0) / 1000, 2),
        "duration_mins": round(summary.get("moving_time", 0) / 60, 2),
        "avg_hr": summary.get("average_heartrate"),
        "hr_zones": custom_zones,
        "laps": []
    }

    # 4. Analiza odcinków 500m
    current_checkpoint = 500
    last_idx = 0

    for i in range(len(dist_s)):
        is_last_point = (i == len(dist_s) - 1)

        if dist_s[i] >= current_checkpoint or is_last_point:
            if i > last_idx:
                # Tempo
                pace_str = "0:00"
                if vel_s[i] > 0:
                    pace_decimal = 16.666 / vel_s[i]
                    pace_str = f"{int(pace_decimal)}:{int((pace_decimal - int(pace_decimal)) * 60):02d}"

                # Kadencja
                cad_val = cad_s[i] if i < len(cad_s) else 0
                if is_single_leg and cad_val > 0:
                    cad_val *= 2

                # Przewyższenie na tym odcinku (Różnica wysokości)
                alt_diff = 0
                if i < len(alt_s) and last_idx < len(alt_s):
                    alt_diff = round(alt_s[i] - alt_s[last_idx], 1)

                # Nazywanie odcinka (zwykłe 500m czy resztówka)
                if is_last_point and dist_s[i] < current_checkpoint:
                    lap_label = f"{int(dist_s[i])}m"
                else:
                    lap_label = f"{current_checkpoint}m"

                data["laps"].append({
                    "odcinek": lap_label,
                    "tempo": pace_str,
                    "tetno": hr_s[i] if i < len(hr_s) else "Brak",
                    "kadencja": cad_val,
                    "gora_dol": f"+{alt_diff}m" if alt_diff > 0 else f"{alt_diff}m"
                })

                last_idx = i
                if not is_last_point:
                    current_checkpoint += 500

    return data