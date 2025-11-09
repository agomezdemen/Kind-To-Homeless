# this file exposes the functionalities of the scrape util to the ai
TOOLS = [
  { "type": "function", "function": {
      "name": "get_html",
      "description": "Fetch raw HTML for a URL (respect robots.txt/timeout in code).",
      "parameters": {"type":"object","properties":{
        "url":{"type":"string"}
      },"required":["url"]}
  }},
  { "type": "function", "function": {
      "name": "html_to_text",
      "description": "Convert HTML to readable plain text.",
      "parameters": {"type":"object","properties":{
        "html":{"type":"string"}
      },"required":["html"]}
  }},
  { "type": "function", "function": {
      "name": "extract_links",
      "description": "Extract absolute links from HTML. If base provided, resolve relatives.",
      "parameters": {"type":"object","properties":{
        "html":{"type":"string"},
        "base":{"type":"string","nullable":True},
        "allow_external":{"type":"boolean","default":True}
      },"required":["html"]}
  }},
  { "type": "function", "function": {
      "name": "filter_links",
      "description": "Filter links by include/exclude substrings.",
      "parameters": {"type":"object","properties":{
        "links":{"type":"array","items":{"type":"string"}},
        "include_substrings":{"type":"array","items":{"type":"string"},"default":[]},
        "exclude_substrings":{"type":"array","items":{"type":"string"},"default":[]}
      },"required":["links"]}
  }},
  { "type": "function", "function": {
      "name": "find_terms_in_text",
      "description": "Find case-insensitive terms in text; returns snippets around matches.",
      "parameters": {"type":"object","properties":{
        "text":{"type":"string"},
        "terms":{"type":"array","items":{"type":"string"}}
      },"required":["text","terms"]}
  }},
  { "type": "function", "function": {
      "name": "extract_contacts",
      "description": "Pull phones, emails, and hours from text.",
      "parameters": {"type":"object","properties":{
        "text":{"type":"string"}
      },"required":["text"]}
  }},
  { "type": "function", "function": {
      "name": "crawl_once",
      "description": "One-shot crawl: fetch URL, return title, links, phones, emails, hours, and term hits.",
      "parameters": {"type":"object","properties":{
        "url":{"type":"string"},
        "terms":{"type":"array","items":{"type":"string"},"default":[]},
        "allow_external_links":{"type":"boolean","default":False}
      },"required":["url"]}
  }},
  # Optional WordPress helper (many shelters use WP):
  { "type": "function", "function": {
      "name": "wp_search_pages",
      "description": "Search a WordPress site for pages with a query string.",
      "parameters": {"type":"object","properties":{
        "base_url":{"type":"string"},
        "query":{"type":"string"}
      },"required":["base_url","query"]}
  }},
]
