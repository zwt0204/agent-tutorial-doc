# Chapter 3: Permission System -- Production-Grade Agent Security

`s01 > s02 > [ s03 ] s04 > s05 > s06 | s07 > s08 > s09 > s10 > s11 > s12`

> *"An Agent can only do what you allow it to do"* -- 4-state permission + audit log.

---

## Problem

The s02 Agent can run any bash command, including `rm -rf /`. Production environments need: auto-allow reads, require approval for writes, block dangerous operations.

## Solution: 4-State Permission Model

| State | Behavior |
| --- | --- |
| **ALLOW** | Auto-execute, no prompt |
| **ASK** | Require user approval every time |
| **ASK_ONCE** | Require approval first time, auto-allow after |
| **DENY** | Block unconditionally |

```python
class PermissionPolicy:
    def __init__(self):
        self.rules = {}      # tool_name -> permission
        self.granted = set() # ASK_ONCE tools already approved

    def check(self, tool_name: str) -> str:
        perm = self.rules.get(tool_name, "allow")
        if perm == "ask_once" and tool_name in self.granted:
            return "allow"
        return perm

    def grant_once(self, tool_name: str):
        self.granted.add(tool_name)
```

## Tool Execution Interceptor

```python
def execute_tool(name, args):
    perm = policy.check(name)
    if perm == "deny":
        return "Permission denied"
    if perm in ("ask", "ask_once"):
        if perm == "ask_once" and name in policy.granted:
            pass
        else:
            ans = input(f"  Allow {name}? [y/N]: ").strip().lower()
            if ans != "y": return "Denied"
            if perm == "ask_once": policy.granted.add(name)
    return HANDLERS[name](**args)
```

## Audit Log

Every tool call records: timestamp, tool name, permission decision, result preview.

## Changes from s02

| Component | Before (s02) | After (s03) |
| --- | --- | --- |
| Tool execution | Direct handler call | Passes through permission check |
| Permissions | None | 4-state model |
| Audit | None | Every call logged |
| Agent loop | Unchanged | Unchanged (permission outside loop) |

## Try it

```bash
python3 agents/s03_permission.py
```

1. `Read README.md` (auto-allow, no approval)
2. `Create test.txt` (first write requires approval)
3. `Write to test.txt again` (ASK_ONCE second time is auto)
4. `Run rm -rf /` (should be denied)

## Summary

- 4-state permission: ALLOW / ASK / DENY / ASK_ONCE
- Permission check sits between loop and handler, loop unchanged
- ASK_ONCE is a practical compromise: approve once, auto after
- Audit log records every decision for post-hoc review
