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

    def _reverse_geocode(lat: float, lon: float) -> dict:
        """Query self-hosted Nominatim API for location name and address."""
        nominatim_url = f"http://nominatim:8080/reverse?format=json&lat={lat}&lon={lon}"
        try:
            req = urlrequest.Request(nominatim_url, method="GET")
            with urlrequest.urlopen(req, timeout=10) as resp:
                body = resp.read().decode("utf-8")
                result = json.loads(body)
                return {
                    "name": result.get("display_name", ""),
                    "address": result.get("address", {})
                }
        except Exception:
            return {"name": "", "address": {}}

    def _find_nearby_named_place(lat: float, lon: float) -> str:
        """Find the name of the closest named building/POI using Overpass API."""
        overpass_url = "https://overpass-api.de/api/interpreter"
        # Search for nearby named features within 50 meters
        query = f"""[out:json];
(
  nwr(around:50,{lat},{lon})[name];
  nwr(around:50,{lat},{lon})["addr:housename"];
);
out center tags 1;"""

        try:
            data = urlparse.urlencode({"data": query}).encode()
            req = urlrequest.Request(
                overpass_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                method="POST",
            )
            with urlrequest.urlopen(req, timeout=10) as resp:
                body = resp.read().decode("utf-8")
                result = json.loads(body)
                elements = result.get("elements", [])
                if elements:
                    # Return the first named element found
                    tags = elements[0].get("tags", {})
                    return tags.get("name") or tags.get("addr:housename", "")
        except Exception:
            pass
        return ""

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

    # Reverse geocode each location and find nearby named places
    toilets = []
    for it in items[:20]:
        location_info = await asyncio.to_thread(_reverse_geocode, it["latitude"], it["longitude"])
        place_name = await asyncio.to_thread(_find_nearby_named_place, it["latitude"], it["longitude"])

        # Use the named place if found, otherwise fall back to a generic description
        display_name = place_name if place_name else location_info.get("address", {}).get("road", "Unknown Location")

        toilets.append({
            "id": it["id"],
            "latitude": it["latitude"],
            "longitude": it["longitude"],
            "name": display_name,
            "address": location_info["address"]
        })

    return {"toilets": toilets}
