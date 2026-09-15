"""Chapter 2: Tool Use - dispatch map + safe paths."""
import json, sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from base import get_client, get_model, run_bash, safe_path, MAX_TURNS

SYSTEM = "You are a helpful coding assistant with tools."
WORKDIR = __import__("pathlib").Path.cwd()

TOOLS_SCHEMA = [
    {"type": "function", "function": {"name": "bash", "description": "Run bash command",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "read_file", "description": "Read a file",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Write a file",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "edit_file", "description": "Edit: replace old_text with new_text",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}}, "required": ["path", "old_text", "new_text"]}}},
]


def run_read(path: str, limit: int = None) -> str:
    text = safe_path(path).read_text(encoding="utf-8")
    lines = text.splitlines()
    if limit:
        lines = lines[:limit]
    return "\n".join(lines)[:50000]


def run_write(path: str, content: str) -> str:
    p = safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Written {len(content)} bytes to {path}"


def run_edit(path: str, old_text: str, new_text: str) -> str:
    p = safe_path(path)
    text = p.read_text(encoding="utf-8")
    if old_text not in text:
        return f"Error: old_text not found in {path}"
    p.write_text(text.replace(old_text, new_text, 1), encoding="utf-8")
    return f"Edited {path}"


HANDLERS = {
    "bash": lambda **kw: run_bash(kw["command"]),
    "read_file": lambda **kw: run_read(kw["path"], kw.get("limit")),
    "write_file": lambda **kw: run_write(kw["path"], kw["content"]),
    "edit_file": lambda **kw: run_edit(kw["path"], kw["old_text"], kw["new_text"]),
}



def agent_loop(query: str):
    client = get_client()
    MODEL = get_model()
    messages = [{"role": "user", "content": query}]
    for turn in range(MAX_TURNS):
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS_SCHEMA, max_tokens=8000)
        msg = response.choices[0].message
        messages.append(msg.model_dump())
        if not msg.tool_calls:
            print(msg.content)
            return
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            handler = HANDLERS.get(tc.function.name)
            output = handler(**args) if handler else f"Unknown: {tc.function.name}"
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(output)})


if __name__ == "__main__":
    query = input("You: ") if len(sys.argv) < 2 else sys.argv[1]
    agent_loop(query)
