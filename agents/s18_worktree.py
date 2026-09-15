"""Chapter 18: Worktree isolation - parallel execution."""
import json, sys, subprocess, datetime
from pathlib import Path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from base import get_client, get_model, MAX_TURNS

WT_DIR = Path("./worktasks")


class WorktreeManager:
    def __init__(self):
        WT_DIR.mkdir(exist_ok=True)
        self.worktrees = {}
        self.index_path = WT_DIR / "index.json"
        if self.index_path.exists():
            self.worktrees = json.loads(self.index_path.read_text())

    def _save(self):
        self.index_path.write_text(json.dumps(self.worktrees, indent=2, ensure_ascii=False))

    def create(self, name):
        path = WT_DIR / name
        subprocess.run(["git", "worktree", "add", "-b", f"wt/{name}", str(path), "HEAD"],
                       capture_output=True, text=True, cwd=".")
        self.worktrees[name] = {"path": str(path), "created": datetime.datetime.now().isoformat()}
        self._save()
        return f"Created worktree '{name}' at {path}"

    def run_in(self, name, cmd):
        path = self.worktrees[name]["path"]
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=path, timeout=300)
        return r.stdout + r.stderr

    def remove(self, name):
        path = self.worktrees[name]["path"]
        subprocess.run(["git", "worktree", "remove", path], capture_output=True, cwd=".")
        del self.worktrees[name]
        self._save()
        return f"Removed worktree '{name}'"

    def list_all(self):
        if not self.worktrees:
            return "No worktrees"
        return "\n".join(f"- {n}: {info['path']}" for n, info in self.worktrees.items())


# wt initialized lazily

TOOLS = [
    {"type": "function", "function": {"name": "bash", "description": "Run bash",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "wt_create", "description": "Create git worktree",
        "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "wt_run", "description": "Run command in worktree",
        "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "command": {"type": "string"}}, "required": ["name", "command"]}}},
    {"type": "function", "function": {"name": "wt_remove", "description": "Remove worktree",
        "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "wt_list", "description": "List worktrees",
        "parameters": {"type": "object", "properties": {}}}},
]



def agent_loop(query):
    wt = WorktreeManager()
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
                r = subprocess.run(args["command"], shell=True, capture_output=True, text=True, timeout=300)
                output = r.stdout + r.stderr
            elif tc.function.name == "wt_create":
                output = wt.create(args["name"])
            elif tc.function.name == "wt_run":
                output = wt.run_in(args["name"], args["command"])
            elif tc.function.name == "wt_remove":
                output = wt.remove(args["name"])
            elif tc.function.name == "wt_list":
                output = wt.list_all()
            else:
                output = "Unknown"
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(output)})

if __name__ == "__main__":
    query = input("You: ") if len(sys.argv) < 2 else sys.argv[1]
    agent_loop(query)
