"""Chapter 3: Permission system - 4-state policy + audit."""
import json, sys, datetime
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from base import get_client, get_model, run_bash, safe_path, MAX_TURNS

SYSTEM = "You are a helpful coding assistant with tools."


class PermissionPolicy:
    def __init__(self):
        self.rules = {}
        self.granted = set()

    def check(self, tool_name: str) -> str:
        perm = self.rules.get(tool_name, "allow")
        if perm == "ask_once" and tool_name in self.granted:
            return "allow"
        return perm

    def grant_once(self, tool_name: str):
        self.granted.add(tool_name)


policy = PermissionPolicy()
policy.rules = {"bash": "ask", "write_file": "ask_once", "edit_file": "ask_once", "read_file": "allow"}

AUDIT_LOG = []


def audit(tool_name, params, result, perm):
    AUDIT_LOG.append({"ts": datetime.datetime.now().isoformat(), "tool": tool_name,
                       "perm": perm, "result_preview": str(result)[:100]})


def execute_tool(name, args):
    perm = policy.check(name)
    if perm == "deny":
        return "Permission denied"
    if perm in ("ask", "ask_once"):
        if perm == "ask_once" and name in policy.granted:
            pass
        else:
            ans = input(f"  Allow {name}({args})? [y/N]: ").strip().lower()
            if ans != "y":
                return "User denied"
            if perm == "ask_once":
                policy.granted.add(name)

    if name == "bash":
        return run_bash(args["command"])
    elif name == "read_file":
        return safe_path(args["path"]).read_text(encoding="utf-8")[:50000]
    elif name == "write_file":
        p = safe_path(args["path"])
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(args["content"], encoding="utf-8")
        return f"Written to {args['path']}"
    return f"Unknown: {name}"


TOOLS = [
    {"type": "function", "function": {"name": "bash", "description": "Run bash",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "read_file", "description": "Read file",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Write file",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
]



def agent_loop(query: str):
    client = get_client()
    MODEL = get_model()
    messages = [{"role": "user", "content": query}]
    for turn in range(MAX_TURNS):
        response = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS, max_tokens=8000)
        msg = response.choices[0].message
        messages.append(msg.model_dump())
        if not msg.tool_calls:
            print(msg.content)
            return
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            output = execute_tool(tc.function.name, args)
            audit(tc.function.name, args, output, policy.check(tc.function.name))
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(output)})


if __name__ == "__main__":
    query = input("You: ") if len(sys.argv) < 2 else sys.argv[1]
    agent_loop(query)
