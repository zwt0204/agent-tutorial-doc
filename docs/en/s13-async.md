# Chapter 13: Async Tasks -- Background Execution

`s01 > ... > s12 | [ s13 ] > s14 > s15 > s16 > s17`

> *"Long commands shouldn't block the Agent"*

---

## Problem

`npm install` might take 5 minutes. The Agent shouldn't wait idle.

## Solution

```python
class AsyncTaskManager:
    def submit(self, tid, fn, *args):
        thread = threading.Thread(target=wrapper, daemon=True)
        thread.start()

    def check(self, tid):
        # Poll results from queue
        ...
```

Tools: `run_async(command)` returns immediately with task ID. `check_async(tid)` polls status.

## Summary

- Submit and return immediately, execute in background
- Result polling via check_async
- Timeout protection prevents runaway tasks
