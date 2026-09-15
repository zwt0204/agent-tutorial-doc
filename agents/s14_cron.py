"""Chapter 14: Cron scheduler - timed execution."""
import json, sys, time, threading
from datetime import datetime
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from base import get_client, get_model, run_bash, MAX_TURNS

TOOLS = [
    {"type": "function", "function": {"name": "bash", "description": "Run bash",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "cron_add", "description": "Add periodic job (interval in seconds)",
        "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "interval": {"type": "integer"}, "command": {"type": "string"}}, "required": ["name", "interval", "command"]}}},
    {"type": "function", "function": {"name": "cron_list", "description": "List scheduled jobs",
        "parameters": {"type": "object", "properties": {}}}},
]

jobs = []
stop_event = threading.Event()


def cron_worker(name, interval, command):
    while not stop_event.is_set():
        time.sleep(interval)
        print(f"[{datetime.now()}] Cron: {name}")
        __import__("subprocess").run(command, shell=True, capture_output=True, timeout=60)



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
            elif tc.function.name == "cron_add":
                jobs.append(args)
                t = threading.Thread(target=cron_worker, args=(args["name"], args["interval"], args["command"]), daemon=True)
                t.start()
                output = f"Added cron: {args['name']}"
            elif tc.function.name == "cron_list":
                output = "\n".join(f"- {j['name']}: every {j['interval']}s -> {j['command']}" for j in jobs) or "No jobs"
            else:
                output = "Unknown"
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(output)})

if __name__ == "__main__":
    try:
        query = input("You: ") if len(sys.argv) < 2 else sys.argv[1]
        agent_loop(query)
    finally:
        stop_event.set()
