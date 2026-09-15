# 第 13 章:异步操作 -- 填坑慢操作

`s01 > ... > s12 | [ s13 ] > s14 > s15 > s16 > s17`

> *"长命令不应该阻塞 Agent"* -- 后台执行、结果轮询、超时保护。
>
> **Harness 层**: 异步 -- 让 Agent 在等待时做其他事。

---

## 问题

文件 I/O、API 调用、长时间运行的命令会阻塞 Agent。`npm install` 可能跑 5 分钟,Agent 不应该傻等。

## 解决方案

```python
import threading
from queue import Queue

class AsyncTaskManager:
    def __init__(self):
        self.tasks = {}
        self.results = Queue()

    def submit(self, task_id: str, fn, *args, **kwargs):
        def wrapper():
            try:
                result = fn(*args, **kwargs)
                self.results.put({"task_id": task_id, "result": result, "error": None})
            except Exception as e:
                self.results.put({"task_id": task_id, "result": None, "error": str(e)})

        thread = threading.Thread(target=wrapper, daemon=True)
        self.tasks[task_id] = {"thread": thread, "status": "running"}
        thread.start()

    def check(self, task_id: str) -> dict:
        while not self.results.empty():
            result = self.results.get()
            if result["task_id"] in self.tasks:
                self.tasks[result["task_id"]]["status"] = "completed"
                self.tasks[result["task_id"]]["result"] = result
        return self.tasks.get(task_id, {"status": "unknown"})

async_tasks = AsyncTaskManager()
```

## 试一试

```bash
python agents/s13_async.py
```

1. `后台运行 "sleep 5 && echo done"`
2. `检查异步任务状态`
3. `同时运行多个后台任务`

## 本章小结

- 异步任务:提交后立即返回,后台执行
- 结果轮询:check_async 检查状态
- 超时保护:防止任务无限运行
