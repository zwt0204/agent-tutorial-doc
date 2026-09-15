# Chapter 5: Session Planning -- Preventing Task Drift

`s01 > s02 > s03 > s04 > [ s05 ] > s06 | s07 > s08 > s09 > s10 > s11 > s12`

> *"Long tasks need anchors, otherwise the Agent forgets what it's doing"*

---

## Problem

In long conversations, the Agent gradually drifts from its original goal. It said "refactor the auth module" but after reading 20 files and running 10 commands, it's doing something unrelated.

## Solution

Inject a TODO list into the system prompt:

```
Current plan:
- [x] Read existing auth code
- [ ] Refactor to JWT
- [ ] Update tests
- [ ] Update docs
```

The Agent sees its plan at every model call and stays on track.

## Implementation

```python
class TodoManager:
    def __init__(self):
        self.items = []

    def add(self, text): self.items.append({"text": text, "status": "pending"})
    def done(self, index): self.items[index]["status"] = "done"
    def render(self):
        return "Plan:\n" + "\n".join(
            f"- [{'x' if i['status']=='done' else ' '}] {i['text']}"
            for i in self.items)
```

Inject into system prompt, add `todo_add` and `todo_done` tools. The Agent manages its own plan.

## Summary

- TODO in system prompt prevents task drift
- Agent updates plan autonomously via tools
- Simple list solves 80% of planning needs
