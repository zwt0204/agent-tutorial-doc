"""Chapter 16: Protocols - structured collaboration."""
import json, sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from base import get_client, get_model, run_bash, MAX_TURNS


class ProtocolManager:
    def __init__(self):
        self.protocols = {}

    def define(self, name, steps):
        self.protocols[name] = {"steps": steps, "current": 0, "status": "pending"}

    def execute(self, name, agent):
        p = self.protocols[name]
        if p["current"] >= len(p["steps"]):
            return "Completed"
        step = p["steps"][p["current"]]
        if step["assignee"] != agent:
            return f"Assigned to {step['assignee']}"
        p["current"] += 1
        if p["current"] >= len(p["steps"]):
            p["status"] = "completed"
        return f"Step {p['current']}: {step['desc']} done"

    def status(self):
        return "\n".join(f"- {n}: {p['status']} ({p['current']}/{len(p['steps'])})"
                         for n, p in self.protocols.items()) or "No protocols"


# proto initialized lazily

TOOLS = [
    {"type": "function", "function": {"name": "bash", "description": "Run bash",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "proto_define", "description": "Define protocol steps",
        "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "steps": {"type": "array", "items": {"type": "object"}}}, "required": ["name", "steps"]}}},
    {"type": "function", "function": {"name": "proto_execute", "description": "Execute a protocol step",
        "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "agent": {"type": "string"}}, "required": ["name", "agent"]}}},
    {"type": "function", "function": {"name": "proto_status", "description": "List protocols",
        "parameters": {"type": "object", "properties": {}}}},
]



def agent_loop(query):
    proto = ProtocolManager()
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
            elif tc.function.name == "proto_define":
                proto.define(args["name"], args["steps"])
                output = f"Defined: {args['name']}"
            elif tc.function.name == "proto_execute":
                output = proto.execute(args["name"], args["agent"])
            elif tc.function.name == "proto_status":
                output = proto.status()
            else:
                output = "Unknown"
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(output)})

if __name__ == "__main__":
    query = input("You: ") if len(sys.argv) < 2 else sys.argv[1]
    agent_loop(query)
