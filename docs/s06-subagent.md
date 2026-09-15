# 第 6 章:子 Agent -- 复杂任务的分身协作

`s01 > s02 > s03 > s04 > s05 > [ s06 ] | s07 > s08 > s09 > s10 > s11 > s12`

> *"大任务拆小,每个小任务干净的上下文"* -- SubAgent 用独立 messages[], 不污染主对话。
>
> **Harness 层**: 上下文隔离 -- 守护模型的思维清晰度。

---

## 本章导读

### 读完这一章,你能做到什么

1. 理解为什么 Agent 工作越久,上下文越臃肿。
2. 实现 SubAgent:独立消息列表、共享工具、最终只返回摘要。
3. 禁止递归委派,防止 Agent 无限生成子 Agent。
4. 限制子 Agent 轮数,防止失控。

### 你需要先具备什么

| 需要 | 程度 |
| --- | --- |
| 上一章 | 理解 TODO 和工具系统 |
| Python | 函数、列表、循环 |

### 术语速查

| 术语 | 一句话解释 |
| --- | --- |
| **SubAgent** | 独立运行的子 Agent,有自己的消息历史,任务完成后销毁 |
| **上下文隔离** | 子 Agent 的消息历史与父 Agent 完全分离 |
| **摘要返回** | 子 Agent 只返回最终文本摘要,不返回完整历史 |

---

## 问题

Agent 工作越久,Messages 数组越臃肿。每次读文件、跑命令的输出都永久留在上下文里。"这个项目用什么测试框架?" 可能要读 5 个文件,但父 Agent 只需要一个词: "pytest。"

---

## 解决方案

```
Parent Agent                     SubAgent
+------------------+             +------------------+
| messages=[...]   |             | messages=[]      | <-- fresh
|                  |  dispatch   |                  |
| tool: task       | ----------> | while tool_use:  |
|   prompt="..."   |             |   call tools     |
|                  |  summary    |   append results |
|   result = "..." | <---------- | return last text |
+------------------+             +------------------+

Parent context stays clean. SubAgent context is discarded.
```

---

## 工作原理

```python
def run_subagent(prompt: str, tools: list, max_turns: int = 10) -> str:
    """运行子 Agent,返回最终摘要"""
    sub_messages = [{"role": "user", "content": prompt}]
    system = "You are a sub-agent. Complete the task concisely. Return only the result."

    for _ in range(max_turns):
        response = client.messages.create(
            model=MODEL, system=system, messages=sub_messages,
            tools=tools, max_tokens=4000,
        )
        sub_messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            break

        results = []
        for block in response.content:
            if block.type == "tool_use":
                handler = TOOL_HANDLERS.get(block.name)
                output = handler(**block.input) if handler else f"Unknown: {block.name}"
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(output)[:50000]})
        sub_messages.append({"role": "user", "content": results})

    # 只返回最终文本摘要
    return "".join(b.text for b in response.content if hasattr(b, "text")) or "(no summary)"
```

### 父 Agent 的 task 工具

```python
PARENT_TOOLS = BASE_TOOLS + [
    {"name": "task",
     "description": "Spawn a subagent with fresh context for isolated work.",
     "input_schema": {
         "type": "object",
         "properties": {"prompt": {"type": "string"}},
         "required": ["prompt"],
     }},
]

TOOL_HANDLERS["task"] = lambda **kw: run_subagent(kw["prompt"], BASE_TOOLS)
```

SubAgent 可能跑了 10+ 次工具调用,但整个消息历史直接丢弃。父 Agent 收到的只是一段摘要。

---

## 相对 s05 的变更

| 组件 | 之前 (s05) | 之后 (s06) |
| --- | --- | --- |
| 上下文 | 单一共享 | 父 + 子隔离 |
| SubAgent | 无 | `run_subagent()` |
| 递归保护 | 无 | 子 Agent 没有 `task` 工具 |
| 返回值 | 不适用 | 仅摘要文本 |

---

## 试一试

```bash
cd agent-tutorial
python agents/s06_subagent.py
```

1. `用子任务查找这个项目用什么测试框架`
2. `委派:读取所有 .py 文件并总结每个文件的功能`
3. `用子任务创建一个新模块,然后从这里验证`

---

## 本章小结

- SubAgent 用独立消息列表,完成后丢弃
- 只返回摘要,父 Agent 上下文保持干净
- 禁止递归:子 Agent 没有 `task` 工具
- 限制轮数防止失控
