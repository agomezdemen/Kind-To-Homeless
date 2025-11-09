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


@app.get("/info")
async def info():
    """Return available features that can be searched."""
    return {
        "available_features": [
            {"feature": "toilets", "description": "Public toilets"},
            {"feature": "shower", "description": "Public showers"},
            {"feature": "drinking_water", "description": "Drinking water fountains"},
            {"feature": "water_tap", "description": "Water taps"},
            {"feature": "place_of_worship", "description": "Places of worship"},
            {"feature": "social_facility", "description": "Social facilities (general)"},
            {"feature": "shelter", "description": "Shelters"},
            {"feature": "soup_kitchen", "description": "Soup kitchens"},
            {"feature": "food_bank", "description": "Food banks"},
            {"feature": "clothing_bank", "description": "Clothing banks"},
            {"feature": "outreach", "description": "Outreach services"},
            {"feature": "homeless_services", "description": "Services specifically for homeless"},
            {"feature": "laundry", "description": "Laundromats"},
            {"feature": "public_bath", "description": "Public baths"},
            {"feature": "day_care", "description": "Day care facilities"},
            {"feature": "community_centre", "description": "Community centres"},
            {"feature": "social_centre", "description": "Social centres"},
            {"feature": "welfare", "description": "Welfare services"}
        ],
        "usage": "Pass 'feature' parameter to /nearby endpoint (e.g., feature=toilets, feature=shelter)"
    }


