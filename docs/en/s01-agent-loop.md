# Chapter 1: Agent Loop -- One Loop Is All You Need

`[ s01 ] s02 > s03 > s04 > s05 > s06 | s07 > s08 > s09 > s10 > s11 > s12`

> *"One loop & Bash is all you need"* -- One tool + one loop = one Agent.
>
> **Harness layer**: Loop -- the first connection between model and real world.

---

## Chapter Preview

### What you'll learn

1. Explain in one sentence the difference between an Agent and "calling an LLM API once."
2. Read the JSON fields exchanged in a single Agent conversation round.
3. Write a working Agent Loop in under 30 lines.
4. Know when the loop terminates and why you need a turn limit.

### Prerequisites

| Need | Level |
| --- | --- |
| Python | Functions, dicts, lists |
| CLI | Run `pip` and `python` |
| LLM API | Know that "send message, get text" works |
| Previous chapter | None. This is Chapter 1 |

### Glossary

| Term | One-line explanation |
| --- | --- |
| **Agent Loop** | "Ask model -> execute tool -> feed result back -> ask again" cycle |
| **Harness** | Everything outside the loop: config, tool registry, approval, turn limits |
| **Turn** | One request sent to the model (not one tool call) |
| **tool_use** | A block in model reply indicating "I want to use a tool" |
| **tool_result** | Tool execution output, appended as a user message |
| **stop_reason** | Why the model stopped. `tool_use` means more work; anything else means done |

---

## What role are you playing right now

Without an Agent, you use LLMs like this: you type "list Python files in this directory", the model outputs `ls *.py`, but it doesn't run it. You switch to terminal, paste, run, copy output, switch back, paste output. Every round, you're the human loop between model and real world.

**An Agent Loop replaces you in that middle layer.**

---

## Two signals, one loop

```
Does model reply contain tool_use?
├── Yes -> execute tool, append result, ask model again
└── No  -> done. Model's final text is the answer
```

That's it. One exit condition controls everything.

---

## Real data flow

**Round 1 -- User:**
```json
messages = [{"role": "user", "content": "List files"}]
```

**Model reply -- wants a tool:**
```json
{"content": [{"type": "tool_use", "name": "bash", "input": {"command": "ls"}, "id": "call_001"}], "stop_reason": "tool_use"}
```

**Program appends result:**
```json
{"role": "user", "content": [{"type": "tool_result", "tool_use_id": "call_001", "content": "main.py\ntest.py\n"}]}
```

**Round 2 -- Model says:** "There are main.py and test.py." `stop_reason` is no longer `tool_use`. Loop ends.

---

## Complete function

```python
import os, json
from openai import OpenAI

client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

TOOLS = [{"type": "function", "function": {
    "name": "bash", "description": "Run a bash command",
    "parameters": {"type": "object", "properties": {
        "command": {"type": "string"}}, "required": ["command"]}
}}]

def run_bash(command: str) -> str:
    import subprocess
    r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
    return r.stdout + r.stderr

def agent_loop(query: str):
    client = get_client()
    MODEL = get_model()
    messages = [{"role": "user", "content": query}]

    for turn in range(20):
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS, max_tokens=8000)
        msg = resp.choices[0].message
        messages.append(msg.model_dump())

        if not msg.tool_calls:
            print(msg.content)
            return

        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            output = run_bash(args["command"])
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": output})

if __name__ == "__main__":
    agent_loop(input("You: "))
```

Under 30 lines. That's the entire Agent. Chapters 2-20 only add mechanisms around this loop -- **the loop itself never changes**.

---

## Why you need a turn limit

The model might loop infinitely (re-reading the same file). `for turn in range(20)` ensures the program always exits. Production systems typically use 50-100.

---

## Try it

```bash
python3 agents/s01_agent_loop.py
```

1. `list files in the current directory`
2. `create a hello.py that prints Hello, World!`
3. `what time is it?`
4. `how many Python files are here?`

---

## Summary

- Agent = Model + Harness (loop + tools + safety boundaries)
- Agent Loop is "ask model -> execute tool -> feed back"
- `stop_reason != "tool_use"` is the only exit condition
- Turn limit prevents infinite loops
- The loop doesn't change across chapters; later chapters only add外围 capabilities
