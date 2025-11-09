from fastapi import FastAPI
import asyncio
import json
from math import radians, sin, cos, asin, sqrt
from urllib import request as urlrequest
from urllib import parse as urlparse
from urllib.error import URLError, HTTPError

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "You've reached the Kind-To-Homeless API"}


@app.get("/nearby")
async def nearby(latitude: float, longitude: float, radius: float):
    """Return up to 20 nearby public toilets (amenity=toilets) within the given radius (miles).
    Args:
        latitude: Latitude of the center point.
        longitude: Longitude of the center point.
        radius: Search radius in miles.
    Returns:
        JSON with list of toilets (id, latitude, longitude) limited to 20, sorted by nearest first.
    """
    overpass_url = "https://overpass-api.de/api/interpreter"
    # Overpass QL query: search nodes/ways/relations (nwr) with amenity=toilets around point.
    # Convert miles to meters for Overpass API (1 mile = 1609.34 meters)
    radius_meters = int(radius * 1609.34)
    query = f"""[out:json];
nwr(around:{radius_meters},{latitude},{longitude})["amenity"="toilets"];
out center tags;"""

    def _fetch():
        data = urlparse.urlencode({"data": query}).encode()
        req = urlrequest.Request(
            overpass_url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urlrequest.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            if not body:
                raise ValueError("Empty response from Overpass API")
            try:
                return json.loads(body)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON response: {body[:200]}")

    # Haversine distance in miles
    def _dist_m(lat1: float, long1: float, lat2: float, long2: float) -> float:
        R = 3958.8  # Earth radius in miles
        dlat = radians(lat2 - lat1)
        dlon = radians(long2 - long1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        return R * c

    try:
        data = await asyncio.to_thread(_fetch)
    except (URLError, HTTPError, TimeoutError, ValueError) as e:
        return {"error": "Failed to fetch data from Overpass API", "detail": str(e)}

    items = []
    for el in data.get("elements", []):
        # Node has lat/lon directly. Way/Relation may have a 'center' field.
        el_latitude = el.get("lat") or (el.get("center") or {}).get("lat")
        el_longitude = el.get("lon") or (el.get("center") or {}).get("lon")
        if el_latitude is None or el_longitude is None:
            continue
        try:
            d = _dist_m(latitude, longitude, float(el_latitude), float(el_longitude))
        except Exception:
            continue

        items.append({
            "id": el.get("id"),
            "latitude": el_latitude,
            "longitude": el_longitude,
            "_d": d
        })

    # Sort by distance and limit to 20
    items.sort(key=lambda x: x["_d"])  # nearest first
    toilets = [
        {
            "id": it["id"],
            "latitude": it["latitude"],
            "longitude": it["longitude"]
        }
        for it in items[:20]
    ]

    return {"toilets": toilets}
