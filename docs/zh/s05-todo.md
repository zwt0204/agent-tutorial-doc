# 第 5 章:会话计划 -- 用 TODO 防止长任务漂移

`s01 > s02 > s03 > s04 > [ s05 ] > s06 | s07 > s08 > s09 > s10 > s11 > s12`

> *"长任务需要锚点,否则 Agent 会忘记自己在做什么"*
>
> **Harness 层**: 规划 -- 让目标持久化在上下文中。

---

## 本章导读

### 读完这一章,你能做到什么

1. 理解为什么长对话中 Agent 会"忘记"最初目标。
2. 实现 TodoManager,支持添加、更新、渲染任务列表。
3. 将 TODO 注入系统提示,让 Agent 始终"看到"自己的计划。
4. 用 TODO 状态校验防止计划陈旧。

### 你需要先具备什么

| 需要 | 程度 |
| --- | --- |
| 上一章 | 理解 Hook 系统 |
| Python | 列表、字典、字符串格式化 |

### 术语速查

| 术语 | 一句话解释 |
| --- | --- |
| **TODO** | 持久化的任务列表,注入系统提示让 Agent 始终可见 |
| **任务漂移** | 长对话中 Agent 逐渐偏离最初目标的现象 |
| **状态校验** | 检查 TODO 是否与实际工作匹配,防止计划陈旧 |

---

## 问题

长对话中,Messages 数组越来越长。Agent 最初说"我要重构认证模块",但读了 20 个文件、跑了 10 条命令后,它可能已经忘了自己在做什么,开始做不相关的事。

---

## 解决方案

把计划以 TODO 格式注入系统提示:

```
当前计划:
- [x] 读取现有认证代码
- [ ] 重构为 JWT 模式
- [ ] 更新测试
- [ ] 更新文档
```

Agent 每次调用模型时都能"看到"自己的计划,不会偏离。

---

## 工作原理

### 1. TodoManager

```python
class TodoManager:
    def __init__(self):
        self.items = []

    def add(self, text: str, status: str = "pending"):
        self.items.append({"text": text, "status": status})

    def update(self, index: int, status: str):
        if 0 <= index < len(self.items):
            self.items[index]["status"] = status

    def render(self) -> str:
        lines = ["当前计划:"]
        for i, item in enumerate(self.items):
            mark = "x" if item["status"] == "done" else " "
            lines.append(f"- [{mark}] {item['text']}")
        return "\n".join(lines)

TODO = TodoManager()
```

### 2. 注入系统提示

```python
def get_system_prompt():
    base = "You are a helpful coding assistant."
    todo_state = TODO.render()
    if todo_state.strip() != "当前计划:":
        return f"{base}\n\n{todo_state}"
    return base
```

### 3. Agent 更新 TODO 的工具

```python
@tool("todo_add")
def todo_add(text: str) -> str:
    TODO.add(text)
    return f"Added: {text}"

@tool("todo_done")
def todo_done(index: int) -> str:
    TODO.update(index, "done")
    return f"Marked task {index} as done"
```

---

## 相对 s04 的变更

| 组件 | 之前 (s04) | 之后 (s05) |
| --- | --- | --- |
| 目标追踪 | 无(靠消息历史) | TODO 注入系统提示 |
| 工具 | 4 | 6 (+todo_add, +todo_done) |
| Agent loop | 不变 | 不变(TODO 在系统提示中) |

---

## 试一试

```bash
cd agent-tutorial
python agents/s05_todo.py
```

1. `帮我重构这个项目的认证模块`
2. 观察 Agent 自动创建 TODO 并按顺序执行
3. 输入 `/todo` 查看当前计划状态

---

## 本章小结

- TODO 注入系统提示,防止长任务漂移
- Agent 可以通过工具自主更新计划
- 简单但有效:一个列表解决 80% 的规划问题
