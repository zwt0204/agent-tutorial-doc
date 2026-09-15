"""Offline tests - no API key needed. Validates all chapter modules."""
import sys, json, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

def test_s02_tool_handlers():
    from s02_tool_use import HANDLERS, run_read, run_write, run_edit
    with tempfile.TemporaryDirectory() as tmpdir:
        import os; os.chdir(tmpdir)
        run_write("test.txt", "hello world")
        assert run_read("test.txt") == "hello world"
        run_edit("test.txt", "hello", "hi")
        assert run_read("test.txt") == "hi world"
        assert "bash" in HANDLERS
        assert "read_file" in HANDLERS
    print("PASS: s02 tool handlers")

def test_s03_permission():
    from s03_permission import PermissionPolicy
    p = PermissionPolicy()
    p.rules = {"bash": "ask_once", "write_file": "ask", "read_file": "allow"}
    assert p.check("read_file") == "allow"
    assert p.check("bash") == "ask_once"
    p.grant_once("bash")
    assert p.check("bash") == "allow"
    print("PASS: s03 permission")

def test_s04_hooks():
    from s04_hooks import HookManager
    h = HookManager()
    results = []
    h.register("PreToolUse", lambda d: results.append(d["tool_name"]) or d)
    h.fire("PreToolUse", {"tool_name": "bash"})
    assert results == ["bash"]
    print("PASS: s04 hooks")

def test_s05_todo():
    from s05_todo import TodoManager
    t = TodoManager()
    t.add("task 1")
    t.add("task 2")
    assert len(t.items) == 2
    t.done(0)
    assert t.items[0]["status"] == "done"
    rendered = t.render()
    assert "[x]" in rendered and "[ ]" in rendered
    print("PASS: s05 todo")

def test_s08_compact():
    from s08_context_compact import micro_compact
    messages = [{"role": "user", "content": [{"role": "tool", "content": "x" * 200}]},
                {"role": "user", "content": [{"role": "tool", "content": "y" * 200}]},
                {"role": "user", "content": [{"role": "tool", "content": "z" * 200}]}]
    micro_compact(messages)
    print("PASS: s08 compact")

def test_s09_memory():
    from s09_memory import MemoryManager
    with tempfile.TemporaryDirectory() as tmpdir:
        import s09_memory
        s09_memory.MEMORY_DIR = Path(tmpdir)
        m = MemoryManager()
        m.remember("test_key", "test_value")
        assert "test_key" in m.recall("test")
    print("PASS: s09 memory")

def test_s11_resilience():
    from s11_api_resilience import RetryPolicy, CircuitBreaker
    r = RetryPolicy(max_retries=3, base_delay=1)
    assert r.get_delay(0) > 0
    b = CircuitBreaker(threshold=2)
    assert b.can_execute()
    b.record_failure()
    b.record_failure()
    assert not b.can_execute()
    print("PASS: s11 resilience")

def test_s12_tasks():
    from s12_task_engine import TaskEngine
    with tempfile.TemporaryDirectory() as tmpdir:
        import s12_task_engine
        s12_task_engine.TASKS_DIR = Path(tmpdir)
        t = TaskEngine()
        t1 = t.create("task 1")
        t2 = t.create("task 2", blocked_by=[t1["id"]])
        assert len(t.list_all()) == 2
        ready = t.get_ready()
        assert len(ready) == 1 and ready[0]["id"] == t1["id"]
        t.update(t1["id"], status="completed")
        ready = t.get_ready()
        assert len(ready) == 1 and ready[0]["id"] == t2["id"]
    print("PASS: s12 tasks")

def test_s15_inbox():
    from s15_inbox import MessageBus
    with tempfile.TemporaryDirectory() as tmpdir:
        import s15_inbox
        s15_inbox.INBOX_DIR = Path(tmpdir)
        bus = MessageBus()
        bus.send("alice", "bob", "hello")
        msgs = bus.read_inbox("bob")
        assert len(msgs) == 1 and msgs[0]["content"] == "hello"
        assert bus.read_inbox("bob") == []
    print("PASS: s15 inbox")

def test_s16_protocols():
    from s16_protocols import ProtocolManager
    p = ProtocolManager()
    p.define("review", [{"assignee": "alice", "desc": "submit"}, {"assignee": "bob", "desc": "review"}])
    assert p.execute("review", "alice").startswith("Step")
    assert p.execute("review", "alice").startswith("Assigned")
    assert p.execute("review", "bob").startswith("Step")
    assert "completed" in p.status()
    print("PASS: s16 protocols")

def test_s19_mcp():
    from s19_mcp import MCPManager
    m = MCPManager()
    m.register("github", {"url": "https://api.github.com"})
    assert "github" in m.list_all()
    tools = m.discover("github")
    assert len(tools) > 0
    print("PASS: s19 mcp")

if __name__ == "__main__":
    test_s02_tool_handlers()
    test_s03_permission()
    test_s04_hooks()
    test_s05_todo()
    test_s08_compact()
    test_s09_memory()
    test_s11_resilience()
    test_s12_tasks()
    test_s15_inbox()
    test_s16_protocols()
    test_s19_mcp()
    print("\n=== ALL 11 TESTS PASSED ===")
