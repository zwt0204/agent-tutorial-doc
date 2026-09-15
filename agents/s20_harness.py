"""Chapter 20: Full harness - unified runtime."""
import json, sys, os, time, datetime, subprocess, threading
from pathlib import Path
from typing import Callable
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from base import get_client, get_model, run_bash, safe_path, estimate_tokens, MAX_TURNS

# ─── Ch03: Permission ───
class PermissionPolicy:
    def __init__(self):
        self.rules = {"bash": "ask", "write_file": "ask_once", "read_file": "allow"}
        self.granted = set()
    def check(self, name):
        perm = self.rules.get(name, "allow")
        return "allow" if perm == "ask_once" and name in self.granted else perm
    def grant(self, name):
        self.granted.add(name)

# ─── Ch04: Hooks ───
class HookManager:
    def __init__(self):
        self.hooks = {"PreToolUse": [], "PostToolUse": [], "Stop": []}
    def register(self, event, fn):
        self.hooks[event].append(fn)
    def fire(self, event, data):
        for fn in self.hooks[event]:
            result = fn(data)
            if isinstance(result, dict):
                data.update(result)
        return data

# ─── Ch07: Skills ───
class SkillManager:
    def __init__(self):
        self.skills = {}
        skills_dir = Path(__file__).parent.parent / "skills"
        if skills_dir.exists():
            for f in skills_dir.glob("*.md"):
                content = f.read_text(encoding="utf-8")
                self.skills[f.stem] = content.split("\n")[0]
    def list_skills(self):
        return "\n".join(f"- {k}: {v}" for k, v in self.skills.items()) or "No skills"

# ─── Ch09: Memory ───
class MemoryManager:
    def __init__(self):
        self.dir = Path("./memory")
        self.dir.mkdir(exist_ok=True)
        self.index_path = self.dir / "index.json"
        self.index = json.loads(self.index_path.read_text()) if self.index_path.exists() else []
    def remember(self, key, value):
        self.index.append({"key": key, "value": value})
        self.index_path.write_text(json.dumps(self.index, ensure_ascii=False))
        return f"Remembered: {key}"
    def recall(self, query):
        results = [e for e in self.index if query.lower() in (e["key"] + e["value"]).lower()]
        return "\n".join(f"- {e['key']}: {e['value'][:100]}" for e in results[:5]) or "None"

# ─── Ch12: Tasks ───
class TaskEngine:
    def __init__(self):
        self.dir = Path("./tasks")
        self.dir.mkdir(exist_ok=True)
    def create(self, subject):
        tid = max([int(f.stem.split("_")[1]) for f in self.dir.glob("task_*.json")], default=0) + 1
        task = {"id": tid, "subject": subject, "status": "pending", "blockedBy": []}
        (self.dir / f"task_{tid}.json").write_text(json.dumps(task, indent=2, ensure_ascii=False))
        return task
    def list_all(self):
        return [json.loads(f.read_text()) for f in sorted(self.dir.glob("task_*.json"))]
    def render(self):
        return "\n".join(f"  {'●' if t['status']=='completed' else '○'} #{t['id']}: {t['subject']}" for t in self.list_all()) or "No tasks"

# ─── Full Harness ───
class AgentHarness:
    def __init__(self):
        self.policy = PermissionPolicy()
        self.hooks = HookManager()
        self.skills = SkillManager()
        self.memory = MemoryManager()
        self.tasks = TaskEngine()

        self.hooks.register("PreToolUse", lambda d: (print(f"[PRE] {d['tool_name']}"), d)[1])
        self.hooks.register("PostToolUse", lambda d: (print(f"[POST] {d['tool_name']}"), d)[1])

    def get_tools(self):
        return [
            {"type": "function", "function": {"name": "bash", "description": "Run bash",
                "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
            {"type": "function", "function": {"name": "read_file", "description": "Read file",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
            {"type": "function", "function": {"name": "write_file", "description": "Write file",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
            {"type": "function", "function": {"name": "remember", "description": "Store memory",
                "parameters": {"type": "object", "properties": {"key": {"type": "string"}, "value": {"type": "string"}}, "required": ["key", "value"]}}},
            {"type": "function", "function": {"name": "recall", "description": "Recall memory",
                "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
            {"type": "function", "function": {"name": "task_create", "description": "Create task",
                "parameters": {"type": "object", "properties": {"subject": {"type": "string"}}, "required": ["subject"]}}},
            {"type": "function", "function": {"name": "task_list", "description": "List tasks",
                "parameters": {"type": "object", "properties": {}}}},
            {"type": "function", "function": {"name": "list_skills", "description": "List skills",
                "parameters": {"type": "object", "properties": {}}}},
        ]

    def execute_tool(self, name, args):
        perm = self.policy.check(name)
        if perm == "deny":
            return "Permission denied"
        if perm in ("ask", "ask_once"):
            if perm == "ask_once" and name in self.policy.granted:
                pass
            else:
                ans = input(f"  Allow {name}? [y/N]: ").strip().lower()
                if ans != "y":
                    return "Denied"
                if perm == "ask_once":
                    self.policy.grant(name)

        if name == "bash":
            return run_bash(args["command"])
        elif name == "read_file":
            return safe_path(args["path"]).read_text(encoding="utf-8")[:50000]
        elif name == "write_file":
            p = safe_path(args["path"])
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(args["content"], encoding="utf-8")
            return f"Written to {args['path']}"
        elif name == "remember":
            return self.memory.remember(args["key"], args["value"])
        elif name == "recall":
            return self.memory.recall(args["query"])
        elif name == "task_create":
            t = self.tasks.create(args["subject"])
            return f"Created task #{t['id']}"
        elif name == "task_list":
            return self.tasks.render()
        elif name == "list_skills":
            return self.skills.list_skills()
        return f"Unknown: {name}"

    def run(self, query):
        client = get_client()
        MODEL = get_model()
        messages = [{"role": "user", "content": query}]
        for turn in range(MAX_TURNS):
            micro_compact(messages)
            sys_prompt = f"You are a coding assistant.\n\n{self.skills.list_skills()}"
            resp = client.chat.completions.create(model=MODEL, system=sys_prompt,
                messages=messages, tools=self.get_tools(), max_tokens=8000)
            msg = resp.choices[0].message
            messages.append(msg.model_dump())
            if not msg.tool_calls:
                self.hooks.fire("Stop", {})
                print(msg.content)
                return
            results = []
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments)
                self.hooks.fire("PreToolUse", {"tool_name": tc.function.name})
                output = self.execute_tool(tc.function.name, args)
                self.hooks.fire("PostToolUse", {"tool_name": tc.function.name, "result": output})
                results.append({"role": "tool", "tool_call_id": tc.id, "content": str(output)})
            messages.extend(results)


def micro_compact(messages):
    tool_results = [(i, j, p) for i, m in enumerate(messages)
                    if m.get("role") == "user" and isinstance(m.get("content"), list)
                    for j, p in enumerate(m["content"])
                    if isinstance(p, dict) and p.get("role") == "tool"]
    for _, _, p in tool_results[:-3]:
        if len(str(p.get("content", ""))) > 100:
            p["content"] = "[truncated]"


if __name__ == "__main__":
    harness = AgentHarness()
    query = input("You: ") if len(sys.argv) < 2 else sys.argv[1]
    harness.run(query)
