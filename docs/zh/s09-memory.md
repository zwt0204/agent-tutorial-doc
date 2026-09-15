# 第 9 章:文件记忆 -- 跨会话的持久化

`s01 > s02 > s03 > s04 > s05 > s06 | s07 > s08 > [ s09 ] > s10 > s11 > s12`

> *"压缩后 Agent 可能忘了自己是谁,记忆解决这个问题"*
>
> **Harness 层**: 记忆 -- 让 Agent 跨会话保持一致性。

---

## 本章导读

### 读完这一章,你能做到什么

1. 理解为什么上下文压缩后 Agent 会"失忆"。
2. 实现 MemoryManager:remember / recall / forget。
3. 设计记忆索引,支持基于关键词的检索。
4. 将记忆与 Skill 系统结合,形成"长期知识"。

### 你需要先具备什么

| 需要 | 程度 |
| --- | --- |
| 上一章 | 理解上下文压缩和 transcript |
| Python | pathlib、JSON、字典 |

### 术语速查

| 术语 | 一句话解释 |
| --- | --- |
| **Memory** | 持久化到文件系统的知识条目,跨会话可检索 |
| **记忆索引** | `index.json` 文件,记录所有记忆的 key、摘要、标签 |
| **canonical history** | 压缩前保存的完整对话历史 |

---

## 问题

上下文压缩后,Agent 的消息历史被替换为摘要。之前做的决策、学到的项目结构、用户的偏好 -- 全部丢失。

---

## 解决方案

将关键信息持久化到文件系统:

```
memory/
  index.json           ← 记忆索引(元数据)
  auth-decision.md     ← "项目使用 JWT 认证"
  code-style.md        ← "用户偏好 4 空格缩进"
  project-structure.md ← "src/ 下有 5 个模块"
```

---

## 工作原理

```python
from pathlib import Path
import json

MEMORY_DIR = Path("./memory")

class MemoryManager:
    def __init__(self):
        MEMORY_DIR.mkdir(exist_ok=True)
        self.index_path = MEMORY_DIR / "index.json"
        self.index = self._load_index()

    def _load_index(self) -> dict:
        if self.index_path.exists():
            return json.loads(self.index_path.read_text(encoding="utf-8"))
        return {"entries": []}

    def _save_index(self):
        self.index_path.write_text(json.dumps(self.index, indent=2), encoding="utf-8")

    def remember(self, key: str, value: str, tags: list = None):
        entry = {"key": key, "value": value, "tags": tags or [],
                 "timestamp": datetime.datetime.now().isoformat()}
        self.index["entries"].append(entry)
        self._save_index()
        (MEMORY_DIR / f"{key}.md").write_text(value, encoding="utf-8")

    def recall(self, query: str) -> str:
        results = [e for e in self.index["entries"]
                   if query.lower() in e["key"].lower() or query.lower() in e["value"].lower()]
        if not results:
            return "No relevant memories found."
        lines = ["Relevant memories:"]
        for e in results[:5]:
            lines.append(f"- {e['key']}: {e['value'][:200]}")
        return "\n".join(lines)

    def forget(self, key: str):
        self.index["entries"] = [e for e in self.index["entries"] if e["key"] != key]
        self._save_index()
        p = MEMORY_DIR / f"{key}.md"
        if p.exists():
            p.unlink()

memory = MemoryManager()
```

---

## 相对 s08 的变更

| 组件 | 之前 (s08) | 之后 (s09) |
| --- | --- | --- |
| 记忆 | 无(压缩后丢失) | 文件系统持久化 |
| 跨会话 | 无 | 记忆索引可检索 |
| 工具 | 7 | 9 (+remember, +recall) |

---

## 试一试

```bash
cd agent-tutorial
python agents/s09_memory.py
```

1. `记住:这个项目使用 pytest 做测试`
2. `记住:用户偏好 4 空格缩进`
3. `回忆:这个项目用什么测试框架?`
4. 检查 `memory/` 目录下的文件

---

## 本章小结

- 记忆持久化到文件系统,压缩后不丢失
- 索引支持关键词检索
- remember / recall / forget 三个工具
