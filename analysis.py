def process_run_data(summary, streams):
    """Główne formatowanie danych przed wysłaniem do AI"""

    # 1. Rozpakowanie strumieni
    stream_map = {s.get('type'): s.get('data', []) for s in streams} if isinstance(streams, list) else {}

    hr_s = stream_map.get('heartrate', [])
    dist_s = stream_map.get('distance', [])
    vel_s = stream_map.get('velocity_smooth', [])
    cad_s = stream_map.get('cadence', [])
    alt_s = stream_map.get('altitude', [])  # WYSOKOŚĆ (N.P.M)

    # 2. Sprytny fix kadencji
    valid_cadences = [c for c in cad_s if c > 0]
    is_single_leg = max(valid_cadences) <= 110 if valid_cadences else False



    data = {
        "name": summary.get("name", "Trening"),
        "distance_km": round(summary.get("distance", 0) / 1000, 2),
        "duration_mins": round(summary.get("moving_time", 0) / 60, 2),
        "avg_hr": summary.get("average_heartrate"),
        "laps": []
    }

    # 4. Analiza odcinków 500m
    current_checkpoint = 500
    last_idx = 0

    for i in range(len(dist_s)):
        if dist_s[i] >= current_checkpoint:
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

            data["laps"].append({
                "odcinek": f"{current_checkpoint}m",
                "tempo": pace_str,
                "tetno": hr_s[i] if i < len(hr_s) else "Brak",
                "kadencja": cad_val,
                "gora_dol": f"+{alt_diff}m" if alt_diff > 0 else f"{alt_diff}m"
            })

            current_checkpoint += 500
            last_idx = i

    return data