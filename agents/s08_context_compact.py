"""Chapter 8: Context compaction - three-layer compression."""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from base import get_client, get_model, run_bash, estimate_tokens, MAX_TURNS

KEEP_RECENT = 3
THRESHOLD = 50000

TOOLS = [{"type": "function", "function": {"name": "bash", "description": "Run bash",
    "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "compact", "description": "Manually compress conversation",
        "parameters": {"type": "object", "properties": {}}}}]


def micro_compact(messages):
    tool_results = [(i, j, part) for i, msg in enumerate(messages)
                    if msg.get("role") == "user" and isinstance(msg.get("content"), list)
                    for j, part in enumerate(msg["content"])
                    if isinstance(part, dict) and part.get("role") == "tool"]
    if len(tool_results) <= KEEP_RECENT:
        return
    for _, _, part in tool_results[:-KEEP_RECENT]:
        content = part.get("content", "")
        if len(content) > 100:
            part["content"] = "[Previous result truncated]"


def auto_compact(messages):
    transcript_dir = Path(".transcripts")
    transcript_dir.mkdir(exist_ok=True)
    with open(transcript_dir / f"t_{int(time.time())}.jsonl", "w") as f:
        for m in messages:
            f.write(json.dumps(m, default=str) + "\n")
    resp = client.chat.completions.create(model=MODEL, max_tokens=2000, messages=[
        {"role": "user", "content": "Summarize this conversation briefly:\n" + json.dumps(messages, default=str)[:60000]}
    ])
    summary = resp.choices[0].message.content
    messages.clear()
    messages.append({"role": "user", "content": f"[Compressed]\n{summary}"})



def agent_loop(query: str):
    client = get_client()
    MODEL = get_model()
    messages = [{"role": "user", "content": query}]
    for turn in range(MAX_TURNS):
        micro_compact(messages)
        if estimate_tokens(messages) > THRESHOLD:
            auto_compact(messages)
        response = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS, max_tokens=8000)
        msg = response.choices[0].message
        messages.append(msg.model_dump())
        if not msg.tool_calls:
            print(msg.content)
            return
        results = []
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            if tc.function.name == "compact":
                auto_compact(messages)
                output = "Conversation compressed."
            else:
                output = run_bash(args.get("command", ""))
            results.append({"role": "tool", "tool_call_id": tc.id, "content": output})
        messages.extend(results)


if __name__ == "__main__":
    query = input("You: ") if len(sys.argv) < 2 else sys.argv[1]
    agent_loop(query)
