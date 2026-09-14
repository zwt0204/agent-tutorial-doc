# AI Agent 工程实战：从零构建生产级 Agent Harness

> 融合 [learn-agent](https://github.com/ryzqi/learn-agent) 与 [learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) 两大教程精华，打造一套完整的 Agent 工程指南。

## 为什么需要这个教程

模型负责推理和决策，Harness 负责把决策安全地落到真实环境。本教程围绕四个核心问题递进：

1. **Agent 如何行动？** 用一个稳定的循环读取模型回复、执行工具、追加结果。
2. **Agent 如何被约束？** 用文件边界、权限策略、Hook 和结构化协议控制副作用。
3. **Agent 如何处理长任务？** 用 TODO、子 Agent、Skill、上下文压缩、记忆、恢复、后台任务和 Cron 延长有效工作时间。
4. **多个 Agent 如何协作并接入外部能力？** 用任务认领、Mailbox、协议审批、Worktree 和 MCP 形成可恢复、可审计的协作运行时。

---

## 教程脉络

```text
Agent Loop
  -> 工具与文件边界
  -> 权限与 Hook
  -> 计划、子 Agent、Skill
  -> 产物落盘、上下文压缩、跨会话记忆
  -> 动态 Prompt、API 恢复、任务 DAG
  -> 后台任务、Cron
  -> Teammate、Mailbox、协议与计划审批
  -> SQLite 认领、Worktree 隔离
  -> MCP 动态工具池
  -> 完整 Harness
```

---

## 第一部分：执行基础（Ch01-Ch04）

### 第 1 章：Agent Loop — 循环是模型与真实世界之间的全部距离

#### 问题

语言模型能推理代码，但碰不到真实世界——不能读文件、跑测试、看报错。没有循环，每次工具调用你都得手动把结果粘回去。你自己就是那个循环。

#### 解决方案

```
+--------+      +-------+      +---------+
|  User  | ---> |  LLM  | ---> |  Tool   |
| prompt |      |       |      | execute |
+--------+      +---+---+      +----+----+
                    ^                |
                    |   tool_result  |
                    +----------------+
                    (loop until stop_reason != "tool_use")
```

一个退出条件控制整个流程。循环持续运行，直到模型不再调用工具。

#### 核心实现（Python）

```python
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-20250514"
SYSTEM = "You are a helpful assistant with access to tools."

TOOLS = [
    {
        "name": "bash",
        "description": "Run a bash command",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"}
            },
            "required": ["command"]
        }
    }
]

def run_bash(command: str) -> str:
    import subprocess
    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
    return result.stdout + result.stderr

def agent_loop(query: str):
    messages = [{"role": "user", "content": query}]
    
    while True:
        response = client.messages.create(
            model=MODEL, system=SYSTEM, messages=messages,
            tools=TOOLS, max_tokens=8000,
        )
        messages.append({"role": "assistant", "content": response.content})
        
        if response.stop_reason != "tool_use":
            return
        
        results = []
        for block in response.content:
            if block.type == "tool_use":
                output = run_bash(block.input["command"])
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })
        messages.append({"role": "user", "content": results})
```

不到 30 行，这就是整个 Agent。后面所有章节都在这个循环上叠加机制——循环本身始终不变。

#### 关键设计点

- **退出条件**：`stop_reason != "tool_use"` 时结束循环
- **工具结果注入**：以 `user` 消息形式追加，让模型看到执行结果
- **幂等性**：循环可随时中断，下次从新 prompt 重启

---

### 第 2 章：工具与文件 — 给 Agent 加一个工具只需要加一行

#### 问题

只有 bash 工具太粗糙。Agent 需要结构化的文件操作能力，同时要防止它访问工作目录之外的文件。

#### 解决方案

注册表模式 + 安全路径约束：

```python
from pathlib import Path
import json
import os

WORKSPACE = Path("./workspace")
WORKSPACE.mkdir(exist_ok=True)

def safe_path(path: str) -> Path:
    """确保路径在 workspace 内"""
    resolved = (WORKSPACE / path).resolve()
    if not str(resolved).startswith(str(WORKSPACE.resolve())):
        raise ValueError(f"Path {path} is outside workspace")
    return resolved

TOOL_HANDLERS = {}

def tool(name):
    def decorator(fn):
        TOOL_HANDLERS[name] = fn
        return fn
    return decorator

@tool("read_file")
def read_file(path: str) -> str:
    return safe_path(path).read_text(encoding="utf-8")

@tool("write_file")
def write_file(path: str, content: str) -> str:
    p = safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Written {len(content)} bytes to {path}"

@tool("list_files")
def list_files(path: str = ".") -> str:
    p = safe_path(path)
    files = [f.name for f in p.iterdir()]
    return json.dumps(files, indent=2)
```

#### 关键设计点

- **注册表模式**：`@tool` 装饰器自动注册，加工具只需加函数
- **安全路径**：`safe_path()` 防止目录遍历攻击
- **原子化设计**：每个工具只做一件事，可组合

---

### 第 3 章：权限系统 — 生产级的 Agent 安全策略

#### 问题

Agent 可能执行危险操作（删除文件、修改系统配置）。需要一个权限系统来控制哪些操作需要审批、哪些可以自动执行。

#### 解决方案

四态权限模型：

```python
from enum import Enum

class Permission(Enum):
    ALLOW = "allow"           # 自动允许
    ASK = "ask"               # 需要用户审批
    DENY = "deny"             # 直接拒绝
    ASK_ONCE = "ask_once"     # 本次会话内首次需要审批，之后自动允许

class PermissionPolicy:
    def __init__(self):
        self.rules = {}
        self.granted = set()  # ASK_ONCE 已授权的
    
    def check(self, tool_name: str, params: dict) -> Permission:
        if tool_name in self.rules:
            perm = self.rules[tool_name]
            if perm == Permission.ASK_ONCE:
                if tool_name in self.granted:
                    return Permission.ALLOW
                return Permission.ASK
            return perm
        return Permission.ALLOW  # 默认允许
    
    def grant_once(self, tool_name: str):
        self.granted.add(tool_name)

policy = PermissionPolicy()
policy.rules["bash"] = Permission.ASK          # bash 需要审批
policy.rules["write_file"] = Permission.ASK_ONCE  # 首次写文件需要审批
policy.rules["read_file"] = Permission.ALLOW   # 读文件自动允许
```

#### 工具执行拦截

```python
def execute_tool(name: str, params: dict) -> str:
    perm = policy.check(name, params)
    
    if perm == Permission.DENY:
        return "Error: Permission denied"
    
    if perm == Permission.ASK:
        # 模拟用户审批（实际应调用 UI）
        approved = input(f"Allow {name}({params})? [y/N]: ").lower() == "y"
        if not approved:
            return "Error: User denied"
    
    if perm == Permission.ASK_ONCE:
        if name not in policy.granted:
            approved = input(f"Allow {name}({params})? (once) [y/N]: ").lower() == "y"
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

#### 审计日志

```python
import datetime

AUDIT_LOG = []

def audit(tool_name: str, params: dict, result: str, permission: Permission):
    AUDIT_LOG.append({
        "timestamp": datetime.datetime.now().isoformat(),
        "tool": tool_name,
        "params": params,
        "permission": permission.value,
        "result": result[:200],  # 截断
    })
```

---

### 第 4 章：Hook 系统 — 用生命周期钩子解耦 Agent 行为

#### 问题

权限检查是静态的。Agent 需要在特定时刻动态调整行为：用户提交 prompt 前验证格式、工具执行前检查副作用、工具执行后记录日志、Agent 停止前保存状态。

#### 解决方案

四个生命周期钩子：

```python
from typing import Callable, List
from dataclasses import dataclass

@dataclass
class HookEvent:
    name: str
    data: dict

class HookManager:
    def __init__(self):
        self.hooks = {
            "UserPromptSubmit": [],   # 用户提交 prompt 前
            "PreToolUse": [],         # 工具执行前
            "PostToolUse": [],        # 工具执行后
            "Stop": [],               # Agent 停止前
        }
    
    def register(self, event: str, fn: Callable):
        if event in self.hooks:
            self.hooks[event].append(fn)
    
    def fire(self, event: str, data: dict) -> dict:
        for fn in self.hooks[event]:
            result = fn(data)
            if result is False:  # 返回 False 阻止后续执行
                return None
            if isinstance(result, dict):
                data.update(result)
        return data

hooks = HookManager()

# 示例：prompt 长度验证
def validate_prompt(data: dict):
    if len(data.get("prompt", "")) > 10000:
        print("Warning: Prompt too long, truncating...")
        data["prompt"] = data["prompt"][:10000]
    return data

hooks.register("UserPromptSubmit", validate_prompt)

# 示例：工具执行日志
def log_tool_use(data: dict):
    print(f"[LOG] {data['tool_name']} called with {data['params']}")
    return data

hooks.register("PreToolUse", log_tool_use)

# 示例：保存状态
def save_state(data: dict):
    # 保存对话历史到文件
    with open("state.json", "w") as f:
        json.dump(data.get("messages", []), f)
    return data

hooks.register("Stop", save_state)
```

#### 集成到 Agent Loop

```python
def agent_loop(query: str):
    messages = [{"role": "user", "content": query}]
    
    while True:
        # UserPromptSubmit hook
        hook_data = hooks.fire("UserPromptSubmit", {"prompt": query, "messages": messages})
        if hook_data is None:
            return "Blocked by hook"
        
        response = client.messages.create(
            model=MODEL, system=SYSTEM, messages=messages,
            tools=TOOLS, max_tokens=8000,
        )
        messages.append({"role": "assistant", "content": response.content})
        
        if response.stop_reason != "tool_use":
            # Stop hook
            hooks.fire("Stop", {"messages": messages})
            return
        
        results = []
        for block in response.content:
            if block.type == "tool_use":
                # PreToolUse hook
                hook_data = hooks.fire("PreToolUse", {
                    "tool_name": block.name,
                    "params": block.input
                })
                if hook_data is None:
                    results.append({"type": "tool_result", "tool_use_id": block.id, "content": "Blocked by hook"})
                    continue
                
                output = execute_tool(block.name, block.input)
                
                # PostToolUse hook
                hooks.fire("PostToolUse", {
                    "tool_name": block.name,
                    "params": block.input,
                    "result": output
                })
                
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
        
        messages.append({"role": "user", "content": results})
```

---

## 第二部分：上下文与知识管理（Ch05-Ch10）

### 第 5 章：会话计划 — 用 TODO 防止长任务漂移

#### 问题

长对话中，Agent 容易忘记最初目标，偏离任务。需要一个持久化的计划来锚定方向。

#### 解决方案

```python
import json
from pathlib import Path

class TodoManager:
    def __init__(self):
        self.items = []
    
    def add(self, text: str, status: str = "pending"):
        self.items.append({"text": text, "status": status})
    
    def update(self, index: int, status: str):
        if 0 <= index < len(self.items):
            self.items[index]["status"] = status
    
    def render(self) -> str:
        lines = ["## TODO"]
        for i, item in enumerate(self.items):
            mark = "x" if item["status"] == "done" else " "
            lines.append(f"- [{mark}] {item['text']}")
        return "\n".join(lines)

# 在 system prompt 中注入 TODO
TODO = TodoManager()

def get_system_prompt():
    base = "You are a helpful assistant."
    todo_state = TODO.render()
    if todo_state.strip() != "## TODO":
        return f"{base}\n\nCurrent plan:\n{todo_state}"
    return base
```

---

### 第 6 章：子 Agent — 复杂任务的分身协作

#### 问题

单个 Agent 处理复杂任务时，上下文会迅速膨胀。需要将子任务委派给独立的子 Agent。

#### 解决方案

```python
class SubAgent:
    def __init__(self, name: str, role: str, max_turns: int = 10):
        self.name = name
        self.role = role
        self.max_turns = max_turns
    
    def run(self, task: str) -> str:
        messages = [{"role": "user", "content": task}]
        system = f"You are {self.name}, a {self.role}. Complete the task concisely."
        
        for _ in range(self.max_turns):
            response = client.messages.create(
                model=MODEL, system=system, messages=messages,
                tools=TOOLS, max_tokens=4000,
            )
            messages.append({"role": "assistant", "content": response.content})
            
            if response.stop_reason != "tool_use":
                # 提取最终回答
                for block in response.content:
                    if hasattr(block, 'text'):
                        return block.text
                return "Task completed"
            
            results = []
            for block in response.content:
                if block.type == "tool_use":
                    output = execute_tool(block.name, block.input)
                    results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
            messages.append({"role": "user", "content": results})
        
        return "Max turns reached"

# 主 Agent 委派任务
def delegate_to_subagent(task: str, role: str = "assistant") -> str:
    agent = SubAgent(name="subagent", role=role, max_turns=5)
    return agent.run(task)
```

---

### 第 7 章：Skill 系统 — 按需加载的知识库

#### 问题

系统 prompt 不能塞太多内容（会稀释注意力）。需要按需加载领域知识。

#### 解决方案

```python
from pathlib import Path

SKILLS_DIR = Path("./skills")

class SkillManager:
    def __init__(self):
        self.skills = {}
        self._scan()
    
    def _scan(self):
        """扫描 skills 目录，只加载摘要"""
        if not SKILLS_DIR.exists():
            return
        for skill_file in SKILLS_DIR.glob("*.md"):
            content = skill_file.read_text(encoding="utf-8")
            # 提取第一行作为摘要
            first_line = content.split("\n")[0]
            self.skills[skill_file.stem] = {
                "summary": first_line,
                "path": skill_file
            }
    
    def list_skills(self) -> str:
        """返回所有可用技能的摘要"""
        lines = ["Available skills:"]
        for name, info in self.skills.items():
            lines.append(f"- {name}: {info['summary']}")
        return "\n".join(lines)
    
    def load(self, name: str) -> str:
        """加载完整技能内容"""
        if name not in self.skills:
            return f"Skill '{name}' not found"
        return self.skills[name]["path"].read_text(encoding="utf-8")

skills = SkillManager()

@tool("list_skills")
def list_skills() -> str:
    return skills.list_skills()

@tool("load_skill")
def load_skill(name: str) -> str:
    return skills.load(name)
```

---

### 第 8 章：上下文压缩 — 干净的记忆，无限的会话

#### 问题

上下文窗口是有限的。读 30 个文件、跑 20 条命令，轻松突破 100k token。不压缩，Agent 根本没法在大项目里干活。

#### 解决方案

三层压缩，激进程度递增：

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

#### 实现

```python
KEEP_RECENT = 3
THRESHOLD = 50000

def micro_compact(messages: list) -> list:
    """第一层：替换旧的 tool_result"""
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

def auto_compact(messages: list) -> list:
    """第二层：LLM 摘要"""
    # 保存完整历史
    transcript_path = Path(".transcripts")
    transcript_path.mkdir(exist_ok=True)
    with open(transcript_path / f"transcript_{int(time.time())}.jsonl", "w") as f:
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

def estimate_tokens(messages: list) -> int:
    """粗略估算 token 数"""
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total += len(content) // 4
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    total += len(part.get("content", "")) // 4
    return total
```

---

### 第 9 章：文件记忆 — 跨会话的持久化

#### 问题

上下文压缩后，Agent 会遗忘之前的决策和历史。需要文件级持久化。

#### 解决方案

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
        """存储记忆"""
        entry = {
            "key": key,
            "value": value,
            "tags": tags or [],
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.index["entries"].append(entry)
        self._save_index()
        
        # 保存到独立文件
        memory_file = MEMORY_DIR / f"{key.replace('/', '_')}.md"
        memory_file.write_text(value, encoding="utf-8")
    
    def recall(self, query: str) -> str:
        """检索相关记忆"""
        results = []
        for entry in self.index["entries"]:
            if query.lower() in entry["key"].lower() or query.lower() in entry["value"].lower():
                results.append(entry)
        
        if not results:
            return "No relevant memories found"
        
        lines = ["Relevant memories:"]
        for entry in results[:5]:  # 最多返回 5 条
            lines.append(f"- {entry['key']}: {entry['value'][:200]}")
        return "\n".join(lines)
    
    def forget(self, key: str):
        """删除记忆"""
        self.index["entries"] = [e for e in self.index["entries"] if e["key"] != key]
        self._save_index()
        memory_file = MEMORY_DIR / f"{key.replace('/', '_')}.md"
        if memory_file.exists():
            memory_file.unlink()

memory = MemoryManager()

@tool("remember")
def remember(key: str, value: str) -> str:
    memory.remember(key, value)
    return f"Remembered: {key}"

@tool("recall")
def recall(query: str) -> str:
    return memory.recall(query)
```

---

### 第 10 章：动态上下文 — 模块化的系统提示

#### 问题

系统提示词太长会稀释注意力，太短会缺少必要信息。需要按需组装上下文。

#### 解决方案

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

# 注册上下文提供者
def base_prompt(ctx):
    return "You are a helpful coding assistant."

def workspace_info(ctx):
    files = list(WORKSPACE.glob("**/*"))[:20]
    return f"Workspace files: {[f.name for f in files]}"

def active_skills(ctx):
    return skills.list_skills()

def memory_context(ctx):
    return memory.recall(ctx.get("topic", ""))

dynamic_prompt.register("base", base_prompt, priority=0)
dynamic_prompt.register("workspace", workspace_info, priority=10)
dynamic_prompt.register("skills", active_skills, priority=20)
dynamic_prompt.register("memory", memory_context, priority=30)

# 使用
system = dynamic_prompt.build({"topic": "authentication"})
```

---

## 第三部分：可靠执行与任务系统（Ch11-Ch14）

### 第 11 章：API 韧性 — 决定 Agent 商业化成败的隐藏细节

#### 问题

生产环境中，API 调用会失败：网络超时、速率限制、模型过载。Agent 需要优雅地处理这些故障。

#### 解决方案

```python
import time
import random

class RetryPolicy:
    def __init__(self, max_retries=3, base_delay=1, max_delay=30):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def get_delay(self, attempt: int) -> float:
        delay = self.base_delay * (2 ** attempt)
        delay = min(delay, self.max_delay)
        delay *= random.uniform(0.5, 1.5)  # 抖动
        return delay

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half-open
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
    
    def record_success(self):
        self.failure_count = 0
        self.state = "closed"
    
    def can_execute(self) -> bool:
        if self.state == "closed":
            return True
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
                return True
            return False
        return True  # half-open

retry_policy = RetryPolicy()
circuit_breaker = CircuitBreaker()

def resilient_api_call(messages, **kwargs):
    for attempt in range(retry_policy.max_retries + 1):
        if not circuit_breaker.can_execute():
            raise Exception("Circuit breaker is open")
        
        try:
            response = client.messages.create(
                model=MODEL, messages=messages, **kwargs
            )
            circuit_breaker.record_success()
            return response
        except anthropic.RateLimitError:
            delay = retry_policy.get_delay(attempt)
            print(f"Rate limited, waiting {delay:.1f}s...")
            time.sleep(delay)
        except anthropic.APIError as e:
            circuit_breaker.record_failure()
            if attempt == retry_policy.max_retries:
                raise
            delay = retry_policy.get_delay(attempt)
            print(f"API error: {e}, retrying in {delay:.1f}s...")
            time.sleep(delay)
```

---

### 第 12 章：任务引擎 — 生产级的 Task DAG

#### 问题

TODO 太简单，没有依赖关系。真实项目需要任务图（DAG）来管理复杂的工作流。

#### 解决方案

```python
from pathlib import Path
import json

TASKS_DIR = Path("./tasks")

class TaskEngine:
    def __init__(self):
        TASKS_DIR.mkdir(exist_ok=True)
    
    def create(self, subject: str, description: str = "", blocked_by: list = None) -> dict:
        task_id = self._next_id()
        task = {
            "id": task_id,
            "subject": subject,
            "description": description,
            "status": "pending",
            "blockedBy": blocked_by or [],
            "owner": "",
            "createdAt": datetime.datetime.now().isoformat()
        }
        self._save(task)
        return task
    
    def _next_id(self) -> int:
        existing = list(TASKS_DIR.glob("task_*.json"))
        if not existing:
            return 1
        ids = [int(f.stem.split("_")[1]) for f in existing]
        return max(ids) + 1
    
    def _save(self, task: dict):
        path = TASKS_DIR / f"task_{task['id']}.json"
        path.write_text(json.dumps(task, indent=2), encoding="utf-8")
    
    def _load(self, task_id: int) -> dict:
        path = TASKS_DIR / f"task_{task_id}.json"
        return json.loads(path.read_text(encoding="utf-8"))
    
    def update(self, task_id: int, **kwargs):
        task = self._load(task_id)
        task.update(kwargs)
        if task.get("status") == "completed":
            self._clear_dependency(task_id)
        self._save(task)
    
    def _clear_dependency(self, completed_id: int):
        for f in TASKS_DIR.glob("task_*.json"):
            task = json.loads(f.read_text(encoding="utf-8"))
            if completed_id in task.get("blockedBy", []):
                task["blockedBy"].remove(completed_id)
                self._save(task)
    
    def list_all(self) -> list:
        tasks = []
        for f in sorted(TASKS_DIR.glob("task_*.json")):
            tasks.append(json.loads(f.read_text(encoding="utf-8")))
        return tasks
    
    def get_ready_tasks(self) -> list:
        """获取可以执行的任务（pending 且无阻塞）"""
        ready = []
        for task in self.list_all():
            if task["status"] == "pending" and not task["blockedBy"]:
                ready.append(task)
        return ready
    
    def render_dag(self) -> str:
        """可视化任务依赖"""
        lines = ["Task DAG:"]
        for task in self.list_all():
            status_mark = {"pending": "○", "in_progress": "◐", "completed": "●"}.get(task["status"], "?")
            deps = f" <- {task['blockedBy']}" if task["blockedBy"] else ""
            lines.append(f"  {status_mark} Task {task['id']}: {task['subject']}{deps}")
        return "\n".join(lines)

tasks = TaskEngine()
```

---

### 第 13 章：异步操作 — 填坑慢操作

#### 问题

文件 I/O、API 调用、长时间运行的命令会阻塞 Agent。需要异步执行。

#### 解决方案

```python
import threading
from queue import Queue

class AsyncTaskManager:
    def __init__(self):
        self.tasks = {}
        self.results = Queue()
    
    def submit(self, task_id: str, fn, *args, **kwargs):
        def wrapper():
            try:
                result = fn(*args, **kwargs)
                self.results.put({"task_id": task_id, "result": result, "error": None})
            except Exception as e:
                self.results.put({"task_id": task_id, "result": None, "error": str(e)})
        
        thread = threading.Thread(target=wrapper, daemon=True)
        self.tasks[task_id] = {"thread": thread, "status": "running"}
        thread.start()
    
    def check(self, task_id: str) -> dict:
        while not self.results.empty():
            result = self.results.get()
            if result["task_id"] in self.tasks:
                self.tasks[result["task_id"]]["status"] = "completed"
                self.tasks[result["task_id"]]["result"] = result
        return self.tasks.get(task_id, {"status": "unknown"})

async_tasks = AsyncTaskManager()

@tool("run_async")
def run_async(command: str) -> str:
    import subprocess
    task_id = f"async_{int(time.time())}"
    async_tasks.submit(task_id, subprocess.run, command, shell=True, capture_output=True, text=True, timeout=300)
    return f"Started async task: {task_id}"

@tool("check_async")
def check_async(task_id: str) -> str:
    status = async_tasks.check(task_id)
    return json.dumps(status, default=str, indent=2)
```

---

### 第 14 章：Cron 调度 — 定时触发任务

#### 问题

Agent 需要定期执行任务：检查更新、清理缓存、生成报告。

#### 解决方案

```python
import schedule
from datetime import datetime

class CronScheduler:
    def __init__(self):
        self.jobs = []
    
    def add_job(self, name: str, interval_minutes: int, fn):
        def job():
            print(f"[{datetime.now()}] Running scheduled job: {name}")
            fn()
        
        schedule.every(interval_minutes).minutes.do(job)
        self.jobs.append({"name": name, "interval": interval_minutes, "fn": fn})
    
    def run_pending(self):
        schedule.run_pending()
    
    def list_jobs(self) -> str:
        lines = ["Scheduled jobs:"]
        for job in self.jobs:
            lines.append(f"- {job['name']}: every {job['interval']} minutes")
        return "\n".join(lines)

cron = CronScheduler()

# 示例：每 30 分钟清理临时文件
def cleanup_temp():
    import shutil
    temp_dir = Path("./temp")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
        temp_dir.mkdir()

cron.add_job("cleanup_temp", 30, cleanup_temp)
```

---

## 第四部分：多 Agent 协作与隔离（Ch15-Ch18）

### 第 15 章：Inbox 机制 — 异步通信

#### 问题

多个 Agent 需要通信，但不想阻塞彼此的执行。

#### 解决方案

```python
from pathlib import Path
import json

INBOX_DIR = Path("./inbox")

class MessageBus:
    def __init__(self):
        INBOX_DIR.mkdir(exist_ok=True)
    
    def send(self, sender: str, to: str, content: str, msg_type: str = "message"):
        inbox_path = INBOX_DIR / f"{to}.jsonl"
        msg = {
            "type": msg_type,
            "from": sender,
            "content": content,
            "timestamp": datetime.datetime.now().isoformat()
        }
        with open(inbox_path, "a") as f:
            f.write(json.dumps(msg) + "\n")
    
    def read_inbox(self, name: str) -> list:
        inbox_path = INBOX_DIR / f"{name}.jsonl"
        if not inbox_path.exists():
            return []
        
        msgs = []
        for line in inbox_path.read_text(encoding="utf-8").strip().split("\n"):
            if line:
                msgs.append(json.loads(line))
        
        # 清空收件箱
        inbox_path.write_text("", encoding="utf-8")
        return msgs
    
    def broadcast(self, sender: str, content: str):
        """广播给所有 Agent"""
        for inbox_file in INBOX_DIR.glob("*.jsonl"):
            name = inbox_file.stem
            if name != sender:
                self.send(sender, name, content, "broadcast")

bus = MessageBus()
```

---

### 第 16 章：协议审批 — 结构化的协作流程

#### 问题

多 Agent 协作需要明确的协议：谁负责什么、如何交接、如何处理冲突。

#### 解决方案

```python
class ProtocolManager:
    def __init__(self):
        self.protocols = {}
    
    def define(self, name: str, steps: list):
        self.protocols[name] = {
            "steps": steps,
            "current_step": 0,
            "status": "pending"
        }
    
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
        
        return f"Step {protocol['current_step']} completed: {step['description']}"
    
    def get_status(self) -> str:
        lines = ["Protocols:"]
        for name, protocol in self.protocols.items():
            status = protocol["status"]
            progress = f"{protocol['current_step']}/{len(protocol['steps'])}"
            lines.append(f"- {name}: {status} ({progress})")
        return "\n".join(lines)

protocols = ProtocolManager()
```

---

### 第 17 章：去中心化协作 — Agent 自主认领任务

#### 问题

集中式分配效率低。Agent 应该能自主发现和认领任务。

#### 解决方案

```python
class AutonomousAgent:
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.working = False
    
    def poll_for_tasks(self) -> dict:
        """扫描任务看板，寻找可认领的任务"""
        ready_tasks = tasks.get_ready_tasks()
        if not ready_tasks:
            return None
        
        # 认领第一个可用任务
        task = ready_tasks[0]
        tasks.update(task["id"], owner=self.name, status="in_progress")
        return task
    
    def check_inbox(self) -> list:
        """检查收件箱"""
        return bus.read_inbox(self.name)
    
    def idle_cycle(self, max_wait: int = 60, poll_interval: int = 5):
        """空闲阶段：轮询任务和收件箱"""
        for _ in range(max_wait // poll_interval):
            time.sleep(poll_interval)
            
            # 检查收件箱
            inbox = self.check_inbox()
            if inbox:
                return {"type": "inbox", "messages": inbox}
            
            # 检查任务
            task = self.poll_for_tasks()
            if task:
                return {"type": "task", "task": task}
        
        return None  # 超时
```

---

### 第 18 章：Worktree 隔离 — 并行开发的安全边界

#### 问题

多个 Agent 同时修改同一个仓库会冲突。需要目录级隔离。

#### 解决方案

```python
import subprocess

class WorktreeManager:
    def __init__(self):
        self.worktrees = {}
        self.worktree_dir = Path("./worktrees")
        self.worktree_dir.mkdir(exist_ok=True)
    
    def create(self, name: str, task_id: int = None) -> str:
        branch = f"wt/{name}"
        path = self.worktree_dir / name
        
        # 创建 git worktree
        result = subprocess.run(
            ["git", "worktree", "add", "-b", branch, str(path), "HEAD"],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            return f"Failed to create worktree: {result.stderr}"
        
        self.worktrees[name] = {
            "path": path,
            "branch": branch,
            "task_id": task_id,
            "created_at": datetime.datetime.now().isoformat()
        }
        
        # 绑定任务
        if task_id:
            tasks.update(task_id, status="in_progress")
        
        return f"Created worktree '{name}' at {path}"
    
    def run_in(self, name: str, command: str) -> str:
        """在 worktree 中执行命令"""
        if name not in self.worktrees:
            return f"Worktree '{name}' not found"
        
        path = self.worktrees[name]["path"]
        result = subprocess.run(
            command, shell=True, cwd=str(path),
            capture_output=True, text=True, timeout=300
        )
        return result.stdout + result.stderr
    
    def remove(self, name: str, complete_task: bool = False) -> str:
        """移除 worktree"""
        if name not in self.worktrees:
            return f"Worktree '{name}' not found"
        
        wt = self.worktrees[name]
        
        # 完成绑定的任务
        if complete_task and wt.get("task_id"):
            tasks.update(wt["task_id"], status="completed")
        
        # 移除 worktree
        subprocess.run(["git", "worktree", "remove", str(wt["path"])], capture_output=True)
        
        del self.worktrees[name]
        return f"Removed worktree '{name}'"
    
    def list_all(self) -> str:
        lines = ["Worktrees:"]
        for name, info in self.worktrees.items():
            task_info = f" (task: {info['task_id']})" if info.get('task_id') else ""
            lines.append(f"- {name}: {info['path']}{task_info}")
        return "\n".join(lines) if lines else "No worktrees"

worktrees = WorktreeManager()
```

---

## 第五部分：动态扩展与总装（Ch19-Ch20）

### 第 19 章：MCP 集成 — 动态工具池

#### 问题

静态工具列表无法扩展。需要动态加载外部工具（MCP 协议）。

#### 解决方案

```python
class MCPManager:
    def __init__(self):
        self.servers = {}
        self.tools = {}
    
    def register_server(self, name: str, config: dict):
        """注册 MCP 服务器"""
        self.servers[name] = {
            "config": config,
            "status": "connected",
            "tools": []
        }
    
    def discover_tools(self, server_name: str) -> list:
        """发现服务器提供的工具"""
        # 实际应调用 MCP 协议
        # 这里模拟返回
        mock_tools = [
            {"name": f"{server_name}_tool_1", "description": "Tool from server"},
        ]
        self.servers[server_name]["tools"] = mock_tools
        return mock_tools
    
    def call_tool(self, server_name: str, tool_name: str, params: dict) -> str:
        """调用 MCP 工具"""
        # 实际应通过 MCP 协议调用
        return f"Called {tool_name} on {server_name} with {params}"
    
    def list_servers(self) -> str:
        lines = ["MCP Servers:"]
        for name, info in self.servers.items():
            tool_count = len(info.get("tools", []))
            lines.append(f"- {name}: {info['status']} ({tool_count} tools)")
        return "\n".join(lines) if lines else "No servers"

mcp = MCPManager()
```

---

### 第 20 章：完整 Harness — 统一运行时

#### 问题

所有组件需要整合成一个统一的运行时。

#### 解决方案

```python
class AgentHarness:
    def __init__(self):
        self.hooks = HookManager()
        self.tools = TOOL_HANDLERS
        self.policy = PermissionPolicy()
        self.skills = SkillManager()
        self.memory = MemoryManager()
        self.tasks = TaskEngine()
        self.bus = MessageBus()
        self.worktrees = WorktreeManager()
        self.cron = CronScheduler()
        self.mcp = MCPManager()
        self.dynamic_prompt = DynamicPrompt()
        
        # 注册所有工具
        self._register_tools()
    
    def _register_tools(self):
        # 基础工具
        self.tools.update({
            "read_file": read_file,
            "write_file": write_file,
            "list_files": list_files,
            "bash": run_bash,
            # 技能工具
            "list_skills": lambda: self.skills.list_skills(),
            "load_skill": lambda name: self.skills.load(name),
            # 记忆工具
            "remember": lambda key, value: self.memory.remember(key, value),
            "recall": lambda query: self.memory.recall(query),
            # 任务工具
            "task_create": lambda subject, **kw: self.tasks.create(subject, **kw),
            "task_update": lambda task_id, **kw: self.tasks.update(task_id, **kw),
            "task_list": lambda: json.dumps(self.tasks.list_all(), indent=2),
            # 异步工具
            "run_async": lambda command: async_tasks.submit(f"async_{int(time.time())}", subprocess.run, command, shell=True, capture_output=True, text=True, timeout=300),
            "check_async": lambda task_id: json.dumps(async_tasks.check(task_id), default=str),
        })
    
    def run(self, query: str):
        """主运行循环"""
        messages = [{"role": "user", "content": query}]
        
        while True:
            # 动态系统提示
            system = self.dynamic_prompt.build({"messages": messages})
            
            # UserPromptSubmit hook
            hook_data = self.hooks.fire("UserPromptSubmit", {"prompt": query, "messages": messages})
            if hook_data is None:
                return "Blocked by hook"
            
            # 压缩检查
            micro_compact(messages)
            if estimate_tokens(messages) > THRESHOLD:
                messages[:] = auto_compact(messages)
            
            # 调用模型
            response = resilient_api_call(
                messages=messages,
                system=system,
                tools=self._get_tool_definitions(),
                max_tokens=8000,
            )
            messages.append({"role": "assistant", "content": response.content})
            
            if response.stop_reason != "tool_use":
                self.hooks.fire("Stop", {"messages": messages})
                return
            
            # 执行工具
            results = []
            for block in response.content:
                if block.type == "tool_use":
                    # 权限检查
                    perm = self.policy.check(block.name, block.input)
                    if perm == Permission.DENY:
                        results.append({"type": "tool_result", "tool_use_id": block.id, "content": "Permission denied"})
                        continue
                    
                    # PreToolUse hook
                    hook_data = self.hooks.fire("PreToolUse", {"tool_name": block.name, "params": block.input})
                    if hook_data is None:
                        results.append({"type": "tool_result", "tool_use_id": block.id, "content": "Blocked by hook"})
                        continue
                    
                    # 执行
                    try:
                        handler = self.tools.get(block.name)
                        if not handler:
                            output = f"Unknown tool: {block.name}"
                        else:
                            output = handler(**block.input)
                    except Exception as e:
                        output = f"Error: {str(e)}"
                    
                    # PostToolUse hook
                    self.hooks.fire("PostToolUse", {"tool_name": block.name, "params": block.input, "result": output})
                    
                    results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(output)})
            
            messages.append({"role": "user", "content": results})
    
    def _get_tool_definitions(self) -> list:
        """生成工具定义"""
        definitions = []
        for name in self.tools:
            definitions.append({
                "name": name,
                "description": f"Tool: {name}",
                "input_schema": {"type": "object", "properties": {}}
            })
        return definitions

# 启动 Harness
harness = AgentHarness()
```

---

## 快速开始

### 环境要求

- Python 3.10+
- Anthropic API Key

### 安装

```bash
pip install anthropic
export ANTHROPIC_API_KEY="your-api-key"
```

### 运行示例

```python
# 最简 Agent
agent_loop("列出当前目录的文件")

# 带任务的 Agent
harness = AgentHarness()
harness.tasks.create("实现用户认证模块")
harness.tasks.create("编写单元测试", blocked_by=[1])
harness.run("完成所有任务")
```

---

## 项目结构

```
agent-tutorial/
├── README.md                 # 本文件
├── agents/
│   ├── s01_agent_loop.py    # Agent 循环
│   ├── s02_tool_use.py      # 工具使用
│   ├── s03_permissions.py   # 权限系统
│   ├── s04_hooks.py         # Hook 系统
│   ├── s05_todo.py          # TODO 管理
│   ├── s06_subagent.py      # 子 Agent
│   ├── s07_skills.py        # 技能系统
│   ├── s08_compact.py       # 上下文压缩
│   ├── s09_memory.py        # 记忆系统
│   ├── s10_dynamic.py       # 动态上下文
│   ├── s11_resilience.py    # API 韧性
│   ├── s12_task_engine.py   # 任务引擎
│   ├── s13_async.py         # 异步操作
│   ├── s14_cron.py          # Cron 调度
│   ├── s15_inbox.py         # Inbox 通信
│   ├── s16_protocols.py     # 协议审批
│   ├── s17_autonomous.py    # 自治 Agent
│   ├── s18_worktree.py      # Worktree 隔离
│   ├── s19_mcp.py           # MCP 集成
│   └── s20_harness.py       # 完整 Harness
├── skills/                   # 示例技能
├── workspace/                # 工作目录
└── tests/                    # 测试
```

---

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](./CONTRIBUTING.md) 了解详情。

## 许可证

MIT License

---

**核心原则**：每章只增加一个主要能力，前章行为继续保留。循环本身始终不变。
