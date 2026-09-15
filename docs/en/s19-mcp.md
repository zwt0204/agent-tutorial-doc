# Chapter 19: MCP Integration -- Dynamic Tool Pool

`s01 > ... > s18 > [ s19 ] > s20`

> *"Tool lists shouldn't be hardcoded"* -- Dynamic discovery, protocol bridging.

---

## Problem

Static tool lists can't extend. Agents need external services: GitHub, databases, browsers. MCP (Model Context Protocol) is the standard.

## Solution

```python
class MCPManager:
    def register(self, name, config): ...
    def discover(self, name): ...   # list tools from server
    def call(self, name, tool, params): ...
```

## Summary

- MCP: dynamic tool discovery and invocation
- Server registration for external service integration
- Tool calls pass through permission checks