@app.get("/nearby")
async def nearby(latitude: float, longitude: float, radius: float, feature: str = "toilets", limit: int = 20):
    """Return nearby facilities within the given radius (miles).
    Args:
        latitude: Latitude of the center point.
        longitude: Longitude of the center point.
        radius: Search radius in miles.
        feature: Type of feature to search for (e.g., 'toilets', 'shelter', 'drinking_water').
                 Default is 'toilets'. See /info for available options.
        limit: Maximum number of results to return. Default is 20.
    Returns:
        JSON with list of facilities (id, latitude, longitude, name, address, distance) limited by the specified limit, sorted by nearest first.
    """
    # Map simple feature names to OSM tags
    feature_map = {
        "toilets": [("amenity", "toilets")],
        "shower": [("amenity", "shower")],
        "drinking_water": [("amenity", "drinking_water"), ("drinking_water", "yes")],
        "water_tap": [("man_made", "water_tap")],
        "place_of_worship": [("amenity", "place_of_worship")],
        "social_facility": [("amenity", "social_facility")],
        "shelter": [("social_facility", "shelter")],
        "soup_kitchen": [("social_facility", "soup_kitchen")],
        "food_bank": [("social_facility", "food_bank")],
        "clothing_bank": [("social_facility", "clothing_bank")],
        "outreach": [("social_facility", "outreach")],
        "homeless_services": [("social_facility:for", "homeless")],
        "laundry": [("shop", "laundry"), ("amenity", "lavoir")],
        "day_care": [("social_facility", "day_care")],
        "community_centre": [("amenity", "community_centre"), ("social_facility", "community_centre")],
        "social_centre": [("amenity", "social_centre")],
        "welfare": [("amenity", "welfare")]
    }

    if feature not in feature_map:
        return {
            "error": f"Unknown feature: {feature}",
            "available_features": list(feature_map.keys()),
            "hint": "Use /info endpoint to see all available features"
        }

    overpass_url = "https://overpass-api.de/api/interpreter"
    # Convert miles to meters for Overpass API (1 mile = 1609.34 meters)
    radius_meters = int(radius * 1609.34)

    # Build query parts for the requested feature (some features have multiple OSM tag combinations)
    feature_queries = []
    for key, value in feature_map[feature]:
        feature_queries.append(f'  nwr(around:{radius_meters},{latitude},{longitude})["{key}"="{value}"];')

    # Single query to get both the requested features AND nearby named buildings
    query = f"""[out:json];
(
{''.join(feature_queries)}
  nwr(around:{radius_meters},{latitude},{longitude})[name][building];
  nwr(around:{radius_meters},{latitude},{longitude})[name][shop];
  nwr(around:{radius_meters},{latitude},{longitude})[name][amenity];
);
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

    def _reverse_geocode(lat: float, lon: float) -> str:
        """Query self-hosted Nominatim API for address."""
        nominatim_url = f"http://nominatim:8080/reverse?format=json&lat={lat}&lon={lon}"
        try:
            req = urlrequest.Request(nominatim_url, method="GET")
            with urlrequest.urlopen(req, timeout=10) as resp:
                body = resp.read().decode("utf-8")
                if not body:
                    return ""
                result = json.loads(body)
                # Return the display_name as a string
                return result.get("display_name", "")
        except Exception as e:
            # Silently fail and return empty - Nominatim might be unavailable
            return ""

    def _find_nearest_named_place(toilet_lat: float, toilet_lon: float, named_places: list) -> str:
        """Find the closest named place to a toilet."""
        min_dist = float('inf')
        nearest_name = ""

        for place in named_places:
            place_lat = place.get("lat") or (place.get("center") or {}).get("lat")
            place_lon = place.get("lon") or (place.get("center") or {}).get("lon")
            if place_lat is None or place_lon is None:
                continue

            try:
                dist = _dist_m(toilet_lat, toilet_lon, float(place_lat), float(place_lon))
                # Only consider places within 150 meters
                if dist < 0.093 and dist < min_dist:  # 0.093 miles ≈ 150 meters
                    min_dist = dist
                    nearest_name = place.get("tags", {}).get("name", "")
            except Exception:
                continue

        return nearest_name

    try:
        data = await asyncio.to_thread(_fetch)
    except (URLError, HTTPError, TimeoutError, ValueError) as e:
        return {"error": "Failed to fetch data from Overpass API", "detail": str(e)}

    # Separate requested facilities from named places
    facilities_list = []
    named_places = []

    # Get the tag combinations for this feature
    feature_tags = feature_map[feature]

    for el in data.get("elements", []):
        el_latitude = el.get("lat") or (el.get("center") or {}).get("lat")
        el_longitude = el.get("lon") or (el.get("center") or {}).get("lon")
        if el_latitude is None or el_longitude is None:
            continue

        tags = el.get("tags", {})

        # Check if it matches any of the requested feature's tag combinations
        is_match = False
        for key, value in feature_tags:
            if tags.get(key) == value:
                is_match = True
                break

        if is_match:
            try:
                d = _dist_m(latitude, longitude, float(el_latitude), float(el_longitude))
            except Exception:
                continue

            facilities_list.append({
                "id": el.get("id"),
                "latitude": el_latitude,
                "longitude": el_longitude,
                "tags": tags,
                "_d": d
            })
        # Otherwise it's a named place
        elif tags.get("name"):
            named_places.append(el)

    # Sort by distance and apply limit
    facilities_list.sort(key=lambda x: x["_d"])  # nearest first

    # Process each facility
    facilities = []
    for it in facilities_list[:limit]:
        address = await asyncio.to_thread(_reverse_geocode, it["latitude"], it["longitude"])

        # Use the facility's name tag if it exists
        tags = it.get("tags", {})
        name = tags.get("name")

        # If no name tag, find the nearest named place
        if not name:
            name = _find_nearest_named_place(it["latitude"], it["longitude"], named_places)

        # Final fallbacks
        if not name:
            name = tags.get("operator") or f"{feature.replace('_', ' ').title()}"

        facilities.append({
            "id": it["id"],
            "latitude": it["latitude"],
            "longitude": it["longitude"],
            "name": name,
            "address": address,
            "distance": round(it["_d"], 3)  # Distance in miles, rounded to 3 decimals
        })

    return {"results": facilities}
