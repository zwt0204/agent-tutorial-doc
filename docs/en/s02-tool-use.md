# Chapter 2: Tools & Files -- Adding a Tool Is One Line

`s01 > [ s02 ] s03 > s04 > s05 > s06 | s07 > s08 > s09 > s10 > s11 > s12`

> *"Add a tool, add one handler"* -- The loop doesn't change; register into the dispatch map.
>
> **Harness layer**: Tool dispatch -- expanding what the model can reach.

---

## Chapter Preview

### What you'll learn

1. Why `bash` alone isn't enough.
2. The dispatch map pattern: add tool = add handler + add schema, loop unchanged.
3. Path sandboxing to prevent directory escape.
4. Expand from 1 tool to 4: bash, read_file, write_file, edit_file.

### Prerequisites

| Need | Level |
| --- | --- |
| Previous chapter | Agent Loop understanding |
| Python | Dicts, functions, pathlib |

---

## Problem

With only `bash`, all operations go through shell. `cat` truncates unpredictably, `sed` crashes on special characters, every bash call is an unconstrained security surface.

**Key insight: Adding tools doesn't require changing the loop.**

---

## Solution

```
User -> LLM -> Tool Dispatch {
    bash: run_bash
    read: run_read
    write: run_write
    edit: run_edit
}
```

The dispatch map is a dict: `{tool_name: handler_function}`. One lookup replaces any if/elif chain.

---

## Implementation

### Path sandbox

```python
from pathlib import Path
WORKDIR = Path.cwd()

def safe_path(p: str) -> Path:
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path
```

### Four tool handlers

```python
def run_read(path: str, limit: int = None) -> str:
    text = safe_path(path).read_text(encoding="utf-8")
    lines = text.splitlines()
    if limit: lines = lines[:limit]
    return "\n".join(lines)[:50000]

def run_write(path: str, content: str) -> str:
    p = safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Written {len(content)} bytes to {path}"

def run_edit(path: str, old_text: str, new_text: str) -> str:
    p = safe_path(path)
    text = p.read_text(encoding="utf-8")
    if old_text not in text:
        return f"Error: old_text not found in {path}"
    p.write_text(text.replace(old_text, new_text, 1), encoding="utf-8")
    return f"Edited {path}"
```

### Dispatch map

```python
HANDLERS = {
    "bash":       lambda **kw: run_bash(kw["command"]),
    "read_file":  lambda **kw: run_read(kw["path"], kw.get("limit")),
    "write_file": lambda **kw: run_write(kw["path"], kw["content"]),
    "edit_file":  lambda **kw: run_edit(kw["path"], kw["old_text"], kw["new_text"]),
}
```

### Loop uses dispatch

```python
for tc in msg.tool_calls:
    handler = HANDLERS.get(tc.function.name)
    output = handler(**args) if handler else f"Unknown: {tc.function.name}"
    messages.append({"role": "tool", "tool_call_id": tc.id, "content": output})
```

**Adding tools = adding handler + adding schema. Loop unchanged.**

---

## Changes from s01

| Component | Before (s01) | After (s02) |
| --- | --- | --- |
| Tools | 1 (bash only) | 4 (bash, read, write, edit) |
| Dispatch | Hardcoded bash call | `HANDLERS` dict |
| Path safety | None | `safe_path()` sandbox |
| Agent loop | Unchanged | Unchanged |

---

## Try it

```bash
python3 agents/s02_tool_use.py
```

1. `Read the first 10 lines of requirements.txt`
2. `Create greet.py with a greet(name) function`
3. `Edit greet.py to add a docstring`
4. `Read greet.py to verify the edit`

---

## Summary

- Dispatch map pattern makes adding tools trivial
- `safe_path()` provides path sandboxing at the tool layer
- Loop body identical to s01 -- all expansion is outside the loop
