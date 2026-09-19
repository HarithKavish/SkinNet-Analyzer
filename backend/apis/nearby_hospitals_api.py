import logging
import time

import requests

logger = logging.getLogger("info_logger")


def get_nearby_hospitals(coords):
    """Finds hospitals near given (lat, lon) using OpenStreetMap Nominatim search."""

    if not coords or coords == (None, None):
        logger.warning("Hospital lookup skipped: no coordinates for the given location")
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

    # Nominatim is a shared free service that can rate-limit or hiccup, so try twice.
    for attempt in range(2):
        try:
            response = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params=params,
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()

            results = response.json()[:5]
            if not results:
                logger.warning(f"Nominatim returned no hospitals near {coords}")
            return [
                {
                    "tags": {"name": r.get("name") or r.get("display_name")},
                    "lat": float(r["lat"]),
                    "lon": float(r["lon"]),
                }
                for r in results
            ]

        except requests.exceptions.RequestException as e:
            logger.warning(f"Hospital lookup attempt {attempt + 1} failed for {coords}: {e}")
            if attempt == 0:
                time.sleep(1.5)

    return []
