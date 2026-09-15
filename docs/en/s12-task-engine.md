# Chapter 12: Task Engine -- Production-Grade Task DAG

`s01 > ... > s11 | [ s12 ] > s13 > s14 > s15 > s16 > s17`

> *"Big goals split into small tasks, ordered, persisted to disk"*

---

## Problem

TODO is flat, no dependencies. Real projects need: task B depends on A, C and D run in parallel, E waits for both.

## Solution: Task DAG

```
task_1 (completed) -> task_2 (pending) -+
                                       +-> task_4 (blocked)
task_1 (completed) -> task_3 (pending) -+
```

```python
class TaskEngine:
    def create(self, subject, blocked_by=None): ...
    def update(self, tid, status="completed"):
        # Auto-clear dependencies when completed
        self._clear_deps(tid)

    def get_ready(self):  # pending + no blockedBy
        ...
```

## Summary

- Task DAG: graph with dependencies
- Auto-unlock: completing a task removes it from others' blockedBy
- Persisted to disk: survives compression and restarts
