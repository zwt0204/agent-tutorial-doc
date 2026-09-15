"""Chapter 1: Agent Loop - the minimal loop."""
import json
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from base import get_client, get_model, run_bash, MAX_TURNS

SYSTEM = "You are a helpful assistant with access to a bash tool."

TOOLS = [
    {"type": "function", "function": {
        "name": "bash", "description": "Run a bash command",
        "parameters": {"type": "object", "properties": {
            "command": {"type": "string"}}, "required": ["command"]}
    }}
]



def agent_loop(query: str):
    client = get_client()
    MODEL = get_model()
    messages = [{"role": "user", "content": query}]

    for turn in range(MAX_TURNS):
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS, max_tokens=8000,
        )
        msg = response.choices[0].message
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
