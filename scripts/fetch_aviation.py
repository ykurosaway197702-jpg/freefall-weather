#!/usr/bin/env python3
"""Fetch public AWC METAR/TAF and Fukuoka FIR international SIGMET data."""
import datetime as dt
import json
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://aviationweather.gov/api/data"
STATIONS = {
    "kirishima": ["RJFK", "RJFM"],
    "tanegashima": ["RJFG", "RJFK"],
    "higashifuji": ["RJNS", "RJTT"],
    "narashino": ["RJAA", "RJTT"],
}


def fetch(endpoint, query):
    url = BASE + "/" + endpoint + "?" + urllib.parse.urlencode(query)
    request = urllib.request.Request(url, headers={"User-Agent": "freefall-weather/0.4"})
    with urllib.request.urlopen(request, timeout=45) as response:
        body = response.read(5_000_001)
    if len(body) > 5_000_000:
        raise ValueError("AWC response too large")
    data = json.loads(body)
    if not isinstance(data, list):
        raise ValueError("Unexpected AWC response")
    return data


def main():
    station_ids = sorted({station for values in STATIONS.values() for station in values})
    errors = []
    try:
        metars = fetch("metar", {"ids": ",".join(station_ids), "format": "json", "hours": 3})
    except Exception as exc:
        metars = []
        errors.append(f"METAR: {type(exc).__name__}: {exc}")
    try:
        tafs = fetch("taf", {"ids": ",".join(station_ids), "format": "json"})
    except Exception as exc:
        tafs = []
        errors.append(f"TAF: {type(exc).__name__}: {exc}")
    try:
        sigmets = [item for item in fetch("isigmet", {"format": "json"})
                   if item.get("firId") == "RJJJ"]
    except Exception as exc:
        sigmets = []
        errors.append(f"SIGMET: {type(exc).__name__}: {exc}")

    payload = {
        "schema_version": 1,
        "source": "US Aviation Weather Center public data API",
        "source_url": BASE,
        "retrieved_utc": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "station_groups": STATIONS,
        "metars": metars,
        "tafs": tafs,
        "sigmets_fukuoka_fir": sigmets,
        "limitations": "Airport METAR/TAF and FIR-wide SIGMET; not a training-area observation or go/no-go decision.",
        "errors": errors,
        "status": "ok" if metars or tafs or sigmets else "unavailable",
    }
    Path("data").mkdir(exist_ok=True)
    Path("data/aviation_weather.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"aviation weather: METAR={len(metars)} TAF={len(tafs)} SIGMET={len(sigmets)} errors={len(errors)}")
    if payload["status"] != "ok":
        raise SystemExit("No aviation weather data available")


if __name__ == "__main__":
    main()
