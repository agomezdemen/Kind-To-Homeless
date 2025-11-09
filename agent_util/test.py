#!/usr/bin/env python3
"""
test.py — quick smoke tests for:
- scrape_utils primitives
- crawl_once composite
- optional wp_search_pages
- optional agent loop with vLLM (only if server is reachable)

Usage:
  python3 test.py
  python3 test.py --url https://austinstreet.org/ --terms shelter,meal,food
"""

from __future__ import annotations
import argparse, json, sys, socket, time

# local imports
import scrape_utils as su

def reachable(host: str, port: int, timeout=0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False

def pp(title: str, obj):
    print(f"\n=== {title} ===")
    try:
        print(json.dumps(obj, indent=2, ensure_ascii=False)[:100000])
    except TypeError:
        print(obj)

def test_scrape(url: str, terms: list[str]):
    print(f"\n[1/4] basic scrape on {url}")
    html = su.get_html(url)
    text = su.html_to_text(html)
    title = su.extract_title(html)
    links = su.extract_links(html, base=url, allow_external=True)
    filtered = su.filter_links(
        links,
        include_substrings=["help", "shelter", "service", "meal", "food", "contact", "intake"],
        exclude_substrings=["facebook", "instagram", "twitter", "linkedin", "youtube"],
        limit=20,
    )
    hits = su.find_terms_in_text(text, terms, context=80)
    emails = su.extract_emails(text)
    phones = su.extract_phones(text)
    hours  = su.extract_hours(text)

    # If you have an aggregate extract_contacts helper, call it; otherwise emulate it here
    contacts = {"emails": emails, "phones": phones, "hours": hours}
    if hasattr(su, "extract_contacts"):
        try:
            contacts = su.extract_contacts(text)  # type: ignore[attr-defined]
        except Exception:
            pass

    pp("title", title)
    pp("hits", hits)
    pp("filtered_links", filtered)
    pp("contacts", contacts)

def test_crawl_once(url: str, terms: list[str]):
    print(f"\n[2/4] crawl_once on {url}")
    out = su.crawl_once(url, terms=terms, allow_external_links=False)
    pp("crawl_once", out)

def test_wp_search(url: str):
    print(f"\n[3/4] wp_search_pages on {url}")
    if not hasattr(su, "wp_search_pages"):
        print("wp_search_pages not implemented — skipping")
        return
    try:
        res = su.wp_search_pages(url, query="shelter")
        pp("wp_search_pages('shelter')", res)
    except Exception as e:
        print(f"wp_search_pages error: {e}")

def test_agent_roundtrip(url: str, terms: list[str]):
    print("\n[4/4] agent + Ollama round-trip")
    try:
        import agent
    except Exception as e:
        print(f"could not import agent.py — skipping agent test ({e})")
        return

    # check server reachability
    host, port = "127.0.0.1", 7545
    if not reachable(host, port):
        print(f"Ollama server not reachable at {host}:{port} — start it to run this step")
        return

    # verify the API endpoint is working (Ollama uses /api/tags to list models)
    try:
        import requests
        test_resp = requests.get(f"http://{host}:{port}/api/tags", timeout=5)
        if test_resp.status_code != 200:
            print(f"Ollama server not responding properly — skipping agent test")
            return
    except Exception as e:
        print(f"Ollama server API not ready at {host}:{port} — skipping agent test ({e})")
        return

    # nudge the model to use tools
    q = (
        f"Use tools to fetch {url}. Extract shelter or meal info, phones, hours, "
        "and return the most relevant links."
    )
    print(f"sending: {q}")
    try:
        agent.run(q)
    except Exception as e:
        print(f"agent.run failed: {e}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="https://austinstreet.org/")
    ap.add_argument("--terms", default="shelter,meal,food,intake,hours")
    args = ap.parse_args()

    terms = [t.strip() for t in args.terms.split(",") if t.strip()]

    test_scrape(args.url, terms)
    test_crawl_once(args.url, terms)
    test_wp_search(args.url)
    test_agent_roundtrip(args.url, terms)

if __name__ == "__main__":
    main()
