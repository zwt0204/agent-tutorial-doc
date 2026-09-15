"""Chapter 12: Task engine - DAG with dependencies."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from base import get_client, get_model, run_bash, MAX_TURNS

TASKS_DIR = Path("./tasks")


class TaskEngine:
    def __init__(self):
        TASKS_DIR.mkdir(exist_ok=True)

    def _next_id(self):
        existing = list(TASKS_DIR.glob("task_*.json"))
        return max([int(f.stem.split("_")[1]) for f in existing], default=0) + 1

    def create(self, subject, blocked_by=None):
        tid = self._next_id()
        task = {"id": tid, "subject": subject, "status": "pending", "blockedBy": blocked_by or [], "owner": ""}
        self._save(task)
        return task

    def update(self, tid, **kw):
        task = self._load(tid)
        task.update(kw)
        if task.get("status") == "completed":
            self._clear_deps(tid)
        self._save(task)
        return task

    def _load(self, tid):
        return json.loads((TASKS_DIR / f"task_{tid}.json").read_text())

    def _save(self, task):
        (TASKS_DIR / f"task_{task['id']}.json").write_text(json.dumps(task, indent=2, ensure_ascii=False))

    def _clear_deps(self, done_id):
        for f in TASKS_DIR.glob("task_*.json"):
            t = json.loads(f.read_text())
            if done_id in t.get("blockedBy", []):
                t["blockedBy"].remove(done_id)
                self._save(t)

    def list_all(self):
        return [json.loads(f.read_text()) for f in sorted(TASKS_DIR.glob("task_*.json"))]

    def get_ready(self):
        return [t for t in self.list_all() if t["status"] == "pending" and not t["blockedBy"]]

    def render_dag(self):
        lines = []
        for t in self.list_all():
            m = {"pending": "○", "in_progress": "◐", "completed": "●"}.get(t["status"], "?")
            d = f" <- {t['blockedBy']}" if t["blockedBy"] else ""
            lines.append(f"  {m} #{t['id']}: {t['subject']}{d}")
        return "Task DAG:\n" + "\n".join(lines)


# tasks initialized lazily in agent_loop

TOOLS = [
    {"type": "function", "function": {"name": "bash", "description": "Run bash",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "task_create", "description": "Create a task",
        "parameters": {"type": "object", "properties": {"subject": {"type": "string"}, "blocked_by": {"type": "array", "items": {"type": "integer"}}}, "required": ["subject"]}}},
    {"type": "function", "function": {"name": "task_update", "description": "Update task status",
        "parameters": {"type": "object", "properties": {"task_id": {"type": "integer"}, "status": {"type": "string"}}, "required": ["task_id", "status"]}}},
    {"type": "function", "function": {"name": "task_list", "description": "List all tasks as DAG",
        "parameters": {"type": "object", "properties": {}}}},
]



def agent_loop(query):
    tasks = TaskEngine()
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
            elif tc.function.name == "task_create":
                t = tasks.create(args["subject"], args.get("blocked_by"))
                output = f"Created task #{t['id']}: {t['subject']}"
            elif tc.function.name == "task_update":
                tasks.update(args["task_id"], status=args["status"])
                output = f"Task #{args['task_id']} -> {args['status']}"
            elif tc.function.name == "task_list":
                output = tasks.render_dag()
            else:
                output = "Unknown"
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": output})

if __name__ == "__main__":
    query = input("You: ") if len(sys.argv) < 2 else sys.argv[1]
    agent_loop(query)
