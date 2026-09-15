"""Chapter 15: Inbox - async messaging."""
import json, sys, datetime
from pathlib import Path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from base import get_client, get_model, run_bash, MAX_TURNS

INBOX_DIR = Path("./inbox")


class MessageBus:
    def __init__(self):
        INBOX_DIR.mkdir(exist_ok=True)

    def send(self, sender, to, content, msg_type="message"):
        msg = {"type": msg_type, "from": sender, "content": content, "ts": datetime.datetime.now().isoformat()}
        with open(INBOX_DIR / f"{to}.jsonl", "a") as f:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")

    def read_inbox(self, name):
        p = INBOX_DIR / f"{name}.jsonl"
        if not p.exists():
            return []
        msgs = [json.loads(l) for l in p.read_text().strip().split("\n") if l]
        p.write_text("")
        return msgs

    def broadcast(self, sender, content):
        for f in INBOX_DIR.glob("*.jsonl"):
            if f.stem != sender:
                self.send(sender, f.stem, content, "broadcast")


def agent_loop(query):
    bus = MessageBus()

TOOLS = [
    {"type": "function", "function": {"name": "bash", "description": "Run bash",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "send_message", "description": "Send message to teammate",
        "parameters": {"type": "object", "properties": {"to": {"type": "string"}, "content": {"type": "string"}}, "required": ["to", "content"]}}},
    {"type": "function", "function": {"name": "read_inbox", "description": "Read inbox (drains it)",
        "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "broadcast", "description": "Broadcast to all",
        "parameters": {"type": "object", "properties": {"content": {"type": "string"}}, "required": ["content"]}}},
]



def agent_loop(query):
    client = get_client()
    MODEL = get_model()
    messages = [{"role": "user", "content": query}]
    for _ in range(MAX_TURNS):
        resp = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS, max_tokens=8000)
        msg = resp.choices[0].message
        messages.append(msg.model_dump())
        if not msg.tool_calls:
            print(msg.content)
            return
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            if tc.function.name == "bash":
                output = run_bash(args["command"])
            elif tc.function.name == "send_message":
                bus.send("lead", args["to"], args["content"])
                output = f"Sent to {args['to']}"
            elif tc.function.name == "read_inbox":
                msgs = bus.read_inbox(args["name"])
                output = json.dumps(msgs, indent=2, ensure_ascii=False)
            elif tc.function.name == "broadcast":
                bus.broadcast("lead", args["content"])
                output = "Broadcast sent"
            else:
                output = "Unknown"
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(output)})

if __name__ == "__main__":
    query = input("You: ") if len(sys.argv) < 2 else sys.argv[1]
    agent_loop(query)
