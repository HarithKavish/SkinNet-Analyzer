import requests
import urllib.parse
import logging

logger = logging.getLogger("info_logger")

def get_city_coordinates(location: str, timeout: int = 10):
    """Fetch city latitude and longitude using Open-Meteo API (Free & No API Key)."""
    if not location.strip():
        logger.warning("Empty location passed to get_city_coordinates.")
        return None, None

    open_meteo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(location)}&count=1"

    try:
        response = requests.get(open_meteo_url, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        if "results" in data and data["results"]:
            lat = data["results"][0].get("latitude")
            lon = data["results"][0].get("longitude")
            logger.info(f"Fetched coordinates for {location}: ({lat}, {lon})")
            return lat, lon
        else:
            logger.warning(f"No coordinates found for location: {location}")
            return None, None

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching coordinates for {location}: {e}")
        return None, None
