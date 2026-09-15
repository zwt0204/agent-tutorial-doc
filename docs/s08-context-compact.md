# 第 8 章:上下文压缩 -- 干净的记忆,无限的会话

`s01 > s02 > s03 > s04 > s05 > s06 | s07 > [ s08 ] > s09 > s10 > s11 > s12`

> *"上下文总会满,要有办法腾地方"* -- 三层压缩策略,换来无限会话。
>
> **Harness 层**: 压缩 -- 干净的记忆,无限的会话。

---

## 本章导读

### 读完这一章,你能做到什么

1. 理解为什么上下文窗口是有限的,以及不压缩的后果。
2. 掌握三层压缩策略:micro_compact / auto_compact / manual compact。
3. 实现 micro_compact:静默替换旧 tool_result。
4. 实现 auto_compact:token 超阈值时自动摘要。

### 你需要先具备什么

| 需要 | 程度 |
| --- | --- |
| 上一章 | 理解 Skill 加载和工具系统 |
| Python | 列表、字典、JSON |

### 术语速查

| 术语 | 一句话解释 |
| --- | --- |
| **micro_compact** | 每次 LLM 调用前,将旧 tool_result 替换为占位符 |
| **auto_compact** | token 超过阈值时,保存完整对话到磁盘,用 LLM 摘要替换 |
| **transcript** | 完整对话历史,保存在 `.transcripts/` 目录用于恢复 |

---

## 问题

上下文窗口是有限的。读一个 1000 行的文件就吃掉 ~4000 token;读 30 个文件、跑 20 条命令,轻松突破 100k token。不压缩,Agent 根本没法在大项目里干活。

---

## 解决方案:三层压缩

```
Every turn:
+------------------+
| Tool call result |
+------------------+
        |
        v
[Layer 1: micro_compact]        (silent, every turn)
  Replace tool_result > 3 turns old
  with "[Previous: used {tool_name}]"
        |
        v
[Check: tokens > 50000?]
   |               |
   no              yes
   |               |
   v               v
continue    [Layer 2: auto_compact]
              Save transcript to .transcripts/
              LLM summarizes conversation.
              Replace all messages with [summary].
                    |
                    v
            [Layer 3: compact tool]
              Model calls compact explicitly.
              Same summarization as auto_compact.
```

---

## 工作原理

### 1. micro_compact -- 静默替换

```python
KEEP_RECENT = 3

def micro_compact(messages: list) -> list:
    tool_results = []
    for i, msg in enumerate(messages):
        if msg["role"] == "user" and isinstance(msg.get("content"), list):
            for j, part in enumerate(msg["content"]):
                if isinstance(part, dict) and part.get("type") == "tool_result":
                    tool_results.append((i, j, part))

    if len(tool_results) <= KEEP_RECENT:
        return messages

    for _, _, part in tool_results[:-KEEP_RECENT]:
        if len(part.get("content", "")) > 100:
            part["content"] = f"[Previous result truncated]"

    return messages
```

### 2. auto_compact -- LLM 摘要

```python
def auto_compact(messages: list) -> list:
    transcript_dir = Path(".transcripts")
    transcript_dir.mkdir(exist_ok=True)

    # 保存完整历史
    with open(transcript_dir / f"transcript_{int(time.time())}.jsonl", "w") as f:
        for msg in messages:
            f.write(json.dumps(msg, default=str) + "\n")

    # LLM 摘要
    response = client.messages.create(
        model=MODEL,
        messages=[{"role": "user", "content":
            "Summarize this conversation for continuity. Keep key decisions and context.\n\n"
            + json.dumps(messages, default=str)[:80000]}],
        max_tokens=2000,
    )
    return [{"role": "user", "content": f"[Compressed]\n\n{response.content[0].text}"}]
```

### 3. 集成到循环

```python
THRESHOLD = 50000

def agent_loop(query: str):
    messages = [{"role": "user", "content": query}]
    while True:
        micro_compact(messages)
        if estimate_tokens(messages) > THRESHOLD:
            messages[:] = auto_compact(messages)

        response = client.messages.create(...)
        # ... 正常循环 ...
```

---

## 相对 s07 的变更

| 组件 | 之前 (s07) | 之后 (s08) |
| --- | --- | --- |
| 上下文管理 | 无 | 三层压缩 |
| 会话长度 | 受窗口限制 | 理论上无限 |
| 历史恢复 | 无 | transcript 保存到磁盘 |

---

## 试一试

```bash
cd agent-tutorial
python agents/s08_context_compact.py
```

1. `逐个读取 agents/ 目录下的所有 Python 文件`(观察 micro_compact 替换旧结果)
2. `继续读取文件直到压缩自动触发`
3. `使用 compact 工具手动压缩对话`

---

## 本章小结

- micro_compact:静默替换旧结果,零感知
- auto_compact:token 超阈值时 LLM 摘要
- 完整历史通过 transcript 保存在磁盘
- 信息没有真正丢失,只是移出了活跃上下文
