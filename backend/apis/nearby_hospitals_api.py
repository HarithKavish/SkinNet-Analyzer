import logging
import math
import time

import requests

logger = logging.getLogger("info_logger")

USER_AGENT = "SkinNet-Analyzer/1.0 (skin disease diagnosis app)"
SEARCH_RADIUS_M = 15000
MAX_RESULTS = 5
CACHE_TTL_SECONDS = 3600

# Free public OSM services rate-limit by IP, and Render's free tier shares outbound IPs
# with many other apps, so any single provider can start returning 429/406. Try several.
OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

_cache = {}  # (rounded lat, rounded lon) -> (stored_at, hospitals); per worker process


def _distance_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 12742 * math.asin(math.sqrt(a))


def _from_overpass(url, lat, lon):
    query = (
        f"[out:json][timeout:10];"
        f'nwr["amenity"="hospital"](around:{SEARCH_RADIUS_M},{lat},{lon});'
        f"out center 60;"
    )
    response = requests.post(url, data={"data": query}, headers={"User-Agent": USER_AGENT}, timeout=12)
    response.raise_for_status()

    found = []
    for element in response.json().get("elements", []):
        point = element if "lat" in element else element.get("center", {})
        if "lat" not in point or "lon" not in point:
            continue
        found.append((element.get("tags", {}).get("name"), float(point["lat"]), float(point["lon"])))
    return found


def _from_nominatim(lat, lon):
    delta = 0.15  # ~15-20km bounding box
    params = {
        "q": "hospital",
        "format": "json",
        "limit": MAX_RESULTS,
        "bounded": 1,
        "viewbox": f"{lon - delta},{lat + delta},{lon + delta},{lat - delta}",
    }
    response = requests.get(NOMINATIM_URL, params=params, headers={"User-Agent": USER_AGENT}, timeout=10)
    response.raise_for_status()
    return [(r.get("name") or r.get("display_name"), float(r["lat"]), float(r["lon"])) for r in response.json()]


def get_nearby_hospitals(coords):
    """Finds hospitals near given (lat, lon), nearest first. Returns [] if every provider fails."""

    if not coords or coords == (None, None):
        logger.warning("Hospital lookup skipped: no coordinates for the given location")
        return []

    lat, lon = coords
    cache_key = (round(lat, 2), round(lon, 2))
    cached = _cache.get(cache_key)
    if cached and time.monotonic() - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    # Nominatim is fast (1-2s) and fails instantly when rate-limited; Overpass is slower (~10s)
    providers = [(NOMINATIM_URL, lambda: _from_nominatim(lat, lon))]
    providers += [(url, lambda u=url: _from_overpass(u, lat, lon)) for url in OVERPASS_MIRRORS]

    for name, fetch in providers:
        try:
            found = fetch()
        except (requests.exceptions.RequestException, ValueError, KeyError) as e:
            logger.warning(f"Hospital lookup via {name} failed for {coords}: {e}")
            continue

        if not found:
            logger.warning(f"Hospital lookup via {name} returned no results near {coords}")
            continue

        # Named hospitals first, then nearest
        found.sort(key=lambda h: (not h[0], _distance_km(lat, lon, h[1], h[2])))
        hospitals = [
            {"tags": {"name": h_name or "Hospital"}, "lat": h_lat, "lon": h_lon}
            for h_name, h_lat, h_lon in found[:MAX_RESULTS]
        ]
        logger.info(f"Hospital lookup via {name} found {len(hospitals)} near {coords}")
        _cache[cache_key] = (time.monotonic(), hospitals)
        return hospitals

    return []
