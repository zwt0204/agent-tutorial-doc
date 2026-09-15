# 第 16 章:协议审批 -- 结构化的协作流程

`s01 > ... > s15 > [ s16 ] > s17`

> *"多 Agent 协作需要明确的规则"* -- 结构化交接、审批闭环。
>
> **Harness 层**: 协议 -- 让 Agent 之间的协作可预测、可审计。

---

## 问题

多 Agent 协作需要明确的规则:谁负责什么、如何交接、如何处理冲突。没有协议,Agent 之间会互相踩脚。

## 解决方案

```python
class ProtocolManager:
    def __init__(self):
        self.protocols = {}

    def define(self, name: str, steps: list):
        """定义协议步骤:每个步骤有 assignee 和 description"""
        self.protocols[name] = {"steps": steps, "current_step": 0, "status": "pending"}

    def execute_step(self, protocol_name: str, agent: str) -> str:
        protocol = self.protocols[protocol_name]
        if protocol["current_step"] >= len(protocol["steps"]):
            return "Protocol completed"

        step = protocol["steps"][protocol["current_step"]]
        if step["assignee"] != agent:
            return f"Step assigned to {step['assignee']}, not {agent}"

        protocol["current_step"] += 1
        if protocol["current_step"] >= len(protocol["steps"]):
            protocol["status"] = "completed"
        return f"Step {protocol['current_step']}: {step['description']} completed"

    def get_status(self) -> str:
        lines = ["Protocols:"]
        for name, p in self.protocols.items():
            progress = f"{p['current_step']}/{len(p['steps'])}"
            lines.append(f"- {name}: {p['status']} ({progress})")
        return "\n".join(lines)

protocols = ProtocolManager()
```

## 试一试

```bash
python agents/s16_protocols.py
```

1. `定义一个代码审查协议:提交 -> 审查 -> 合并`
2. `让 alice 执行审查步骤`
3. `查看协议状态`

## 本章小结

- 协议定义清晰的协作步骤
- 步骤绑定到具体 Agent
- 状态追踪防止遗漏
