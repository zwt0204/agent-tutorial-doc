"""Chapter 6: SubAgent - isolated context delegation."""
import json, sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from base import get_client, get_model, run_bash, MAX_TURNS

CHILD_TOOLS = [{"type": "function", "function": {"name": "bash", "description": "Run bash",
    "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}}]

PARENT_TOOLS = CHILD_TOOLS + [{"type": "function", "function": {
    "name": "task", "description": "Spawn subagent with fresh context",
    "parameters": {"type": "object", "properties": {"prompt": {"type": "string"}}, "required": ["prompt"]}
}}]


def run_subagent(prompt: str) -> str:
    client = get_client()
    MODEL = get_model()
    sub_messages = [{"role": "user", "content": prompt}]
    for _ in range(10):
        response = client.chat.completions.create(
            model=MODEL, system="You are a sub-agent. Complete tasks concisely.",
            messages=sub_messages, tools=CHILD_TOOLS, max_tokens=4000)
        msg = response.choices[0].message
        sub_messages.append(msg.model_dump())
        if not msg.tool_calls:
            return msg.content or "(no summary)"
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            output = run_bash(args["command"])
            sub_messages.append({"role": "tool", "tool_call_id": tc.id, "content": output})
    return "(max turns reached)"



def agent_loop(query: str):
    client = get_client()
    MODEL = get_model()
    messages = [{"role": "user", "content": query}]
    for turn in range(MAX_TURNS):
        response = client.chat.completions.create(
            model=MODEL, system="You are a coding assistant. Delegate isolated work to subagents.",
            messages=messages, tools=PARENT_TOOLS, max_tokens=8000)
        msg = response.choices[0].message
        messages.append(msg.model_dump())
        if not msg.tool_calls:
            print(msg.content)
            return
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            if tc.function.name == "task":
                output = run_subagent(args["prompt"])
            else:
                output = run_bash(args.get("command", ""))
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": output})


if __name__ == "__main__":
    query = input("You: ") if len(sys.argv) < 2 else sys.argv[1]
    agent_loop(query)
