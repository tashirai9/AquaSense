"""Weather utility backed by OpenWeatherMap."""

from datetime import datetime
import requests

from aquasense.config import OPENWEATHER_API_KEY


def _season_from_month(month):
    """Infer season from month; inputs: month number; output: season string."""
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    if month in (9, 10, 11):
        return "autumn"
    return "winter"


def get_weather(city):
    """Fetch weather for a city; inputs: city name; output: dict with temperature, description, season."""
    season = _season_from_month(datetime.now().month)
    defaults = {"temperature": None, "description": "Weather unavailable", "season": season}
    if not city or OPENWEATHER_API_KEY == "your_api_key_here":
        return defaults
    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": OPENWEATHER_API_KEY, "units": "metric"},
            timeout=5,
        )
        response.raise_for_status()
        payload = response.json()
        return {
            "temperature": payload.get("main", {}).get("temp"),
            "description": payload.get("weather", [{}])[0].get("description", "Weather unavailable"),
            "season": season,
        }
    except Exception:
        return defaults
