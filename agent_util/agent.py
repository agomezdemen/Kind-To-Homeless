# agent.py
import json, requests
from scrape_utils import get_html, extract_links, find_terms, extract_contacts  # whatever you wrote

VLLM_URL = "http://localhost:8000/v1/chat/completions"
MODEL    = "nvidia/Llama-3_3-Nemotron-Super-49B-v1_5"

TOOLS = [
  {
    "type": "function",
    "function": {
      "name": "get_html",
      "description": "Fetch raw HTML for a URL.",
      "parameters": {
        "type": "object",
        "properties": { "url": {"type":"string"} },
        "required": ["url"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "find_terms",
      "description": "Search HTML for case-insensitive terms and return snippets.",
      "parameters": {
        "type": "object",
        "properties": {
          "html": {"type":"string"},
          "terms": {"type":"array","items":{"type":"string"}}
        },
        "required": ["html","terms"]
      }
    }
  },
  # add other tiny utilities here (extract_links, extract_contacts, etc)
]

def call_tool(name, arguments):
  if name == "get_html":
    return get_html(**arguments)                 # e.g. {"url": "..."}
  if name == "find_terms":
    return find_terms(**arguments)               # e.g. {"html": "...", "terms": ["shelter","meals"]}
  # map other tool names -> your functions here
  raise ValueError(f"Unknown tool: {name}")

def chat(messages):
  payload = {
    "model": MODEL,
    "messages": messages,
    "tools": TOOLS,
    "tool_choice": "auto",     # let the model decide
    "max_tokens": 512
  }
  r = requests.post(VLLM_URL, json=payload, timeout=120)
  r.raise_for_status()
  return r.json()

def run(query):
  messages = [
    {"role":"system","content":"You are a helpful agent. When needed, call tools. Keep outputs concise."},
    {"role":"user","content":query}
  ]

  for _ in range(4):  # small loop to allow multi-step tool use
    resp = chat(messages)
    msg  = resp["choices"][0]["message"]
    tool_calls = msg.get("tool_calls", [])

    if not tool_calls:
      # model answered directly
      print(msg.get("content",""))
      return

    # dispatch each tool call, then feed results back
    for tc in tool_calls:
      name = tc["function"]["name"]
      args = json.loads(tc["function"]["arguments"] or "{}")
      result = call_tool(name, args)

      messages.append({
        "role": "assistant",
        "tool_calls": [tc]              # echo the tool call we executed
      })
      messages.append({
        "role": "tool",
        "tool_call_id": tc["id"],
        "name": name,
        "content": json.dumps(result)   # text—model will read this and continue
      })

  print("Stopped after max tool steps.")

if __name__ == "__main__":
  run("Given https://austinstreet.org/ find ‘shelter’ mentions and relevant links.")
