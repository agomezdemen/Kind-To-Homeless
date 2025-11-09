from fastapi import FastAPI
import asyncio
import json
import sys
import os
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
            {"feature": "community_centre", "description": "Community centres"},
            {"feature": "social_centre", "description": "Social centres"},
            {"feature": "welfare", "description": "Welfare services"}
        ],
        "usage": "Pass 'feature' parameter to /nearby endpoint (e.g., feature=toilets, feature=shelter)"
    }


@app.get("/nearby")
async def nearby(latitude: float, longitude: float, radius: float = 3.0, feature: str = "all", limit: int = 3, search: str = None):
    """Return nearby facilities within the given radius (miles).
    Args:
        latitude: Latitude of the center point.
        longitude: Longitude of the center point.
        radius: Search radius in miles. Default is 3 miles.
        feature: Type of feature to search for (e.g., 'toilets', 'shelter', 'drinking_water').
                 Default is 'all' which returns 3 results of each feature type. See /info for available options.
        limit: Maximum number of results to return per feature type. Default is 3.
        search: Optional natural language search string. If provided, uses AI to match the search to relevant features.
    Returns:
        JSON with list of facilities (id, latitude, longitude, name, address, distance, feature_type) limited by the specified limit, sorted by nearest first.
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
        "social_centre": [("amenity", "social_centre")],
        "welfare": [("amenity", "welfare")]
    }

    # Handle search parameter with Ollama
    if search:
        print(f"Search parameter received: '{search}'")
        def _query_ollama(search_string: str, features: list) -> list:
            """Query Ollama to match search string to feature names."""
            ollama_url = "http://ollama:11434/api/generate"

            # Format features list clearly
            features_list = '\n'.join([f"- {f}" for f in features])

            prompt = f"""Match "{search_string}" to features from this list. Return ONLY exact feature names.

Available features:
{features_list}

Rules:
- Return exact names only (with underscores like food_bank)
- Multiple matches: separate with comma
- No quotes, no extra words, no punctuation at end

Examples:
Search: bathroom → toilets
Search: wash → shower
Search: food → food_bank, soup_kitchen
Search: sleep → shelter

