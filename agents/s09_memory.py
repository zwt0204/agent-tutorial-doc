"""Chapter 9: Memory - cross-session persistence."""
import json, sys, datetime
from pathlib import Path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from base import get_client, get_model, run_bash, MAX_TURNS

MEMORY_DIR = Path("./memory")


class MemoryManager:
    def __init__(self):
        MEMORY_DIR.mkdir(exist_ok=True)
        self.index_path = MEMORY_DIR / "index.json"
        self.index = json.loads(self.index_path.read_text()) if self.index_path.exists() else {"entries": []}

    def _save(self):
        self.index_path.write_text(json.dumps(self.index, indent=2, ensure_ascii=False))

    def remember(self, key, value):
        self.index["entries"].append({"key": key, "value": value, "ts": datetime.datetime.now().isoformat()})
        self._save()
        (MEMORY_DIR / f"{key}.md").write_text(value, encoding="utf-8")

    def recall(self, query):
        results = [e for e in self.index["entries"] if query.lower() in (e["key"] + e["value"]).lower()]
        if not results:
            return "No relevant memories."
        return "\n".join(f"- {e['key']}: {e['value'][:200]}" for e in results[:5])


# memory initialized lazily in agent_loop

TOOLS = [
    {"type": "function", "function": {"name": "bash", "description": "Run bash",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "remember", "description": "Store a memory",
        "parameters": {"type": "object", "properties": {"key": {"type": "string"}, "value": {"type": "string"}}, "required": ["key", "value"]}}},
    {"type": "function", "function": {"name": "recall", "description": "Recall memories by query",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
]



def agent_loop(query):
    memory = MemoryManager()
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
            elif tc.function.name == "remember":
                memory.remember(args["key"], args["value"])
                output = f"Remembered: {args['key']}"
            elif tc.function.name == "recall":
                output = memory.recall(args["query"])
            else:
                output = "Unknown"
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(output)})

if __name__ == "__main__":
    query = input("You: ") if len(sys.argv) < 2 else sys.argv[1]
    agent_loop(query)
