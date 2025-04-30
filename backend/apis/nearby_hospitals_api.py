import requests

def get_nearby_hospitals(coords):
    """Finds hospitals near given (lat, lon) using OpenStreetMap Overpass API."""

    if not coords or coords == (None, None):
        return []

    lat, lon = coords

    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    node["amenity"="hospital"](around:10000,{lat},{lon});
    out body;
    """

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.post(overpass_url, data=query, headers=headers, timeout=10)
        response.raise_for_status()

        hospitals = response.json().get("elements", [])[:5]  # Take up to 5 hospitals
        return hospitals

    except requests.exceptions.RequestException:
        return []
