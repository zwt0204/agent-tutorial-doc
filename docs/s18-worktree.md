# 第 18 章:Worktree 隔离 -- 并行开发的安全边界

`s01 > ... > s17 > [ s18 ]`

> *"各干各的目录,互不干扰"* -- 任务管目标,worktree 管目录。
>
> **Harness 层**: 目录隔离 -- 永不碰撞的并行执行通道。

---

## 问题

所有任务共享一个目录。两个 Agent 同时重构不同模块 -- A 改 `config.py`,B 也改 `config.py`,未提交的改动互相污染。

## 解决方案

```
Control plane (.tasks/)             Execution plane (.worktrees/)
+------------------+                +------------------------+
| task_1.json      |                | auth-refactor/         |
|   status: in_progress  <------>   branch: wt/auth-refactor
|   worktree: "auth-refactor"   |   task_id: 1             |
+------------------+                +------------------------+
| task_2.json      |                | ui-login/              |
|   status: pending    <------>     branch: wt/ui-login
|   worktree: "ui-login"       |   task_id: 2             |
+------------------+                +------------------------+
```

## 工作原理

```python
class WorktreeManager:
    def __init__(self):
        self.worktrees = {}
        self.worktree_dir = Path("./worktrees")
        self.worktree_dir.mkdir(exist_ok=True)

    def create(self, name: str, task_id: int = None) -> str:
        branch = f"wt/{name}"
        path = self.worktree_dir / name
        subprocess.run(["git", "worktree", "add", "-b", branch, str(path), "HEAD"],
                       capture_output=True, text=True)
        self.worktrees[name] = {"path": path, "branch": branch, "task_id": task_id}
        if task_id:
            tasks.update(task_id, status="in_progress")
        return f"Created worktree '{name}'"

    def run_in(self, name: str, command: str) -> str:
        path = self.worktrees[name]["path"]
        result = subprocess.run(command, shell=True, cwd=str(path),
                                capture_output=True, text=True, timeout=300)
        return result.stdout + result.stderr

    def remove(self, name: str, complete_task: bool = False) -> str:
        wt = self.worktrees[name]
        if complete_task and wt.get("task_id"):
            tasks.update(wt["task_id"], status="completed")
        subprocess.run(["git", "worktree", "remove", str(wt["path"])], capture_output=True)
        del self.worktrees[name]
        return f"Removed worktree '{name}'"

worktrees = WorktreeManager()
```

## 试一试

```bash
python agents/s18_worktree.py
```

1. `创建 worktree "auth-refactor" 绑定 task 1`
2. `在 worktree "auth-refactor" 中运行 git status`
3. `移除 worktree 并完成绑定的任务`

## 本章小结

- Worktree 隔离:每个任务独立目录
- 任务绑定:worktree 创建时自动推进任务状态
- 事件流:每个生命周期步骤记录到 events.jsonl
- 崩溃恢复:从 .tasks/ 和 .worktrees/index.json 重建现场
