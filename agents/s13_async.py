"""Chapter 13: Async tasks - background execution."""
import json, sys, time, threading
from queue import Queue
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from base import get_client, get_model, run_bash, MAX_TURNS

TOOLS = [
    {"type": "function", "function": {"name": "bash", "description": "Run bash",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "run_async", "description": "Run command in background",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "check_async", "description": "Check async task status",
        "parameters": {"type": "object", "properties": {"task_id": {"type": "string"}}, "required": ["task_id"]}}},
]

async_tasks = {}
async_results = Queue()


def run_async_task(tid, cmd):
    try:
        r = __import__("subprocess").run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        async_results.put({"task_id": tid, "result": r.stdout + r.stderr, "error": None})
    except Exception as e:
        async_results.put({"task_id": tid, "result": None, "error": str(e)})


def check_async(tid):
    while not async_results.empty():
        r = async_results.get()
        if r["task_id"] in async_tasks:
            async_tasks[r["task_id"]].update({"status": "done", "result": r})
    return async_tasks.get(tid, {"status": "unknown"})



def agent_loop(query):
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
            elif tc.function.name == "run_async":
                tid = f"async_{int(time.time())}"
                async_tasks[tid] = {"status": "running"}
                t = threading.Thread(target=run_async_task, args=(tid, args["command"]), daemon=True)
                t.start()
                output = f"Started: {tid}"
            elif tc.function.name == "check_async":
                output = json.dumps(check_async(args["task_id"]), default=str, indent=2)
            else:
                output = "Unknown"
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(output)})

if __name__ == "__main__":
    query = input("You: ") if len(sys.argv) < 2 else sys.argv[1]
    agent_loop(query)
