# Chapter 6: Sub-Agents -- Isolated Context Delegation

`s01 > s02 > s03 > s04 > s05 > [ s06 ] | s07 > s08 > s09 > s10 > s11 > s12`

> *"Big tasks split small, each small task gets fresh context"*

---

## Problem

As the Agent works, messages grow. Reading 5 files to answer "what test framework does this project use?" bloats the parent context. But the parent only needs one word: "pytest."

## Solution

SubAgent runs with its own messages list, executes independently, returns only a summary. Parent context stays clean.

```
Parent Agent                     SubAgent
messages=[...]                   messages=[]  <-- fresh
    |                                |
    | dispatch                       |
    | prompt="..."                   |
    +----------------------------->  | run tools
    |                                | append results
    | result = "pytest"              |
    +<-----------------------------  | return text
```

## Implementation

```python
def run_subagent(prompt: str) -> str:
    client = get_client()
    MODEL = get_model()
    sub_messages = [{"role": "user", "content": prompt}]
    for _ in range(10):  # safety limit
        resp = client.chat.completions.create(model=MODEL, system="...",
            messages=sub_messages, tools=CHILD_TOOLS, max_tokens=4000)
        msg = resp.choices[0].message
        sub_messages.append(msg.model_dump())
        if not msg.tool_calls:
            return msg.content or "(no summary)"
        # execute tools...
    return "(max turns reached)"
```

Parent's `task` tool calls `run_subagent`. SubAgent has no `task` tool (no recursion). Only summary text returns to parent.

## Summary

- SubAgent: isolated messages, discard after completion
- Returns only summary, parent context stays clean
- No recursion: SubAgent has no `task` tool
- Turn limit prevents runaway
