# 第 7 章:Skill 系统 -- 按需加载的知识库

`s01 > s02 > s03 > s04 > s05 > s06 > [ s07 ] | s08 > s09 > s10 > s11 > s12`

> *"先告诉 Agent 有什么,再让它自己拉取"* -- 扫描摘要,按需加载正文。
>
> **Harness 层**: 知识加载 -- 让 Agent 按需获取领域专长。

---

## 本章导读

### 读完这一章,你能做到什么

1. 理解为什么不能把所有知识塞进系统提示(会稀释注意力)。
2. 实现 SkillManager:扫描目录获取摘要,按名称加载完整内容。
3. 设计两步加载:先列清单,再按需拉取。

### 你需要先具备什么

| 需要 | 程度 |
| --- | --- |
| 上一章 | 理解子 Agent 和工具系统 |
| Python | pathlib、字符串处理 |

### 术语速查

| 术语 | 一句话解释 |
| --- | --- |
| **Skill** | Markdown 格式的领域知识文件,存放在 `skills/` 目录 |
| **两步加载** | 先扫描获取摘要列表,再按名称加载完整正文 |
| **注意力稀释** | 系统提示太长时,模型对每个部分的注意力下降 |

---

## 问题

系统提示不能塞太多内容。100 个 Skill 文件全部塞进去,模型的注意力被稀释,反而什么都做不好。

---

## 解决方案:两步加载

```
Agent 启动
    │
    v
扫描 skills/ 目录 → 获取摘要列表 ["skill1: 描述1", "skill2: 描述2", ...]
    │
    v
摘要注入系统提示(只占几百 token)
    │
    v
Agent 需要时调用 load_skill("skill1") → 加载完整内容
```

---

## 工作原理

```python
from pathlib import Path

SKILLS_DIR = Path("./skills")

class SkillManager:
    def __init__(self):
        self.skills = {}
        self._scan()

    def _scan(self):
        if not SKILLS_DIR.exists():
            return
        for f in SKILLS_DIR.glob("*.md"):
            content = f.read_text(encoding="utf-8")
            first_line = content.split("\n")[0]
            self.skills[f.stem] = {"summary": first_line, "path": f}

    def list_skills(self) -> str:
        if not self.skills:
            return "No skills available."
        lines = ["Available skills:"]
        for name, info in self.skills.items():
            lines.append(f"- {name}: {info['summary']}")
        return "\n".join(lines)

    def load(self, name: str) -> str:
        if name not in self.skills:
            return f"Skill '{name}' not found. Available: {list(self.skills.keys())}"
        return self.skills[name]["path"].read_text(encoding="utf-8")

skills = SkillManager()
```

---

## 相对 s06 的变更

| 组件 | 之前 (s06) | 之后 (s07) |
| --- | --- | --- |
| 知识 | 硬编码在系统提示 | 文件系统 + 按需加载 |
| 工具 | 5 (+task) | 7 (+list_skills, +load_skill) |
| Agent loop | 不变 | 不变 |

---

## 试一试

```bash
cd agent-tutorial
python agents/s07_skill_loading.py
```

1. `有哪些可用的 skill?`
2. `加载 python-style skill`
3. `根据 python-style skill 的规范,写一个函数`

---

## 本章小结

- 两步加载:先摘要后正文,避免注意力稀释
- Skill 存放在文件系统,易于维护
- Agent 自主决定何时加载什么知识
