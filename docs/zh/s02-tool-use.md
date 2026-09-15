# 第 2 章:工具与文件 -- 给 Agent 加一个工具只需要加一行

`s01 > [ s02 ] s03 > s04 > s05 > s06 | s07 > s08 > s09 > s10 > s11 > s12`

> *"加一个工具,只加一个 handler"* -- 循环不用动,新工具注册进 dispatch map 就行。
>
> **Harness 层**: 工具分发 -- 扩展模型能触达的边界。

---

## 本章导读

### 读完这一章,你能做到什么

1. 理解为什么只有 `bash` 工具是不够的。
2. 掌握 dispatch map 模式:加工具 = 加 handler + 加 schema,循环不变。
3. 实现路径沙箱,防止 Agent 逃逸工作目录。
4. 从 1 个工具扩展到 4 个工具:bash、read_file、write_file、edit_file。

### 你需要先具备什么

| 需要 | 程度 |
| --- | --- |
| 上一章 | 读过第 1 章,理解 Agent Loop |
| Python | 字典、函数定义、路径操作 |

### 术语速查

| 术语 | 一句话解释 |
| --- | --- |
| **Dispatch map** | 工具名到处理函数的字典映射,替代 if/elif 链 |
| **safe_path()** | 路径沙箱函数,确保文件操作不逃逸工作目录 |
| **Tool schema** | 工具的 JSON Schema 描述,告诉模型工具接受什么参数 |

---

## 问题

只有 `bash` 时,所有操作都走 shell。`cat` 截断不可预测,`sed` 遇到特殊字符就崩,每次 bash 调用都是不受约束的安全面。

关键洞察:**加工具不需要改循环。** 只需要加 handler + 加 schema。

---

## 解决方案

```
+--------+      +-------+      +------------------+
|  User  | ---> |  LLM  | ---> | Tool Dispatch    |
| prompt |      |       |      | {                |
+--------+      +---+---+      |   bash: run_bash |
                    ^           |   read: run_read |
                    |           |   write: run_wr  |
                    +-----------+   edit: run_edit |
                    tool_result | }                |
                                +------------------+
```

dispatch map 是一个字典:`{tool_name: handler_function}`。一个查找替代任何 if/elif 链。

---

## 工作原理

### 1. 路径沙箱

```python
from pathlib import Path

WORKDIR = Path.cwd()

def safe_path(p: str) -> Path:
    """确保路径在工作目录内"""
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path
```

### 2. 四个工具的 handler

```python
def run_bash(command: str) -> str:
    import subprocess
    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
    return result.stdout + result.stderr

def run_read(path: str, limit: int = None) -> str:
    text = safe_path(path).read_text(encoding="utf-8")
    lines = text.splitlines()
    if limit and limit < len(lines):
        lines = lines[:limit]
    return "\n".join(lines)[:50000]

def run_write(path: str, content: str) -> str:
    p = safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Written {len(content)} bytes to {path}"

def run_edit(path: str, old_text: str, new_text: str) -> str:
    p = safe_path(path)
    text = p.read_text(encoding="utf-8")
    if old_text not in text:
        return f"Error: old_text not found in {path}"
    new = text.replace(old_text, new_text, 1)
    p.write_text(new, encoding="utf-8")
    return f"Edited {path}"
```

### 3. Dispatch map

```python
TOOL_HANDLERS = {
    "bash":       lambda **kw: run_bash(kw["command"]),
    "read_file":  lambda **kw: run_read(kw["path"], kw.get("limit")),
    "write_file": lambda **kw: run_write(kw["path"], kw["content"]),
    "edit_file":  lambda **kw: run_edit(kw["path"], kw["old_text"], kw["new_text"]),
}
```

### 4. 循环中按名称查找

```python
for block in response.content:
    if block.type == "tool_use":
        handler = TOOL_HANDLERS.get(block.name)
        output = handler(**block.input) if handler else f"Unknown tool: {block.name}"
        results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
```

**加工具 = 加 handler + 加 schema。循环永远不变。**

---

## 相对 s01 的变更

| 组件 | 之前 (s01) | 之后 (s02) |
| --- | --- | --- |
| Tools | 1 (仅 bash) | 4 (bash, read, write, edit) |
| Dispatch | 硬编码 bash 调用 | `TOOL_HANDLERS` 字典 |
| 路径安全 | 无 | `safe_path()` 沙箱 |
| Agent loop | 不变 | 不变 |

---

## 试一试

```bash
cd agent-tutorial
python agents/s02_tool_use.py
```

1. `读取 requirements.txt 的前 10 行`
2. `创建一个 greet.py 文件,里面有一个 greet(name) 函数`
3. `编辑 greet.py,给函数加上 docstring`
4. `读取 greet.py 确认编辑生效了`

---

## 本章小结

- dispatch map 模式让加工具变得极其简单
- `safe_path()` 在工具层做路径沙箱,比在 shell 层拦截更可靠
- 循环体与 s01 完全一致 -- 所有扩展都在循环外围
