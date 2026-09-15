# 第 4 章:Hook 系统 -- 用生命周期钩子解耦 Agent 行为

`s01 > s02 > s03 > [ s04 ] s05 > s06 | s07 > s08 > s09 > s10 > s11 > s12`

> *"在 Agent 的四个关键时刻,插入你自己的逻辑"* -- 四个生命周期点,零侵入扩展。
>
> **Harness 层**: 生命周期 -- 让外部代码在特定时刻介入。

---

## 本章导读

### 读完这一章,你能做到什么

1. 理解为什么权限检查还不够 -- 还需要"在特定时刻做特定事"的能力。
2. 掌握四个生命周期钩子:UserPromptSubmit、PreToolUse、PostToolUse、Stop。
3. 实现 HookManager,支持注册、触发、链式调用。
4. 用 Hook 实现日志记录、状态保存、输入验证等横切关注点。

### 你需要先具备什么

| 需要 | 程度 |
| --- | --- |
| 上一章 | 理解权限拦截器的位置 |
| Python | 函数、列表、字典 |

### 术语速查

| 术语 | 一句话解释 |
| --- | --- |
| **Hook** | 在特定生命周期点插入的回调函数 |
| **生命周期** | Agent 运行过程中的关键时刻:提交 prompt、执行工具前后、停止时 |
| **横切关注点** | 贯穿多个功能的通用逻辑:日志、审计、状态保存 |

---

## 问题

权限检查是静态的 -- 规则写死在 policy 里。但真实场景需要动态行为:

- 用户提交 prompt 前:验证格式、过滤敏感词
- 工具执行前:记录日志、检查副作用
- 工具执行后:更新统计、触发通知
- Agent 停止前:保存状态、生成报告

这些逻辑不能硬编码在循环里。需要一种**零侵入**的扩展机制。

---

## 解决方案:四个生命周期钩子

```
User prompt
    │
    v
[UserPromptSubmit]  ← 用户提交 prompt 前
    │
    v
┌───────────────────────────────────────┐
│  while True:                          │
│    LLM response                       │
│        │                              │
│        v                              │
│    [PreToolUse]  ← 工具执行前         │
│        │                              │
│        v                              │
│    execute tool                       │
│        │                              │
│        v                              │
│    [PostToolUse] ← 工具执行后         │
│        │                              │
│        v                              │
│    append result                      │
└───────────────────────────────────────┘
    │
    v
[Stop]  ← Agent 停止前
```

---

## 工作原理

### 1. HookManager

```python
from typing import Callable

class HookManager:
    def __init__(self):
        self.hooks = {
            "UserPromptSubmit": [],
            "PreToolUse": [],
            "PostToolUse": [],
            "Stop": [],
        }

    def register(self, event: str, fn: Callable):
        if event in self.hooks:
            self.hooks[event].append(fn)

    def fire(self, event: str, data: dict) -> dict:
        for fn in self.hooks[event]:
            result = fn(data)
            if result is False:
                return None
            if isinstance(result, dict):
                data.update(result)
        return data

hooks = HookManager()
```

### 2. 示例钩子

```python
def validate_prompt(data: dict):
    if len(data.get("prompt", "")) > 10000:
        print("Warning: Prompt too long, truncating...")
        data["prompt"] = data["prompt"][:10000]
    return data

def log_tool_use(data: dict):
    print(f"[LOG] {data['tool_name']} called with {data['params']}")
    return data

def save_state(data: dict):
    import json
    with open("state.json", "w") as f:
        json.dump(data.get("messages", []), f)
    return data

hooks.register("UserPromptSubmit", validate_prompt)
hooks.register("PreToolUse", log_tool_use)
hooks.register("Stop", save_state)
```

### 3. 集成到 Agent Loop

```python
def agent_loop(query: str):
    messages = [{"role": "user", "content": query}]

    while True:
        hook_data = hooks.fire("UserPromptSubmit", {"prompt": query, "messages": messages})
        if hook_data is None:
            return "Blocked by hook"

        response = client.messages.create(
            model=MODEL, system=SYSTEM, messages=messages,
            tools=TOOLS, max_tokens=8000,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            hooks.fire("Stop", {"messages": messages})
            return

        results = []
        for block in response.content:
            if block.type == "tool_use":
                hooks.fire("PreToolUse", {"tool_name": block.name, "params": block.input})
                output = execute_tool(block.name, block.input)
                hooks.fire("PostToolUse", {"tool_name": block.name, "params": block.input, "result": output})
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
        messages.append({"role": "user", "content": results})
```

钩子注册在循环外面,触发在循环里面。循环结构不变,但行为可无限扩展。

---

## 相对 s03 的变更

| 组件 | 之前 (s03) | 之后 (s04) |
| --- | --- | --- |
| 横切逻辑 | 硬编码在循环中 | 注册为 Hook,按需触发 |
| 扩展方式 | 改循环代码 | 注册回调函数 |
| 生命周期点 | 无 | 4 个(Submit/Pre/Post/Stop) |
| Agent loop | 不变 | 不变(钩子在循环内触发) |

---

## 试一试

```bash
cd agent-tutorial
python agents/s04_hooks.py
```

1. `列出当前目录`(观察 PreToolUse 日志输出)
2. `读取 README.md`(观察 PostToolUse 日志输出)
3. 按 Ctrl+C 停止(观察 Stop 钩子保存状态)
4. 检查 `state.json` 文件是否生成

---

## 本章小结

- 四个生命周期钩子:UserPromptSubmit / PreToolUse / PostToolUse / Stop
- Hook 让横切关注点(日志、审计、状态保存)与核心循环解耦
- 注册在循环外,触发在循环内
- 返回 False 可以阻止后续执行(用于安全拦截)
