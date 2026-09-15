# Chapter 16: Protocols -- Structured Collaboration

`s01 > ... > s15 > [ s16 ] > s17`

> *"Multi-Agent collaboration needs clear rules"*

---

## Problem

Without protocols, Agents step on each other. Who's responsible for what? How do you hand off?

## Solution

```python
class ProtocolManager:
    def define(self, name, steps):
        # steps = [{"assignee": "alice", "desc": "submit"}, ...]

    def execute(self, name, agent):
        # Only the assigned agent can execute the step
```

## Summary

- Protocols define clear collaboration steps
- Steps bound to specific Agents
- Status tracking prevents omissions
