#!/usr/bin/env python3
"""One turn of chat with a local Ollama model, persisting the conversation.

Lets a human/agent orchestrator (e.g. Claude in the terminal) play the attacker
turn by turn: pass --say, the target model replies, history is saved to --history.

  python3 scripts/localchat.py --model qwen2.5-coder:latest --history /tmp/c.json --say "hi"
"""
import argparse, json, urllib.request
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--model", required=True)
p.add_argument("--history", required=True)
p.add_argument("--say", required=True)
p.add_argument("--url", default="http://localhost:11434")
a = p.parse_args()

hist = json.loads(Path(a.history).read_text()) if Path(a.history).exists() else []
hist.append({"role": "user", "content": a.say})
req = urllib.request.Request(
    f"{a.url}/api/chat",
    data=json.dumps({"model": a.model, "messages": hist, "stream": False}).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req, timeout=180) as r:
    reply = json.loads(r.read())["message"]["content"]
hist.append({"role": "assistant", "content": reply})
Path(a.history).write_text(json.dumps(hist, ensure_ascii=False, indent=1))
print(reply)
