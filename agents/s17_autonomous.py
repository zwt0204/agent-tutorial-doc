"""Chapter 17: Autonomous agents - idle polling + auto-claim."""
import json, sys, time, threading
from pathlib import Path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from base import get_client, get_model, run_bash, MAX_TURNS

TASKS_DIR = Path("./tasks")
INBOX_DIR = Path("./inbox")


def read_inbox(name):
    p = INBOX_DIR / f"{name}.jsonl"
    if not p.exists():
        return []
    msgs = [json.loads(l) for l in p.read_text().strip().split("\n") if l]
    p.write_text("")
    return msgs


def scan_unclaimed():
    if not TASKS_DIR.exists():
        return []
    unclaimed = []
    for f in sorted(TASKS_DIR.glob("task_*.json")):
        t = json.loads(f.read_text())
        if t["status"] == "pending" and not t.get("owner") and not t.get("blockedBy"):
            unclaimed.append(t)
    return unclaimed


def claim_task(tid, owner):
    p = TASKS_DIR / f"task_{tid}.json"
    t = json.loads(p.read_text())
    t["owner"] = owner
    t["status"] = "in_progress"
    p.write_text(json.dumps(t, indent=2, ensure_ascii=False))


class AutonomousAgent:
    def __init__(self, name, role):
        self.name, self.role = name, role

    def idle_poll(self, messages, max_wait=30, interval=3):
        for _ in range(max_wait // interval):
            time.sleep(interval)
            inbox = read_inbox(self.name)
            if inbox:
                messages.append({"role": "user", "content": f"<inbox>{json.dumps(inbox)}</inbox>"})
                return True
            unclaimed = scan_unclaimed()
            if unclaimed:
                claim_task(unclaimed[0]["id"], self.name)
                messages.append({"role": "user", "content": f"<auto-claimed>Task #{unclaimed[0]['id']}: {unclaimed[0]['subject']}</auto-claimed>"})
                return True
        return False

    def run(self, prompt):
        client = get_client()
        MODEL = get_model()
        messages = [{"role": "user", "content": prompt}]
        tools = [{"type": "function", "function": {"name": "bash", "description": "Run bash",
            "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}}]
        for _ in range(20):
            sys_prompt = f"You are '{self.name}', role: {self.role}. Work independently."
            resp = client.chat.completions.create(model=MODEL, system=sys_prompt, messages=messages, tools=tools, max_tokens=4000)
            msg = resp.choices[0].message
            messages.append(msg.model_dump())
            if not msg.tool_calls:
                return msg.content
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments)
                output = run_bash(args["command"])
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": output})
            if not self.idle_poll(messages):
                return f"{self.name}: idle timeout"
        return f"{self.name}: max turns"


TOOLS = [
    {"type": "function", "function": {"name": "bash", "description": "Run bash",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "spawn", "description": "Spawn autonomous teammate",
        "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "role": {"type": "string"}, "prompt": {"type": "string"}}, "required": ["name", "role", "prompt"]}}},
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
            elif tc.function.name == "spawn":
                agent = AutonomousAgent(args["name"], args["role"])
                t = threading.Thread(target=lambda: agent.run(args["prompt"]), daemon=True)
                t.start()
                output = f"Spawned {args['name']}"
            else:
                output = "Unknown"
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(output)})

if __name__ == "__main__":
    query = input("You: ") if len(sys.argv) < 2 else sys.argv[1]
    agent_loop(query)
