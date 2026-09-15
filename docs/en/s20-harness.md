# Chapter 20: Complete Harness -- Unified Runtime

`s01 > ... > s19 > [ s20 ]`

> *"Verify that all 19 chapters' capabilities work together in one AgentRunner"*

---

## This is the final chapter. No new mechanisms -- just assembly.

### Component List

```python
class AgentHarness:
    def __init__(self):
        self.policy = PermissionPolicy()    # Ch03
        self.hooks = HookManager()          # Ch04
        self.skills = SkillManager()        # Ch07
        self.memory = MemoryManager()       # Ch09
        self.tasks = TaskEngine()           # Ch12
        # Ch01 loop, Ch02 tools, Ch05 TODO,
        # Ch06 subagent, Ch08 compact, Ch10 dynamic prompt,
        # Ch11 resilience, Ch13 async, Ch14 cron,
        # Ch15 inbox, Ch16 protocols, Ch17 autonomous,
        # Ch18 worktree, Ch19 MCP
```

### Design Principles

1. **Loop unchanged**: All expansion outside the loop.
2. **Add per chapter**: One capability at a time, previous preserved.
3. **Tools = interface**: All Agent capabilities exposed as tools.
4. **Security first**: Permission check before execution, fail-closed.
5. **Disk is truth**: Tasks, memory, worktrees persist to disk. Sessions are volatile.

---

## Final Words

You're not writing intelligence. You're building the world intelligence inhabits. The quality of that world -- how clearly the Agent can see, how precisely it can act, how rich its available knowledge is -- directly determines how effectively intelligence can express itself.

**Build good Harnesses. The Agents will handle the rest.**