Match for "{search_string}":"""

            payload = {
                "model": "nemotron:70B",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1
                }
            }

            try:
                req = urlrequest.Request(
                    ollama_url,
                    data=json.dumps(payload).encode('utf-8'),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urlrequest.urlopen(req, timeout=30) as resp:
                    body = resp.read().decode('utf-8')
                    result = json.loads(body)
                    response_text = result.get("response", "").strip()

                    print(f"Ollama raw response: {response_text}")

                    # Clean up response - remove quotes, periods, and extra whitespace
                    response_text = response_text.replace('"', '').replace("'", "")
                    # Take only the first line if multiple lines
                    response_text = response_text.split('\n')[0].strip()
                    # Remove any trailing period
                    response_text = response_text.rstrip('.')

                    # Parse comma-separated feature names
                    matched_features = [f.strip() for f in response_text.split(',') if f.strip()]

                    # Filter to only valid features - handle plurals and close matches
                    valid_matches = []
                    for matched in matched_features:
                        # Exact match first
                        if matched in features:
                            valid_matches.append(matched)
                        # Try removing 's' for plural
                        elif matched.endswith('s') and matched[:-1] in features:
                            valid_matches.append(matched[:-1])
                        # Try adding underscore variations
                        elif matched.replace(' ', '_') in features:
                            valid_matches.append(matched.replace(' ', '_'))

                    # Remove duplicates while preserving order
                    valid_matches = list(dict.fromkeys(valid_matches))

                    print(f"Cleaned response: {response_text}")
                    print(f"Matched features after filtering: {valid_matches}")

                    return valid_matches
            except Exception as e:
                # Return empty list on error
                print(f"Ollama error: {e}")
                return []

        # Get matched features from Ollama
        available_features = list(feature_map.keys())
        print(f"About to query Ollama with search: '{search}', available features: {len(available_features)}")
        matched_features = await asyncio.to_thread(_query_ollama, search, available_features)

        print(f"Ollama returned matched features: {matched_features}")

        # If no features matched, return empty results
        if not matched_features:
            print("No features matched, returning empty results")
            return {"results": []}

        # Query each matched feature and combine results
        all_facilities = []
        for matched_feature in matched_features:
            # Recursive call to nearby with specific feature
            feature_results = await nearby(latitude, longitude, radius, matched_feature, limit, None)
            if "results" in feature_results:
                # Add feature_type to each result if not already present
                for result in feature_results["results"]:
                    if "feature_type" not in result:
                        result["feature_type"] = matched_feature
                all_facilities.extend(feature_results["results"])

        # Sort by distance and return
        all_facilities.sort(key=lambda x: x["distance"])
        return {"results": all_facilities}

    if feature != "all" and feature not in feature_map:
        return {
            "error": f"Unknown feature: {feature}",
            "available_features": list(feature_map.keys()) + ["all"],
            "hint": "Use /info endpoint to see all available features"
        }

    overpass_url = "https://overpass-api.de/api/interpreter"
    # Convert miles to meters for Overpass API (1 mile = 1609.34 meters)
    radius_meters = int(radius * 1609.34)

    # Build query parts for the requested feature (some features have multiple OSM tag combinations)
    feature_queries = []
    if feature == "all":
        # Query all feature types
        for feature_name, tags in feature_map.items():
            for key, value in tags:
                feature_queries.append(f'  nwr(around:{radius_meters},{latitude},{longitude})["{key}"="{value}"];')
    else:
        # Query only the requested feature
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
    # When feature="all", group by feature type
    facilities_by_type = {} if feature == "all" else {"single": []}
    named_places = []

    for el in data.get("elements", []):
        el_latitude = el.get("lat") or (el.get("center") or {}).get("lat")
        el_longitude = el.get("lon") or (el.get("center") or {}).get("lon")
        if el_latitude is None or el_longitude is None:
            continue

        tags = el.get("tags", {})

        # Check if it matches any feature type
        matched_feature = None
        if feature == "all":
            # Check against all feature types
            for feature_name, feature_tags in feature_map.items():
                for key, value in feature_tags:
                    if tags.get(key) == value:
                        matched_feature = feature_name
                        break
                if matched_feature:
                    break
        else:
            # Check against the requested feature only
            for key, value in feature_map[feature]:
                if tags.get(key) == value:
                    matched_feature = "single"
                    break

        if matched_feature:
            try:
                d = _dist_m(latitude, longitude, float(el_latitude), float(el_longitude))
            except Exception:
                continue

            if matched_feature not in facilities_by_type:
                facilities_by_type[matched_feature] = []

            facilities_by_type[matched_feature].append({
                "id": el.get("id"),
                "latitude": el_latitude,
                "longitude": el_longitude,
                "tags": tags,
                "_d": d,
                "feature_type": matched_feature if feature == "all" else feature
            })
        # Otherwise it's a named place
        elif tags.get("name"):
            named_places.append(el)

    # Sort each feature type by distance and apply limit per feature
    facilities = []
    for feature_type, facilities_list in facilities_by_type.items():
        facilities_list.sort(key=lambda x: x["_d"])  # nearest first

        # Process each facility (limited per feature type)
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
                feature_name = it["feature_type"]
                name = tags.get("operator") or f"{feature_name.replace('_', ' ').title()}"

            result = {
                "id": it["id"],
                "latitude": it["latitude"],
                "longitude": it["longitude"],
                "name": name,
                "address": address,
                "distance": round(it["_d"], 3),  # Distance in miles, rounded to 3 decimals
                "feature_type": it["feature_type"]
            }

            facilities.append(result)

    # When returning all features, sort by distance across all feature types
    if feature == "all":
        facilities.sort(key=lambda x: x["distance"])

    return {"results": facilities}


@app.get("/agent")
async def agent(url: str):
    """Use AI agent to scrape and analyze a URL for homeless resources.

    Args:
        url: The URL to analyze for shelter, meal, and service information.

    Returns:
        JSON object with findings including:
        - seed_url: The URL that was analyzed
        - findings: List of discovered resources with contact info
        - next_actions: Suggested next steps
        - uncertainties: Gaps or unconfirmed information
    """
    import requests

    # Add agent_util to path and import modules
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent_util'))
    import scrape_utils as su
    from tools import TOOLS

    # Load system prompt
    system_prompt_path = os.path.join(os.path.dirname(__file__), '..', 'agent_util', 'agent_system.txt')
    with open(system_prompt_path) as f:
        SYSTEM_PROMPT = f.read()

    VLLM_URL = "http://localhost:7545/v1/chat/completions"
    MODEL = "nvidia/Llama-3_3-Nemotron-Super-49B-v1_5"

    def call_tool(name, arguments):
        fn = getattr(su, name, None)
        if fn is None:
            raise ValueError(f"Unknown tool: {name}")
        return fn(**(arguments or {}))

    def chat(messages):
        payload = {
            "model": MODEL,
            "messages": messages,
            "tools": TOOLS,
            "tool_choice": "auto",
            "max_tokens": 512
        }
        r = requests.post(VLLM_URL, json=payload, timeout=120)
        r.raise_for_status()
        return r.json()

    # Build the query
    query = (
        f"Use tools to fetch {url}. Extract shelter or meal info, phones, hours, "
        "and return the most relevant links."
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query}
    ]

    # Agent loop - allow up to 4 tool use rounds
    for _ in range(4):
        resp = await asyncio.to_thread(chat, messages)
        msg = resp["choices"][0]["message"]
        tool_calls = msg.get("tool_calls", [])

        if not tool_calls:
            # Model answered directly - parse and return JSON
            content = msg.get("content", "")
            try:
                # Try to extract JSON from the response
                result = json.loads(content)
                return result
            except json.JSONDecodeError:
                # If not valid JSON, return as-is
                return {"response": content}

        # Dispatch each tool call and feed results back
        for tc in tool_calls:
            name = tc["function"]["name"]
            args = json.loads(tc["function"]["arguments"] or "{}")
            result = await asyncio.to_thread(call_tool, name, args)

            messages.append({
                "role": "assistant",
                "tool_calls": [tc]
            })
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "name": name,
                "content": json.dumps(result)
            })

    # If we exhausted the loop without a final answer
    return {"error": "Agent stopped after max tool steps", "messages": messages}



