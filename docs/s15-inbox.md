# 第 15 章:Inbox 机制 -- 异步通信

`s01 > ... > s14 > [ s15 ] > s16 > s17`

> *"队友之间需要通信,但不想阻塞彼此"* -- JSONL 收件箱。
>
> **Harness 层**: 消息传递 -- 多 Agent 之间的异步通信通道。

---

## 问题

多个 Agent 需要通信:Lead 分配任务、队友汇报进度、广播系统事件。但不想阻塞彼此的执行。

## 解决方案

```
.team/
  inbox/
    alice.jsonl   ← append-only, drain-on-read
    bob.jsonl
    lead.jsonl

send("alice", "bob", "Task assigned")  → bob.jsonl 追加一行
read_inbox("alice") → 读取全部并清空
```

## 工作原理

```python
from pathlib import Path
import json

INBOX_DIR = Path("./inbox")

class MessageBus:
    def __init__(self):
        INBOX_DIR.mkdir(exist_ok=True)

    def send(self, sender: str, to: str, content: str, msg_type: str = "message"):
        msg = {"type": msg_type, "from": sender, "content": content,
               "timestamp": datetime.datetime.now().isoformat()}
        with open(INBOX_DIR / f"{to}.jsonl", "a") as f:
            f.write(json.dumps(msg) + "\n")

    def read_inbox(self, name: str) -> list:
        path = INBOX_DIR / f"{name}.jsonl"
        if not path.exists():
            return []
        msgs = [json.loads(line) for line in path.read_text().strip().split("\n") if line]
        path.write_text("", encoding="utf-8")
        return msgs

    def broadcast(self, sender: str, content: str):
        for f in INBOX_DIR.glob("*.jsonl"):
            if f.stem != sender:
                self.send(sender, f.stem, content, "broadcast")

bus = MessageBus()
```

## 试一试

```bash
python agents/s15_inbox.py
```

1. `给 alice 发送消息:"任务已分配"`
2. `广播:"项目构建完成"`
3. `查看 lead 的收件箱`

## 本章小结

- JSONL 收件箱:append-only,drain-on-read
- send / read_inbox / broadcast 三个工具
- 异步通信不阻塞执行
