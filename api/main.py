from fastapi import FastAPI
import asyncio
import json
import sys
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
    import time

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
        search_start = time.time()
        print(f"Search parameter received: '{search}'")
        def _query_ollama(search_string: str, features: list) -> list:
            """Query Ollama to match search string to feature names."""
            ollama_start = time.time()
            ollama_host = os.environ.get("OLLAMA_HOST", "http://host.docker.internal:11434")
            ollama_url = f"{ollama_host}/api/generate"

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
                print(f"Calling Ollama at {ollama_url}...")
                with urlrequest.urlopen(req, timeout=60) as resp:
                    body = resp.read().decode('utf-8')
                    result = json.loads(body)
                    response_text = result.get("response", "").strip()

                    ollama_elapsed = time.time() - ollama_start

                    # Extract performance metrics from Ollama response
                    eval_count = result.get("eval_count", 0)
                    eval_duration = result.get("eval_duration", 0) / 1e9  # Convert nanoseconds to seconds
                    tokens_per_sec = eval_count / eval_duration if eval_duration > 0 else 0

                    print(f"Ollama inference time: {ollama_elapsed:.3f}s")
                    print(f"Ollama tokens generated: {eval_count}, speed: {tokens_per_sec:.1f} tokens/s")
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
                print(f"Ollama error: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
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
        query_start = time.time()
        for matched_feature in matched_features:
            feature_start = time.time()
            print(f"Querying feature: {matched_feature} with lat={latitude}, lon={longitude}, radius={radius}, limit={limit}")
            # Recursive call to nearby with specific feature (search=None to avoid re-matching)
            feature_results = await nearby(latitude, longitude, radius, matched_feature, limit, None)
            feature_elapsed = time.time() - feature_start
            result_count = len(feature_results.get('results', []))
            print(f"Feature {matched_feature} returned {result_count} results in {feature_elapsed:.3f}s")
            if "results" in feature_results:
                # Add feature_type to each result if not already present
                for result in feature_results["results"]:
                    if "feature_type" not in result:
                        result["feature_type"] = matched_feature
                all_facilities.extend(feature_results["results"])

        # Sort by distance and return
        all_facilities.sort(key=lambda x: x["distance"])
        total_elapsed = time.time() - search_start
        query_elapsed = time.time() - query_start
        ollama_elapsed = total_elapsed - query_elapsed
        print(f"Returning total of {len(all_facilities)} facilities from search")
        print(f"Total search time: {total_elapsed:.3f}s (Ollama: {ollama_elapsed:.3f}s, DB queries: {query_elapsed:.3f}s)")
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
        fetch_start = time.time()
        data = await asyncio.to_thread(_fetch)
        fetch_elapsed = time.time() - fetch_start
        print(f"Overpass API fetch time: {fetch_elapsed:.3f}s")
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
    facilities_to_process = []

    # First, collect all facilities that need processing
    for feature_type, facilities_list in facilities_by_type.items():
        facilities_list.sort(key=lambda x: x["_d"])  # nearest first
        facilities_to_process.extend(facilities_list[:limit])

    # Parallelize address lookups for all facilities at once
    if facilities_to_process:
        geocode_start = time.time()
        address_tasks = [
            asyncio.to_thread(_reverse_geocode, it["latitude"], it["longitude"])
            for it in facilities_to_process
        ]
        addresses = await asyncio.gather(*address_tasks)
        geocode_elapsed = time.time() - geocode_start
        print(f"Nominatim geocoding ({len(facilities_to_process)} addresses in parallel): {geocode_elapsed:.3f}s")

        # Now process each facility with its pre-fetched address
        for it, address in zip(facilities_to_process, addresses):
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


@app.get("/search")
async def search(query: str, max_results: int = 5):
    """Search DuckDuckGo and return top result URLs.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return. Default is 5.

    Returns:
        JSON object with list of search result URLs.
    """
    try:
        from ddgs import DDGS

        def _search():
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                return [{"url": r["href"], "title": r["title"]} for r in results]

        search_results = await asyncio.to_thread(_search)
        return {"results": search_results}

    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


@app.get("/prompt_search")
async def prompt_search(latitude: float = 32.9859, longitude: float = -96.7503):
    """Use Ollama to generate search queries from prompt-search.txt, then search and return URLs.

    Args:
        latitude: Latitude for city identification. Default is Richardson, Texas.
        longitude: Longitude for city identification. Default is Richardson, Texas.

    Returns:
        JSON object with:
        - search_queries: List of search query strings generated by Ollama
        - urls: List of all search result URLs from those queries
    """
    try:
        # Get city name from coordinates using Nominatim reverse geocoding
        def _get_city_name(lat: float, lon: float) -> str:
            """Query Nominatim API to get city name from coordinates."""
            nominatim_url = f"http://nominatim:8080/reverse?format=json&lat={lat}&lon={lon}"
            try:
                req = urlrequest.Request(nominatim_url, method="GET")
                with urlrequest.urlopen(req, timeout=10) as resp:
                    body = resp.read().decode("utf-8")
                    if not body:
                        return "Richardson, Texas"  # fallback
                    result = json.loads(body)
                    address = result.get("address", {})
                    # Try to extract city and state
                    city = address.get("city") or address.get("town") or address.get("village") or address.get("municipality")
                    state = address.get("state")
                    if city and state:
                        return f"{city}, {state}"
                    elif city:
                        return city
                    else:
                        return "Richardson, Texas"  # fallback
            except Exception:
                return "Richardson, Texas"  # fallback on error

        # Get city name
        city_name = await asyncio.to_thread(_get_city_name, latitude, longitude)

        # Load the prompt from file
        # In Docker, WORKDIR is /app, so we can use absolute path
        prompt_path = '/app/agentic_prompts/prompt-search.txt'
        # Fallback for local development
        if not os.path.exists(prompt_path):
            prompt_path = os.path.join(os.path.dirname(__file__), '..', 'agentic_prompts', 'prompt-search.txt')

        with open(prompt_path, 'r') as f:
            prompt = f.read()

        # Replace [CITY] placeholder with actual city name
        prompt = prompt.replace('[CITY]', city_name)

        # Call Ollama to generate search queries
        ollama_host = os.environ.get("OLLAMA_HOST", "http://host.docker.internal:11434")
        ollama_url = f"{ollama_host}/api/generate"

        payload = {
            "model": "nemotron:70B",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7
            }
        }

        def _query_ollama():
            req = urlrequest.Request(
                ollama_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urlrequest.urlopen(req, timeout=60) as resp:
                body = resp.read().decode('utf-8')
                result = json.loads(body)
                return result.get("response", "").strip()

        # Get generated queries from Ollama
        response_text = await asyncio.to_thread(_query_ollama)

        # Parse queries - split on both newlines and commas
        # First replace newlines with commas, then split on commas
        response_text = response_text.replace('\n', ',')
        queries = [q.strip() for q in response_text.split(',') if q.strip()]
        # Search each query and collect all URLs (50 per query)
        all_results_by_query = {}
        for query in queries:
            # Append " November 2025" to each search query
            search_query = f"{query} November 2025"
            search_results = await search(search_query, max_results=50)
            if "results" in search_results:
                all_results_by_query[query] = search_results["results"]

        # Load URL selector prompt
        selector_prompt_path = '/app/agentic_prompts/prompt-url-selector.txt'
        if not os.path.exists(selector_prompt_path):
            selector_prompt_path = os.path.join(os.path.dirname(__file__), '..', 'agentic_prompts', 'prompt-url-selector.txt')

        with open(selector_prompt_path, 'r') as f:
            selector_prompt_template = f.read()

        # For each query, filter URLs using Ollama
        def _filter_urls(query_text: str, results: list) -> list:
            """Use Ollama to filter URLs for relevance."""
            if not results:
                return []

            # Format URLs with titles for the prompt
            urls_text = '\n'.join([f"{r['title']}\n{r['url']}" for r in results])

            # Build the filtering prompt
            filter_prompt = selector_prompt_template.replace('{query}', query_text)
            filter_prompt = filter_prompt.replace('{urls}', urls_text)

            payload = {
                "model": "nemotron:70B",
                "prompt": filter_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3  # Lower temperature for more focused filtering
                }
            }

            req = urlrequest.Request(
                ollama_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urlrequest.urlopen(req, timeout=60) as resp:
                body = resp.read().decode('utf-8')
                result = json.loads(body)
                response = result.get("response", "").strip()

                # If response is "NONE", return empty list
                if response.upper() == "NONE":
                    return []

                # Parse URLs from response (one per line)
                filtered_urls = [line.strip() for line in response.split('\n') if line.strip() and line.strip().startswith('http')]

                # Match filtered URLs back to original results to keep titles
                filtered_results = []
                for url in filtered_urls:
                    for r in results:
                        if r['url'] == url:
                            filtered_results.append(r)
                            break

                return filtered_results

        # Filter URLs for each query in parallel
        filter_tasks = [
            asyncio.to_thread(_filter_urls, query, results)
            for query, results in all_results_by_query.items()
        ]
        filtered_results_list = await asyncio.gather(*filter_tasks)

        # Combine all filtered results
        final_urls = []
        seen_urls = set()
        for query, filtered_results in zip(all_results_by_query.keys(), filtered_results_list):
            for result in filtered_results:
                # Deduplicate URLs
                if result['url'] not in seen_urls:
                    seen_urls.add(result['url'])
                    final_urls.append({
                        "url": result['url'],
                        "title": result['title'],
                        "query": query
                    })

        return {"search_queries": queries, "urls": final_urls, "total_filtered": len(final_urls)}

    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


@app.get("/scrape_events")
async def scrape_events(latitude: float = 32.9859, longitude: float = -96.7503):
    """Scrape event information from URLs found via prompt_search.

    This endpoint:
    1. Calls /prompt_search to find relevant URLs for homeless services and food distribution events
    2. Scrapes each URL to extract readable text content
    3. Returns structured JSON with page content, contact info, and metadata

    Args:
        latitude: Latitude for location-based search. Default is Richardson, Texas.
        longitude: Longitude for location-based search. Default is Richardson, Texas.

    Returns:
        JSON object with:
        - search_queries: List of search queries used
        - total_urls: Number of URLs processed
        - scraped_pages: List of scraped page data including:
            - url: The page URL
            - title: Page title
            - query: Original search query that found this URL
            - text_content: Cleaned plaintext of the page (first 3000 chars)
            - contacts: Extracted emails, phones, and hours
            - success: Whether scraping succeeded
            - error: Error message if scraping failed
    """
    import time

    try:
        start_time = time.time()

        # Step 1: Call prompt_search to get relevant URLs
        print(f"Calling prompt_search with lat={latitude}, lon={longitude}")
        search_results = await prompt_search(latitude, longitude)

        if "error" in search_results:
            return {"error": "Failed to get search results", "detail": search_results}

        urls_to_scrape = search_results.get("urls", [])
        search_queries = search_results.get("search_queries", [])

        if not urls_to_scrape:
            return {
                "search_queries": search_queries,
                "total_urls": 0,
                "scraped_pages": [],
                "message": "No URLs found to scrape"
            }

        print(f"Found {len(urls_to_scrape)} URLs to scrape")

        # Step 2: Import scraping utilities
        # Add parent directory to path to import from agent_util
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        from agent_util.scrape_utils import get_html, html_to_text, extract_title, extract_contacts

        # Step 3: Scrape each URL
        def _scrape_url(url_info: dict) -> dict:
            """Scrape a single URL and extract content."""
            url = url_info['url']
            try:
                print(f"Scraping: {url}")
                html = get_html(url, timeout=20)
                title = extract_title(html)
                text = html_to_text(html)

                # Extract contact information
                contacts = extract_contacts(text)

                # Truncate text to first 3000 characters for readability
                text_preview = text[:3000] + "..." if len(text) > 3000 else text

                return {
                    "url": url,
                    "title": title,
                    "query": url_info.get('query', ''),
                    "text_content": text_preview,
                    "full_text_length": len(text),
                    "contacts": contacts,
                    "success": True
                }
            except Exception as e:
                print(f"Error scraping {url}: {type(e).__name__}: {e}")
                return {
                    "url": url,
                    "title": url_info.get('title', ''),
                    "query": url_info.get('query', ''),
                    "text_content": "",
                    "full_text_length": 0,
                    "contacts": {"emails": [], "phones": [], "hours": []},
                    "success": False,
                    "error": f"{type(e).__name__}: {str(e)}"
                }

        # Scrape all URLs in parallel
        print("Starting parallel scraping...")
        scrape_tasks = [asyncio.to_thread(_scrape_url, url_info) for url_info in urls_to_scrape]
        scraped_pages = await asyncio.gather(*scrape_tasks)

        # Count successful scrapes
        successful = sum(1 for page in scraped_pages if page.get("success"))
        failed = len(scraped_pages) - successful

        elapsed = time.time() - start_time
        print(f"Scraping complete: {successful} successful, {failed} failed in {elapsed:.2f}s")

        return {
            "search_queries": search_queries,
            "total_urls": len(urls_to_scrape),
            "successful_scrapes": successful,
            "failed_scrapes": failed,
            "scraped_pages": scraped_pages,
            "elapsed_seconds": round(elapsed, 2)
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "type": type(e).__name__}


@app.post("/extract_event")
async def extract_event(content: str):
    """Extract event information from scraped web page content using Ollama.

    This endpoint:
    1. Uses Ollama to analyze the content and determine if it describes a valid event
    2. If valid, extracts event details (name, date, address, summary)
    3. Geocodes the address using Nominatim to get GPS coordinates
    4. Returns structured event JSON or null if no valid event found

    Args:
        content: The scraped web page text content to analyze

    Returns:
        JSON object with:
        - event: Event object with properties (Name, Date, address, latitude, longitude, summary)
                 or null if no valid event was found
        - reasoning: Brief explanation of why event was/wasn't created
    """
    import time

    try:
        start_time = time.time()

        # Build prompt for Ollama to extract event information
        extraction_prompt = f"""You are an event extraction assistant. Analyze the following web page content to determine if it describes a specific, actionable food distribution event, meal service, or homeless aid event.

Requirements for a valid event:
- Must have a specific date or recurring schedule (e.g., "November 15th", "Every Tuesday at 5pm")
- Must have a physical location/address where the event occurs
- Must be related to food distribution, meals, shelter, or direct aid for homeless/needy individuals
- Must be current or upcoming (late 2024 or 2025)

If valid event found, extract:
1. Name: Short descriptive name for the event
2. Date: The date/time or recurring schedule in clear format
3. Address: Full physical address where event occurs
4. Summary: 1-2 sentence description of what's offered

Output format:
If valid event exists, respond with JSON only:
{{"valid": true, "name": "...", "date": "...", "address": "...", "summary": "..."}}

If NO valid event (no clear date, no address, just general info, etc.), respond with JSON only:
{{"valid": false, "reason": "brief explanation"}}

Content to analyze:
{content[:4000]}"""

        # Call Ollama
        ollama_host = os.environ.get("OLLAMA_HOST", "http://host.docker.internal:11434")
        ollama_url = f"{ollama_host}/api/generate"

        payload = {
            "model": "nemotron:70B",
            "prompt": extraction_prompt,
            "stream": False,
            "options": {
                "temperature": 0.3
            }
        }

        def _query_ollama():
            req = urlrequest.Request(
                ollama_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urlrequest.urlopen(req, timeout=90) as resp:
                body = resp.read().decode('utf-8')
                result = json.loads(body)
                return result.get("response", "").strip()

        print("Calling Ollama to extract event information...")
        response_text = await asyncio.to_thread(_query_ollama)
        print(f"Ollama response: {response_text[:200]}...")

        # Parse JSON response from Ollama
        # Clean up response - sometimes LLMs add markdown code blocks
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        try:
            event_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"Failed to parse Ollama JSON response: {e}")
            return {
                "event": None,
                "reasoning": "Failed to parse event extraction response",
                "raw_response": response_text[:500]
            }

        # Check if valid event was found
        if not event_data.get("valid", False):
            return {
                "event": None,
                "reasoning": event_data.get("reason", "No valid event found")
            }

        # Extract event details
        event_name = event_data.get("name", "")
        event_date = event_data.get("date", "")
        event_address = event_data.get("address", "")
        event_summary = event_data.get("summary", "")

        if not event_address:
            return {
                "event": None,
                "reasoning": "Event found but no address provided"
            }

        # Geocode the address using Nominatim
        def _geocode_address(address: str) -> dict:
            """Query Nominatim to get coordinates for an address."""
            nominatim_url = f"http://nominatim:8080/search?format=json&q={urlparse.quote(address)}&limit=1"
            try:
                req = urlrequest.Request(nominatim_url, method="GET")
                with urlrequest.urlopen(req, timeout=15) as resp:
                    body = resp.read().decode("utf-8")
                    if not body:
                        return None
                    results = json.loads(body)
                    if results and len(results) > 0:
                        result = results[0]
                        return {
                            "latitude": float(result["lat"]),
                            "longitude": float(result["lon"]),
                            "display_name": result.get("display_name", address)
                        }
                    return None
            except Exception as e:
                print(f"Geocoding error: {e}")
                return None

        print(f"Geocoding address: {event_address}")
        geocode_result = await asyncio.to_thread(_geocode_address, event_address)

        if not geocode_result:
            return {
                "event": None,
                "reasoning": f"Could not geocode address: {event_address}"
            }

        # Build final event object
        event_object = {
            "Name": event_name,
            "Date": event_date,
            "summary": event_summary,
            "address": geocode_result["display_name"],
            "latitude": geocode_result["latitude"],
            "longitude": geocode_result["longitude"]
        }

        elapsed = time.time() - start_time
        print(f"Event extracted successfully in {elapsed:.2f}s")

        return {
            "event": event_object,
            "reasoning": "Valid event found and geocoded successfully"
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "type": type(e).__name__}


@app.get("/find_event")
async def find_event(latitude: float = 32.9859, longitude: float = -96.7503):
    """Find and extract the first valid event from search results.

    This endpoint:
    1. Calls /prompt_search to get relevant URLs
    2. Processes URLs one at a time, scraping and extracting event data
    3. Returns as soon as a valid event is found
    4. If no event found after 40 seconds, falls back to Local Good Pantry data

    Args:
        latitude: Latitude for location-based search. Default is Richardson, Texas.
        longitude: Longitude for location-based search. Default is Richardson, Texas.

    Returns:
        JSON object with:
        - events: List containing single event object with properties:
            - Name: Event name
            - Date: Event date/schedule
            - Summary: Event description
            - Address: Event address
            - latitude: GPS latitude
            - longitude: GPS longitude
            - source_url: URL where event was found
        - processing_time: Time taken to find the event
        - urls_processed: Number of URLs processed before finding event
    """
    import time

    # Fallback event data
    FALLBACK_EVENT = {
        "events": [{
            "Name": "Local Good Pantry",
            "Date": "Every Tuesday, Thursday, and Saturday",
            "Summary": "The Local Good Pantry, part of the Local Good Collective started by Chase Oaks Church, provides food assistance to the Richardson community. It partners with the City of Richardson and the North Texas Food Bank to help local residents access food and resources.",
            "Address": "741 S Sherman St, Richardson, TX 75081",
            "latitude": 32.9392,
            "longitude": -96.7294,
            "source_url": "https://localgoodpantry.org/"
        }]
    }

    try:
        start_time = time.time()
        TIMEOUT = 40  # seconds

        # Step 1: Get search URLs
        print(f"Starting find_event with lat={latitude}, lon={longitude}")
        search_results = await prompt_search(latitude, longitude)

        if "error" in search_results:
            print("Error in prompt_search, using fallback")
            return FALLBACK_EVENT

        urls_to_process = search_results.get("urls", [])

        if not urls_to_process:
            print("No URLs found, using fallback")
            return FALLBACK_EVENT

        print(f"Found {len(urls_to_process)} URLs to process")

        # Import scraping utilities
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        from agent_util.scrape_utils import get_html, html_to_text, extract_title

        # Step 2: Process URLs one at a time
        for i, url_info in enumerate(urls_to_process):
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed >= TIMEOUT:
                print(f"Timeout reached after {elapsed:.2f}s, using fallback")
                fallback_result = FALLBACK_EVENT.copy()
                fallback_result["processing_time"] = round(elapsed, 2)
                fallback_result["urls_processed"] = i
                return fallback_result

            url = url_info['url']
            print(f"Processing URL {i+1}/{len(urls_to_process)}: {url}")

            try:
                # Scrape the URL
                def _scrape():
                    html = get_html(url, timeout=15)
                    return html_to_text(html)

                content = await asyncio.to_thread(_scrape)
                print(f"Scraped {len(content)} characters from {url}")

                # Extract event from content
                extraction_result = await extract_event(content)

                # Check if valid event was found
                if extraction_result.get("event"):
                    event = extraction_result["event"]
                    event["source_url"] = url

                    elapsed = time.time() - start_time
                    print(f"Found valid event in {elapsed:.2f}s after processing {i+1} URLs")

                    return {
                        "events": [event],
                        "processing_time": round(elapsed, 2),
                        "urls_processed": i + 1
                    }
                else:
                    print(f"No valid event in {url}: {extraction_result.get('reasoning')}")

            except Exception as e:
                print(f"Error processing {url}: {type(e).__name__}: {e}")
                continue

        # If we've processed all URLs without finding an event
        elapsed = time.time() - start_time
        print(f"Processed all {len(urls_to_process)} URLs without finding event, using fallback")
        fallback_result = FALLBACK_EVENT.copy()
        fallback_result["processing_time"] = round(elapsed, 2)
        fallback_result["urls_processed"] = len(urls_to_process)
        return fallback_result

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Exception in find_event: {type(e).__name__}: {e}, using fallback")
        return FALLBACK_EVENT
