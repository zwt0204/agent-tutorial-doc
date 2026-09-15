"""Chapter 4: Hook system - lifecycle callbacks."""
import json, sys
from typing import Callable
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from base import get_client, get_model, run_bash, safe_path, MAX_TURNS

SYSTEM = "You are a helpful coding assistant."


class HookManager:
    def __init__(self):
        self.hooks = {"UserPromptSubmit": [], "PreToolUse": [], "PostToolUse": [], "Stop": []}

    def register(self, event: str, fn: Callable):
        self.hooks[event].append(fn)

    def fire(self, event: str, data: dict) -> dict | None:
        for fn in self.hooks[event]:
            result = fn(data)
            if result is False:
                return None
            if isinstance(result, dict):
                data.update(result)
        return data


hooks = HookManager()
hooks.register("UserPromptSubmit", lambda d: d)
hooks.register("PreToolUse", lambda d: (print(f"[PRE] {d['tool_name']}"), d)[1])
hooks.register("PostToolUse", lambda d: (print(f"[POST] {d['tool_name']} -> {str(d.get('result',''))[:80]}"), d)[1])
hooks.register("Stop", lambda d: (print("[STOP] Saving state..."), d)[1])

TOOLS = [{"type": "function", "function": {"name": "bash", "description": "Run bash",
    "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}}]



def agent_loop(query: str):
    client = get_client()
    MODEL = get_model()
    messages = [{"role": "user", "content": query}]
    while True:
        hook_data = hooks.fire("UserPromptSubmit", {"prompt": query, "messages": messages})
        if hook_data is None:
            return "Blocked by hook"
        response = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS, max_tokens=8000)
        msg = response.choices[0].message
        messages.append(msg.model_dump())
        if not msg.tool_calls:
            hooks.fire("Stop", {"messages": messages})
            print(msg.content)
            return
        results = []
        for tc in msg.tool_calls:
            hooks.fire("PreToolUse", {"tool_name": tc.function.name, "params": tc.function.arguments})
            args = json.loads(tc.function.arguments)
            output = run_bash(args["command"])
            hooks.fire("PostToolUse", {"tool_name": tc.function.name, "result": output})
            results.append({"role": "tool", "tool_call_id": tc.id, "content": output})
        messages.extend(results)


if __name__ == "__main__":
    query = input("You: ") if len(sys.argv) < 2 else sys.argv[1]
    agent_loop(query)
