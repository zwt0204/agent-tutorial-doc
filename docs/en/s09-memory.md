# Chapter 9: File Memory -- Cross-Session Persistence

`s01 > ... > s08 > [ s09 ] > s10 > s11 > s12`

> *"After compression the Agent may forget who it was. Memory solves this."*

---

## Problem

After context compression, decisions, project structure, and user preferences are all lost.

## Solution

Persist key information to the filesystem:

```
memory/
  index.json           <- metadata
  auth-decision.md     <- "Project uses JWT auth"
  code-style.md        <- "User prefers 4-space indent"
```

```python
class MemoryManager:
    def remember(self, key, value): ...
    def recall(self, query): ...  # keyword search
    def forget(self, key): ...
```

Tools: `remember(key, value)`, `recall(query)`.

## Summary

- Memory persists across sessions via filesystem
- Index supports keyword retrieval
- Remember / recall / forget tools
