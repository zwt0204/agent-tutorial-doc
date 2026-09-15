"""Chapter 5: TODO - session planning."""
import json, sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from base import get_client, get_model, run_bash, MAX_TURNS


class TodoManager:
    def __init__(self):
        self.items = []

    def add(self, text: str):
        self.items.append({"text": text, "status": "pending"})

    def done(self, index: int):
        if 0 <= index < len(self.items):
            self.items[index]["status"] = "done"

    def render(self) -> str:
        lines = ["当前计划:"]
        for i, item in enumerate(self.items):
            mark = "x" if item["status"] == "done" else " "
            lines.append(f"- [{mark}] {item['text']}")
        return "\n".join(lines)


TODO = TodoManager()

TOOLS = [
    {"type": "function", "function": {"name": "bash", "description": "Run bash",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "todo_add", "description": "Add a task to the plan",
        "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "todo_done", "description": "Mark task as done by index (0-based)",
        "parameters": {"type": "object", "properties": {"index": {"type": "integer"}}, "required": ["index"]}}},
]



def agent_loop(query: str):
    client = get_client()
    MODEL = get_model()
    messages = [{"role": "user", "content": query}]
    for turn in range(MAX_TURNS):
        sys_prompt = "You are a helpful assistant.\n\n" + TODO.render()
        response = client.chat.completions.create(model=MODEL, system=sys_prompt,
            messages=messages, tools=TOOLS, max_tokens=8000)
        msg = response.choices[0].message
        messages.append(msg.model_dump())
        if not msg.tool_calls:
            print(msg.content)
            return
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            if tc.function.name == "bash":
                output = run_bash(args["command"])
            elif tc.function.name == "todo_add":
                TODO.add(args["text"])
                output = f"Added: {args['text']}"
            elif tc.function.name == "todo_done":
                TODO.done(args["index"])
                output = f"Done: task {args['index']}"
            else:
                output = f"Unknown: {tc.function.name}"
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": output})


if __name__ == "__main__":
    query = input("You: ") if len(sys.argv) < 2 else sys.argv[1]
    agent_loop(query)
