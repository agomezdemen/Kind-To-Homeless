# agent.py
import json, requests
import scrape_utils as su
from tools import TOOLS

# Ollama server URL (mapped to port 7545)
OLLAMA_URL = "http://localhost:7545/api/chat"
MODEL = "nemotron:70B"  # Model from ollama-init.sh (slow - 5min+ per call)
SYSTEM_PROMPT = open('agent_system.txt').read()

def call_tool(name, arguments):
  fn = getattr(su, name, None)
  if fn is None:
    raise ValueError(f"Unknown tool: {name}")

  return fn(**(arguments or {}))

def chat(messages):
  # Convert OpenAI-style messages to Ollama format
  payload = {
    "model": MODEL,
    "messages": messages,
    "tools": TOOLS,
    "stream": False
  }
  print(f"[agent] calling {MODEL} via Ollama...", flush=True)
  r = requests.post(OLLAMA_URL, json=payload, timeout=300)
  r.raise_for_status()
  resp = r.json()

  # Convert Ollama response to OpenAI-compatible format
  return {
    "choices": [{
      "message": resp.get("message", {})
    }]
  }

def run(query):
  messages = [
    {"role":"system","content":SYSTEM_PROMPT},
    {"role":"user","content":query}
  ]

  for step in range(4):  # small loop to allow multi-step tool use
    print(f"[agent] step {step+1}/4", flush=True)
    resp = chat(messages)
    msg  = resp["choices"][0]["message"]
    tool_calls = msg.get("tool_calls", [])

    if not tool_calls:
      # model answered directly
      print(f"\n[agent] final answer:\n{msg.get('content','')}")
      return

    # dispatch each tool call, then feed results back
    print(f"[agent] executing {len(tool_calls)} tool call(s)")
    for tc in tool_calls:
      name = tc["function"]["name"]
      # Ollama returns dict, OpenAI returns JSON string
      raw_args = tc["function"]["arguments"]
      args = raw_args if isinstance(raw_args, dict) else json.loads(raw_args or "{}")
      print(f"  → {name}({', '.join(f'{k}={v!r}' if len(str(v)) < 50 else f'{k}=...' for k,v in args.items())})")
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

  print("\n[agent] stopped after max tool steps.")

if __name__ == "__main__":
  run("Given https://austinstreet.org/ find ‘shelter’ mentions and relevant links.")
