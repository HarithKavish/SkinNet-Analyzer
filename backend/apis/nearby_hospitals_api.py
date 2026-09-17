import requests


def get_nearby_hospitals(coords):
    """Finds hospitals near given (lat, lon) using OpenStreetMap Nominatim search."""

    if not coords or coords == (None, None):
        return []

    lat, lon = coords
    delta = 0.15  # ~15-20km bounding box around the point, roughly matching the old 10km radius

    params = {
        "q": "hospital",
        "format": "json",
        "limit": 5,
        "bounded": 1,
        "viewbox": f"{lon - delta},{lat + delta},{lon + delta},{lat - delta}",
    }
    headers = {"User-Agent": "SkinNet-Analyzer/1.0 (skin disease diagnosis app)"}

    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params=params,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()

        results = response.json()[:5]
        return [
            {
                "tags": {"name": r.get("name") or r.get("display_name")},
                "lat": float(r["lat"]),
                "lon": float(r["lon"]),
            }
            for r in results
        ]

    except requests.exceptions.RequestException:
        return []
