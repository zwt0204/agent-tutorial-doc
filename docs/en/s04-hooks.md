# Chapter 4: Hook System -- Lifecycle Callbacks

`s01 > s02 > s03 > [ s04 ] s05 > s06 | s07 > s08 > s09 > s10 > s11 > s12`

> *"At four critical moments, insert your own logic"* -- Zero-invasion extension.

---

## Problem

Permission checks are static. Real scenarios need dynamic behavior: validate prompts before submission, log before tool execution, save state on stop. These can't be hardcoded in the loop.

## Solution: Four Lifecycle Hooks

```
User prompt
    |
    v
[UserPromptSubmit]  <-- before prompt processing
    |
    v
loop:
    LLM response
        |
    [PreToolUse]     <-- before tool execution
        |
    execute tool
        |
    [PostToolUse]    <-- after tool execution
        |
    append result

[Stop]              <-- before agent exits
```

## Implementation

```python
class HookManager:
    def __init__(self):
        self.hooks = {"PreToolUse": [], "PostToolUse": [], "Stop": []}

    def register(self, event, fn):
        self.hooks[event].append(fn)

    def fire(self, event, data):
        for fn in self.hooks[event]:
            result = fn(data)
            if result is False: return None  # block execution
            if isinstance(result, dict): data.update(result)
        return data
```

## Try it

```bash
python3 agents/s04_hooks.py
```

1. `list files` (observe PreToolUse/PostToolUse logs)
2. `read README.md` (observe log output)
3. Ctrl+C to stop (observe Stop hook)

## Summary

- 4 lifecycle hooks: PreToolUse / PostToolUse / Stop
- Hooks decouple cross-cutting concerns (logging, auditing) from core loop
- Return False to block execution (security interception)
