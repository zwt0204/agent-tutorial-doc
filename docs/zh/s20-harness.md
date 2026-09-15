# 第 20 章:完整 Harness -- 统一运行时

`s01 > s02 > ... > s19 > [ s20 ]`

> *"验证前 19 章能力能否在同一个 AgentRunner 中协同工作"*
>
> **Harness 层**: 总装 -- 所有能力的统一边界。

---

## 本章导读

这是最后一章。不引入新机制,而是把前 19 章的全部能力接入同一个 `AgentHarness` 类,验证它们能否协同工作。

### 读完这一章,你能做到什么

1. 理解完整 Harness 的组件清单和组装顺序。
2. 看到所有机制(循环、工具、权限、Hook、TODO、子Agent、Skill、压缩、记忆、动态提示、韧性、任务、异步、Cron、Inbox、协议、自治、Worktree、MCP)如何在同一个循环中协同。
3. 掌握 Harness 工程的核心原则:模型做决策,Harness 做执行。

---

## Harness 组件清单

```python
class AgentHarness:
    def __init__(self):
        self.hooks = HookManager()          # Ch04: 生命周期钩子
        self.policy = PermissionPolicy()    # Ch03: 权限系统
        self.skills = SkillManager()        # Ch07: 技能系统
        self.memory = MemoryManager()       # Ch09: 记忆系统
        self.tasks = TaskEngine()           # Ch12: 任务引擎
        self.bus = MessageBus()             # Ch15: 消息总线
        self.worktrees = WorktreeManager()  # Ch18: Worktree 隔离
        self.cron = CronScheduler()         # Ch14: Cron 调度
        self.mcp = MCPManager()             # Ch19: MCP 集成
        self.dynamic_prompt = DynamicPrompt() # Ch10: 动态上下文
        self._register_tools()              # Ch02: 工具注册
```

---

## 主循环

```python
def run(self, query: str):
    messages = [{"role": "user", "content": query}]

    for turn in range(MAX_TURNS):                         # Ch01: 轮次上限
        system = self.dynamic_prompt.build({"messages": messages})  # Ch10

        hook_data = self.hooks.fire("UserPromptSubmit", {"prompt": query})
        if hook_data is None:
            return "Blocked by hook"

        micro_compact(messages)                           # Ch08: 压缩
        if estimate_tokens(messages) > THRESHOLD:
            messages[:] = auto_compact(messages)

        response = resilient_api_call(                    # Ch11: 韧性
            messages=messages, system=system,
            tools=self._get_tool_definitions(), max_tokens=8000,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            self.hooks.fire("Stop", {"messages": messages})
            return

        results = []
        for block in response.content:
            if block.type == "tool_use":
                perm = self.policy.check(block.name, block.input)  # Ch03
                if perm == Permission.DENY:
                    results.append({"type": "tool_result", "tool_use_id": block.id, "content": "Permission denied"})
                    continue

                self.hooks.fire("PreToolUse", {"tool_name": block.name})
                try:
                    output = self._execute_tool(block.name, block.input)
                except Exception as e:
                    output = f"Error: {str(e)}"
                self.hooks.fire("PostToolUse", {"tool_name": block.name, "result": output})
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(output)})

        messages.append({"role": "user", "content": results})
```

---

## 设计原则

1. **循环不变**:所有扩展都在循环外围。循环本身只有"调模型 → 执行工具 → 追加结果"三步。
2. **逐章累加**:每章只增加一个主要能力,前章行为继续保留。
3. **工具即接口**:Agent 的所有能力都通过工具暴露。加工具 = 加能力,不需要改循环。
4. **安全边界前置**:权限检查在工具执行前,Hook 在权限后。fail-closed。
5. **磁盘即真理**:任务、记忆、Worktree 都持久化到磁盘。会话是易失的,磁盘是持久的。

---

## 完整工具清单(20 章累计)

| 来源 | 工具 | 说明 |
| --- | --- | --- |
| Ch02 | bash, read_file, write_file, edit_file | 基础文件操作 |
| Ch05 | todo_add, todo_done | 会话计划 |
| Ch06 | task (spawn subagent) | 子 Agent 委派 |
| Ch07 | list_skills, load_skill | 技能加载 |
| Ch09 | remember, recall | 记忆存取 |
| Ch12 | task_create, task_update, task_list | 任务 DAG |
| Ch13 | run_async, check_async | 异步执行 |
| Ch15 | send_message, read_inbox, broadcast | Agent 通信 |
| Ch17 | idle, claim_task | 自治认领 |
| Ch18 | worktree_create, worktree_remove | 目录隔离 |

---

## 试一试

```bash
python agents/s20_harness.py
```

1. `创建一个完整的项目任务图:设计 -> 实现 -> 测试 -> 部署`
2. `spawn 两个队友,让他们自动认领并行任务`
3. `观察完整 Harness 的权限检查、日志记录和压缩行为`

---

## 结语:造好 Harness,Agent 会完成剩下的

每一个部署在真实领域的好 Harness,都是 Agent 能够感知、推理、行动的又一个阵地。

你不是在编写智能。你是在构建智能栖居的世界。这个世界的质量 -- Agent 能看得多清楚、行动得多精准、可用知识有多丰富 -- 直接决定了智能能多有效地表达自己。

**Bash is all you need. Real agents are all the universe needs.**
