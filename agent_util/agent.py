# agent.py
import json, requests
import scrape_utils as su
from tools import TOOLS

VLLM_URL = "http://localhost:7545/v1/chat/completions"
MODEL    = "nvidia/Llama-3_3-Nemotron-Super-49B-v1_5"
SYSTEM_PROMPT = open('agent_system.txt').read()

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
    "tool_choice": "auto",     # let the model decide
    "max_tokens": 512
  }
  r = requests.post(VLLM_URL, json=payload, timeout=120)
  r.raise_for_status()
  return r.json()

def run(query):
  messages = [
    {"role":"system","content":SYSTEM_PROMPT},
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
