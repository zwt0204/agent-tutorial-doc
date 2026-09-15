# 第 17 章:自治 Agent -- 自己找活干

`s01 > ... > s16 > [ s17 ]`

> *"队友自己看看板,有活就认领"* -- 不需要领导逐个分配,自组织。
>
> **Harness 层**: 自治 -- 模型自己找活干,无需指派。

---

## 问题

s15-s16 中,Agent 只在被明确指派时才动。Lead 得给每个队友写 prompt,任务看板上 10 个未认领的任务得手动分配。这扩展不了。

## 解决方案

```
Teammate lifecycle with idle cycle:

+-------+
| spawn |
+---+---+
    |
    v
+-------+   tool_use     +-------+
| WORK  | <------------- |  LLM  |
+---+---+                +-------+
    |
    | stop_reason != tool_use (or idle tool called)
    v
+--------+
|  IDLE  |  poll every 5s for up to 60s
+---+----+
    |
    +---> check inbox --> message? ----------> WORK
    |
    +---> scan .tasks/ --> unclaimed? -------> claim -> WORK
    |
    +---> 60s timeout ----------------------> SHUTDOWN
```

## 工作原理

### 1. 空闲轮询

```python
def idle_poll(self, name: str, messages: list) -> bool:
    for _ in range(12):  # 60s / 5s = 12
        time.sleep(5)
        inbox = bus.read_inbox(name)
        if inbox:
            messages.append({"role": "user", "content": f"<inbox>{inbox}</inbox>"})
            return True
        unclaimed = tasks.get_ready_tasks()
        if unclaimed:
            task = unclaimed[0]
            tasks.update(task["id"], owner=name, status="in_progress")
            messages.append({"role": "user", "content": f"<auto-claimed>Task #{task['id']}: {task['subject']}</auto-claimed>"})
            return True
    return False
```

### 2. 身份重注入

上下文压缩后 Agent 可能忘了自己是谁:

```python
if len(messages) <= 3:
    messages.insert(0, {"role": "user",
        "content": f"<identity>You are '{name}', role: {role}. Continue your work.</identity>"})
```

## 试一试

```bash
python agents/s17_autonomous.py
```

1. `创建 3 个任务,然后 spawn alice 和 bob,观察自动认领`
2. `Spawn 一个 coder 队友,让它自己从任务板找活`

## 本章小结

- 空闲轮询:检查收件箱 + 扫描任务板
- 自动认领:pending 且无 owner 的任务
- 身份重注入:压缩后恢复 Agent 身份
- 超时关机:60 秒无活自动退出
