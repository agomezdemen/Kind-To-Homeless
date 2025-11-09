"""
scrape_utils.py — tiny, composable scraping helpers for agentic use

Dependency: requests (pip install requests)
No BeautifulSoup required. Works with plain regex + stdlib.
"""

from __future__ import annotations

import html as _html
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ------------------------------
# Networking / sessions
# ------------------------------

UA = "Mozilla/5.0 (X11; Linux x86_64) agentic-bot/0.1 (+nocrawl; contact=none)"


def make_session(
    retries: int = 3,
    backoff: float = 0.5,
    status_forcelist: Sequence[int] = (429, 500, 502, 503, 504),
    user_agent: str = UA,
    proxies: Optional[Dict[str, str]] = None,
) -> requests.Session:
    """
    Create a requests Session with retry + UA header.
    """
    s = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=status_forcelist,
        allowed_methods=frozenset(["HEAD", "GET", "OPTIONS", "POST"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    s.headers.update({"User-Agent": user_agent})
    if proxies:
        s.proxies.update(proxies)
    return s


def _ensure_session(session: Optional[requests.Session] = None) -> requests.Session:
    return session or make_session()


# ------------------------------
# Fetch
# ------------------------------

def get_html(
    url: str,
    timeout: int = 15,
    session: Optional[requests.Session] = None,
    allow_redirects: bool = True,
) -> str:
    """
    Fetch decoded HTML as text. Raises for HTTP errors.
    """
    s = _ensure_session(session)
    r = s.get(url, timeout=timeout, allow_redirects=allow_redirects)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or "utf-8"
    return r.text


def get_bytes(
    url: str,
    timeout: int = 15,
    session: Optional[requests.Session] = None,
    allow_redirects: bool = True,
) -> bytes:
    """
    Fetch raw bytes. Raises for HTTP errors.
    """
    s = _ensure_session(session)
    r = s.get(url, timeout=timeout, allow_redirects=allow_redirects)
    r.raise_for_status()
    return r.content


def get_status(
    url: str,
    timeout: int = 10,
    session: Optional[requests.Session] = None,
) -> int:
    """
    HTTP status code after following redirects.
    """
    s = _ensure_session(session)
    r = s.head(url, allow_redirects=True, timeout=timeout)
    return r.status_code


def get_headers(
    url: str,
    timeout: int = 10,
    session: Optional[requests.Session] = None,
) -> Dict[str, str]:
    """
    Response headers after following redirects.
    """
    s = _ensure_session(session)
    r = s.head(url, allow_redirects=True, timeout=timeout)
    return dict(r.headers)


def get_json(
    url: str,
    timeout: int = 15,
    session: Optional[requests.Session] = None,
) -> Any:
    """
    Convenience: GET JSON endpoint and parse.
    """
    s = _ensure_session(session)
    r = s.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()


# ------------------------------
# URL utilities
# ------------------------------

def normalize_url(base: str, link: str) -> Optional[str]:
    """
    Turn a relative/fragment mailto/tel/etc. into an absolute HTTP(S) URL or None.
    """
    if not link:
        return None
    if link.startswith(("javascript:", "mailto:", "tel:")):
        return None
    # Drop pure fragment
    if link.startswith("#"):
        return None
    return urljoin(base, link)


def canonicalize_url(url: str, drop_fragment: bool = True) -> str:
    """
    Normalize a URL minimally: option to drop fragment, leave query intact.
    """
    p = urlparse(url)
    fragment = "" if drop_fragment else p.fragment
    return urlunparse((p.scheme, p.netloc, p.path or "/", p.params, p.query, fragment))


def same_domain(a: str, b: str) -> bool:
    return urlparse(a).netloc == urlparse(b).netloc


def is_http_url(url: str) -> bool:
    return urlparse(url).scheme in ("http", "https")


def dedupe_preserve_order(items: Iterable[str]) -> List[str]:
    seen, out = set(), []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


# ------------------------------
# Parse (regex-only, no BS4)
# ------------------------------

_RE_SCRIPT_STYLE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.I | re.S)
_RE_TAG = re.compile(r"<[^>]+>")
_RE_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
_RE_HREF = re.compile(r'href=["\']([^"\']+)["\']', re.I)


def extract_title(html: str) -> str:
    m = _RE_TITLE.search(html)
    return (m.group(1).strip() if m else "")


def html_to_text(html: str) -> str:
    """
    Remove <script>/<style>, strip tags, unescape entities, collapse whitespace.
    """
    clean = _RE_SCRIPT_STYLE.sub(" ", html)
    clean = _RE_TAG.sub(" ", clean)
    clean = _html.unescape(clean)
    return re.sub(r"\s+", " ", clean).strip()


def extract_links(html: str, base: Optional[str] = None, allow_external: bool = True) -> List[str]:
    """
    Extract absolute <a href> links. If base is None, only absolute http(s) links are returned.
    """
    links = []
    for h in _RE_HREF.findall(html):
        if base:
            u = normalize_url(base, h)
        else:
            # If no base is provided, keep only absolute http(s) links.
            u = h if is_http_url(h) else None
        if not u:
            continue
        if base and not allow_external and not same_domain(base, u):
            continue
        links.append(canonicalize_url(u))
    return dedupe_preserve_order(links)



def filter_links(
    links: Sequence[str],
    include_substrings: Optional[Sequence[str]] = None,
    exclude_substrings: Optional[Sequence[str]] = None,
    limit: Optional[int] = None,
) -> List[str]:
    """
    Simple substring filter; order preserved.
    """
    out = []
    for u in links:
        if include_substrings and not any(s.lower() in u.lower() for s in include_substrings):
            continue
        if exclude_substrings and any(s.lower() in u.lower() for s in exclude_substrings):
            continue
        out.append(u)
        if limit and len(out) >= limit:
            break
    return out


# ------------------------------
# Search / extraction
# ------------------------------

def find_terms_in_text(text: str, terms: Sequence[str], context: int = 80) -> List[Dict[str, str]]:
    """
    Return [{term, snippet}] for first occurrence of each term.
    """
    low = text.lower()
    hits: List[Dict[str, str]] = []
    for t in terms:
        q = t.lower()
        i = low.find(q)
        if i != -1:
            s = max(0, i - context)
            e = min(len(text), i + len(t) + context)
            hits.append({"term": t, "snippet": text[s:e].strip()})
    return hits


def find_terms_in_url(
    url: str,
    terms: Sequence[str],
    context: int = 80,
    timeout: int = 15,
    session: Optional[requests.Session] = None,
) -> Dict[str, Any]:
    html = get_html(url, timeout=timeout, session=session)
    text = html_to_text(html)
    return {
        "url": url,
        "title": extract_title(html),
        "hits": find_terms_in_text(text, terms, context),
    }


# Contacts / hours (naive regex; keep tiny)

_RE_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_RE_PHONE = re.compile(r"(?:\+1\s*)?(?:\(\d{3}\)|\d{3})[.\-\s]?\d{3}[.\-\s]?\d{4}")
_RE_HOURS = re.compile(
    r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[^\n]{0,30}"
    r"(\d{1,2}(:\d{2})?\s?(am|pm|AM|PM)?\s?[-–]\s?\d{1,2}(:\d{2})?\s?(am|pm|AM|PM)?)"
)


def extract_emails(text: str) -> List[str]:
    return sorted(set(_RE_EMAIL.findall(text)))


def extract_phones(text: str) -> List[str]:
    return sorted(set(p.strip() for p in _RE_PHONE.findall(text)))


def extract_hours(text: str) -> List[str]:
    return sorted(set(m.group(0).strip() for m in _RE_HOURS.finditer(text)))

# ------------------------------
# Higher-level mini-composites (still tiny)
# ------------------------------

def crawl_once(
    url: str,
    terms: Optional[Sequence[str]] = None,
    allow_external_links: bool = True,
    timeout: int = 15,
    session: Optional[requests.Session] = None,
    include_contact_and_hours: bool = True,
    text_max_chars: int = 50000,
) -> Dict[str, Any]:
    """
    One-shot: fetch → parse → links → (optional) term hits + contacts/hours.
    Keeps everything small and returns a compact dict.
    """

    html = get_html(url, timeout=timeout, session=session)
    title = extract_title(html)
    text = html_to_text(html)
    if len(text) > text_max_chars:
        text = text[:text_max_chars]

    out: Dict[str, Any] = {
        "url": url,
        "title": title,
        "links": extract_links(html, base=url, allow_external=allow_external_links),
    }

    if terms:
        out["hits"] = find_terms_in_text(text, terms)

    if include_contact_and_hours:
        out["emails"] = extract_emails(text)
        out["phones"] = extract_phones(text)
        out["hours"] = extract_hours(text)

    return out


# ------------------------------
# Example (manual test)
# ------------------------------

if __name__ == "__main__":
    s = make_session()
    test_url = "https://example.org/"
    data = crawl_once(test_url, terms=["example", "contact"], session=s)
    from pprint import pprint
    pprint(data)

def wp_search_pages(
    base_url: str,
    query: str,
    per_page: int = 10,
    timeout: int = 15,
    session: Optional[requests.Session] = None,
) -> Dict[str, Any]:
    """
    Query a WordPress site's REST API for pages matching `query`.
    Returns {ok, results:[{title,url}], status?}.
    """
    s = _ensure_session(session)
    api = urljoin(base_url, "/wp-json/wp/v2/search")
    params = {"search": query, "subtype": "page", "per_page": per_page}
    try:
        r = s.get(api, params=params, timeout=timeout)
    except requests.RequestException as e:
        return {"ok": False, "error": str(e), "results": []}
    if r.status_code >= 400:
        return {"ok": False, "status": r.status_code, "results": []}
    out = []
    try:
        for item in r.json():
            url = item.get("url")
            if url:
                out.append({
                    "title": item.get("title", ""),
                    "url": canonicalize_url(url),
                })
    except ValueError:
        return {"ok": False, "status": r.status_code, "results": []}
    return {"ok": True, "results": out}
