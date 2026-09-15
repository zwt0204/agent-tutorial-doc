# 第 3 章:权限系统 -- 生产级的 Agent 安全策略

`s01 > s02 > [ s03 ] s04 > s05 > s06 | s07 > s08 > s09 > s10 > s11 > s12`

> *"Agent 能做的事,必须是你允许它做的事"* -- 四态权限决定 + 审计日志。
>
> **Harness 层**: 权限 -- 给模型的每一步行动划定信任边界。

---

## 本章导读

### 读完这一章,你能做到什么

1. 理解为什么 Agent 需要权限系统(不只是"能跑就行")。
2. 掌握四态权限模型:ALLOW / ASK / DENY / ASK_ONCE。
3. 实现工具执行拦截器,在循环和 handler 之间插入权限检查。
4. 实现审计日志,记录每一次工具调用的决策过程。

### 你需要先具备什么

| 需要 | 程度 |
| --- | --- |
| 上一章 | 理解 dispatch map 和工具执行流程 |
| Python | 字典、枚举、函数 |

### 术语速查

| 术语 | 一句话解释 |
| --- | --- |
| **四态权限** | ALLOW(自动允许) / ASK(需要审批) / DENY(拒绝) / ASK_ONCE(首次审批) |
| **审计日志** | 记录每次工具调用的工具名、参数、权限决策、执行结果 |
| **fail-closed** | 出错时选择拒绝而不是放行 |

---

## 问题

s02 的 Agent 能执行任何 bash 命令 -- `rm -rf /` 也可以。生产环境中,这是不可接受的。我们需要:
- 读文件:自动允许
- 写文件:首次需要审批
- bash 命令:每次都需要审批
- 危险操作:直接拒绝

---

## 解决方案:四态权限模型

```
权限检查流程:

工具调用请求
    │
    v
┌─────────────┐
│ 查找权限规则 │
└──────┬──────┘
       │
  ┌────┴────┐
  │  匹配?  │
  └────┬────┘
       │
  ┌────┴────────────────────────────┐
  │                                 │
  v                                 v
ALLOW ──→ 直接执行            ASK_ONCE ──→ 已授权过? ──→ 是 ──→ 直接执行
                                        │
                                        否
                                        │
                                        v
                                  ASK ──→ 用户审批 ──→ 通过 ──→ 执行 + 记录
                                        │
                                        拒绝
                                        │
                                        v
                                   DENY ──→ 返回 "Permission denied"
```

---

## 工作原理

### 1. 权限策略

```python
from enum import Enum

class Permission(Enum):
    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"
    ASK_ONCE = "ask_once"

class PermissionPolicy:
    def __init__(self):
        self.rules = {}
        self.granted = set()

    def check(self, tool_name: str, params: dict) -> Permission:
        if tool_name in self.rules:
            perm = self.rules[tool_name]
            if perm == Permission.ASK_ONCE and tool_name in self.granted:
                return Permission.ALLOW
            return perm
        return Permission.ALLOW

    def grant_once(self, tool_name: str):
        self.granted.add(tool_name)

policy = PermissionPolicy()
policy.rules["bash"] = Permission.ASK
policy.rules["write_file"] = Permission.ASK_ONCE
policy.rules["read_file"] = Permission.ALLOW
policy.rules["edit_file"] = Permission.ASK_ONCE
```

### 2. 工具执行拦截器

```python
def execute_tool(name: str, params: dict) -> str:
    perm = policy.check(name, params)

    if perm == Permission.DENY:
        return "Error: Permission denied"

    if perm == Permission.ASK:
        approved = input(f"  Allow {name}({params})? [y/N]: ").lower() == "y"
        if not approved:
            return "Error: User denied"

    if perm == Permission.ASK_ONCE and name not in policy.granted:
        approved = input(f"  Allow {name}({params})? (once) [y/N]: ").lower() == "y"
        if not approved:
            return "Error: User denied"
        policy.grant_once(name)

    handler = TOOL_HANDLERS.get(name)
    if not handler:
        return f"Error: Unknown tool {name}"

    try:
        return handler(**params)
    except Exception as e:
        return f"Error: {str(e)}"
```

### 3. 审计日志

```python
import datetime

AUDIT_LOG = []

def audit(tool_name: str, params: dict, result: str, permission: Permission):
    AUDIT_LOG.append({
        "timestamp": datetime.datetime.now().isoformat(),
        "tool": tool_name,
        "params": str(params)[:200],
        "permission": permission.value,
        "result_preview": str(result)[:200],
    })
```

---

## 集成到 Agent Loop

```python
for block in response.content:
    if block.type == "tool_use":
        perm = policy.check(block.name, block.input)
        audit(block.name, block.input, "", perm)

        output = execute_tool(block.name, block.input)
        audit(block.name, block.input, output, perm)

        results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
```

权限检查插在循环和 handler 之间。循环本身不变。

---

## 相对 s02 的变更

| 组件 | 之前 (s02) | 之后 (s03) |
| --- | --- | --- |
| 工具执行 | 直接调用 handler | 经过权限检查再调用 |
| 权限 | 无 | 四态权限模型 |
| 审计 | 无 | 每次调用记录日志 |
| Agent loop | 不变 | 不变(权限在循环外) |

---

## 试一试

```bash
cd agent-tutorial
python agents/s03_permission.py
```

1. `读取 README.md`(应该自动执行,不需要审批)
2. `创建一个 test.txt 文件`(首次写入需要审批)
3. `再次写入 test.txt`(ASK_ONCE 第二次自动允许)
4. `执行 rm -rf /`(应该被拒绝)

---

## 本章小结

- 四态权限:ALLOW / ASK / DENY / ASK_ONCE
- 权限检查在循环和 handler 之间,循环不变
- ASK_ONCE 是实用折中:首次审批,后续自动
- 审计日志记录决策过程,用于事后审计
- fail-closed:异常当作拒绝处理
