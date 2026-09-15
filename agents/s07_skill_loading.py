"""Chapter 7: Skill loading - two-step knowledge."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from base import get_client, get_model, run_bash, MAX_TURNS

SKILLS_DIR = Path(__file__).parent.parent / "skills"


class SkillManager:
    def __init__(self):
        self.skills = {}
        if SKILLS_DIR.exists():
            for f in SKILLS_DIR.glob("*.md"):
                content = f.read_text(encoding="utf-8")
                self.skills[f.stem] = {"summary": content.split("\n")[0], "path": f}

    def list_skills(self) -> str:
        if not self.skills:
            return "No skills available."
        return "Skills:\n" + "\n".join(f"- {k}: {v['summary']}" for k, v in self.skills.items())

    def load(self, name: str) -> str:
        if name not in self.skills:
            return f"Skill '{name}' not found."
        return self.skills[name]["path"].read_text(encoding="utf-8")[:50000]


skills = SkillManager()

TOOLS = [
    {"type": "function", "function": {"name": "bash", "description": "Run bash",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "list_skills", "description": "List available skills",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "load_skill", "description": "Load a skill by name",
        "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
]



def agent_loop(query: str):
    client = get_client()
    MODEL = get_model()
    messages = [{"role": "user", "content": query}]
    for turn in range(MAX_TURNS):
        sys_prompt = f"You are a coding assistant.\n\n{skills.list_skills()}"
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
            elif tc.function.name == "list_skills":
                output = skills.list_skills()
            elif tc.function.name == "load_skill":
                output = skills.load(args["name"])
            else:
                output = f"Unknown: {tc.function.name}"
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(output)})


if __name__ == "__main__":
    query = input("You: ") if len(sys.argv) < 2 else sys.argv[1]
    agent_loop(query)
