# 第 10 章:动态上下文 -- 模块化的系统提示

`s01 > s02 > s03 > s04 > s05 > s06 | s07 > s08 > s09 > [ s10 ] > s11 > s12`

> *"系统提示不是一坨文本,而是多个 Provider 按顺序组装的"*
>
> **Harness 层**: 上下文组装 -- 按需生成运行态系统提示。

---

## 本章导读

### 读完这一章,你能做到什么

1. 理解为什么系统提示需要动态组装而不是静态写死。
2. 实现 DynamicPrompt:按优先级注册 Provider,运行时组装。
3. 将 workspace 信息、Skill 列表、Memory 内容注入系统提示。

### 你需要先具备什么

| 需要 | 程度 |
| --- | --- |
| 上一章 | 理解 Memory 和 Skill 系统 |
| Python | 函数、列表、排序 |

### 术语速查

| 术语 | 一句话解释 |
| --- | --- |
| **DynamicPrompt** | 按优先级组装系统提示的框架 |
| **Provider** | 生成系统提示某个片段的函数 |

---

## 问题

系统提示需要包含:基础指令、workspace 信息、可用 Skill 列表、相关 Memory。如果写死在一个字符串里,每次改动都要改代码。

---

## 解决方案

```python
class DynamicPrompt:
    def __init__(self):
        self.providers = []

    def register(self, name: str, fn, priority: int = 0):
        self.providers.append({"name": name, "fn": fn, "priority": priority})
        self.providers.sort(key=lambda x: x["priority"])

    def build(self, context: dict = None) -> str:
        parts = []
        for provider in self.providers:
            try:
                part = provider["fn"](context or {})
                if part:
                    parts.append(part)
            except Exception as e:
                parts.append(f"[{provider['name']} failed: {e}]")
        return "\n\n".join(parts)

dynamic_prompt = DynamicPrompt()

# 注册 Provider
dynamic_prompt.register("base", lambda ctx: "You are a helpful coding assistant.", 0)
dynamic_prompt.register("workspace", lambda ctx: f"Workspace: {list(WORKSPACE.glob('**/*.py'))[:10]}", 10)
dynamic_prompt.register("skills", lambda ctx: skills.list_skills(), 20)
dynamic_prompt.register("memory", lambda ctx: memory.recall(ctx.get("topic", "")), 30)
```

---

## 相对 s09 的变更

| 组件 | 之前 (s09) | 之后 (s10) |
| --- | --- | --- |
| 系统提示 | 静态字符串 | 动态组装 |
| 扩展方式 | 改代码 | 注册新 Provider |
| 上下文来源 | 单一 | 多源聚合 |

---

## 试一试

```bash
cd agent-tutorial
python agents/s10_dynamic_prompt.py
```

1. `这个项目有哪些 Python 文件?`
2. `根据项目的代码风格规范,写一个函数`

---

## 本章小结

- DynamicPrompt 按优先级组装系统提示
- Provider 模式让上下文来源可插拔
- 运行时按需生成,避免复制循环逻辑
