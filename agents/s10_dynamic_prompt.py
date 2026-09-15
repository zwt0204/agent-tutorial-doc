"""Chapter 10: Dynamic prompt - modular system prompt."""
import json, sys, os
from pathlib import Path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from base import get_client, get_model, run_bash, MAX_TURNS

WORKSPACE = Path.cwd()


class DynamicPrompt:
    def __init__(self):
        self.providers = []

    def register(self, name, fn, priority=0):
        self.providers.append({"name": name, "fn": fn, "priority": priority})
        self.providers.sort(key=lambda x: x["priority"])

    def build(self, ctx=None):
        parts = []
        for p in self.providers:
            try:
                part = p["fn"](ctx or {})
                if part:
                    parts.append(part)
            except Exception as e:
                parts.append(f"[{p['name']} failed: {e}]")
        return "\n\n".join(parts)


dp = DynamicPrompt()
dp.register("base", lambda c: "You are a helpful coding assistant.", 0)
dp.register("workspace", lambda c: f"Workspace files: {[f.name for f in WORKSPACE.glob('*.py')][:10]}", 10)
dp.register("model", lambda c: f"Using model: {os.getenv('OPENAI_MODEL', 'gpt-4o')}", 20)

TOOLS = [{"type": "function", "function": {"name": "bash", "description": "Run bash",
    "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}}]



def agent_loop(query):
    client = get_client()
    MODEL = get_model()
    messages = [{"role": "user", "content": query}]
    for _ in range(MAX_TURNS):
        resp = client.chat.completions.create(model=MODEL, system=dp.build(), messages=messages, tools=TOOLS, max_tokens=8000)
        msg = resp.choices[0].message
        messages.append(msg.model_dump())
        if not msg.tool_calls:
            print(msg.content)
            return
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            output = run_bash(args["command"])
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": output})

if __name__ == "__main__":
    query = input("You: ") if len(sys.argv) < 2 else sys.argv[1]
    agent_loop(query)
