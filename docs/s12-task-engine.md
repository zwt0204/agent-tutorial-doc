# 第 12 章:任务引擎 -- 生产级的 Task DAG

`s01 > ... > s11 | [ s12 ] > s13 > s14 > s15 > s16 > s17`

> *"大目标要拆成小任务,排好序,记在磁盘上"* -- 带依赖关系的任务图。
>
> **Harness 层**: 任务持久化 -- 比任何一次对话都长命的目标。

---

## 问题

TODO 太简单,没有依赖关系。真实项目需要:任务 B 依赖任务 A,任务 C 和 D 可以并行,任务 E 要等 C 和 D 都完成。

## 解决方案

```
.tasks/
  task_1.json  {"id":1, "status":"completed"}
  task_2.json  {"id":2, "blockedBy":[1], "status":"pending"}
  task_3.json  {"id":3, "blockedBy":[1], "status":"pending"}
  task_4.json  {"id":4, "blockedBy":[2,3], "status":"pending"}

任务图 (DAG):
                 +----------+
            +--> | task 2   | --+
            |    | pending  |   |
+----------+     +----------+    +--> +----------+
| task 1   |                          | task 4   |
| completed| --> +----------+    +--> | blocked  |
+----------+     | task 3   | --+     +----------+
                 | pending  |
                 +----------+
```

## 工作原理

```python
from pathlib import Path
import json

TASKS_DIR = Path("./tasks")

class TaskEngine:
    def __init__(self):
        TASKS_DIR.mkdir(exist_ok=True)

    def create(self, subject: str, blocked_by: list = None) -> dict:
        task_id = self._next_id()
        task = {"id": task_id, "subject": subject, "status": "pending",
                "blockedBy": blocked_by or [], "owner": ""}
        self._save(task)
        return task

    def update(self, task_id: int, **kwargs):
        task = self._load(task_id)
        task.update(kwargs)
        if task.get("status") == "completed":
            self._clear_dependency(task_id)
        self._save(task)

    def _clear_dependency(self, completed_id: int):
        for f in TASKS_DIR.glob("task_*.json"):
            task = json.loads(f.read_text(encoding="utf-8"))
            if completed_id in task.get("blockedBy", []):
                task["blockedBy"].remove(completed_id)
                self._save(task)

    def get_ready_tasks(self) -> list:
        ready = []
        for f in sorted(TASKS_DIR.glob("task_*.json")):
            task = json.loads(f.read_text(encoding="utf-8"))
            if task["status"] == "pending" and not task["blockedBy"]:
                ready.append(task)
        return ready

    def render_dag(self) -> str:
        lines = ["Task DAG:"]
        for f in sorted(TASKS_DIR.glob("task_*.json")):
            task = json.loads(f.read_text(encoding="utf-8"))
            mark = {"pending": "○", "in_progress": "◐", "completed": "●"}.get(task["status"], "?")
            deps = f" <- {task['blockedBy']}" if task["blockedBy"] else ""
            lines.append(f"  {mark} Task {task['id']}: {task['subject']}{deps}")
        return "\n".join(lines)

tasks = TaskEngine()
```

## 相对 s11 的变更

| 组件 | 之前 (s11) | 之后 (s12) |
| --- | --- | --- |
| 任务管理 | 无 | 带依赖关系的 DAG |
| 持久化 | 无 | JSON 文件 |
| 依赖解除 | 无 | 完成时自动解锁后续 |

## 试一试

```bash
python agents/s12_task_engine.py
```

1. `创建 3 个任务:"Setup project", "Write code", "Write tests",按顺序依赖`
2. `完成 task 1,然后查看 task 2 是否解锁`
3. `创建一个并行任务图:parse -> transform -> emit -> test`

## 本章小结

- 任务 DAG:带依赖关系的任务图
- 自动依赖解除:完成任务时自动解锁后续
- 持久化到磁盘:压缩和重启后存活
