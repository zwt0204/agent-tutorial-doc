# 第 19 章:MCP 集成 -- 动态工具池

`s01 > ... > s18 > [ s19 ] > s20`

> *"工具列表不应该写死"* -- 动态发现、安全沙箱、协议桥接。
>
> **Harness 层**: 工具路由 -- 让 Agent 接入外部能力。

---

## 问题

静态工具列表无法扩展。Agent 需要接入外部服务:GitHub API、数据库、浏览器、自定义工具。MCP (Model Context Protocol) 是标准协议。

## 解决方案

```python
class MCPManager:
    def __init__(self):
        self.servers = {}
        self.tools = {}

    def register_server(self, name: str, config: dict):
        self.servers[name] = {"config": config, "status": "connected", "tools": []}

    def discover_tools(self, server_name: str) -> list:
        # 实际应调用 MCP 协议 discover
        tools = [{"name": f"{server_name}_tool_1", "description": "Tool from server"}]
        self.servers[server_name]["tools"] = tools
        return tools

    def call_tool(self, server_name: str, tool_name: str, params: dict) -> str:
        # 实际应通过 MCP 协议调用
        return f"Called {tool_name} on {server_name}"

    def list_servers(self) -> str:
        lines = ["MCP Servers:"]
        for name, info in self.servers.items():
            tool_count = len(info.get("tools", []))
            lines.append(f"- {name}: {info['status']} ({tool_count} tools)")
        return "\n".join(lines) if lines else "No servers"

mcp = MCPManager()
```

## 试一试

```bash
python agents/s19_mcp.py
```

1. `注册一个 GitHub MCP 服务器`
2. `发现服务器提供的工具`
3. `调用 GitHub 工具获取仓库信息`

## 本章小结

- MCP 集成:动态发现和调用外部工具
- 服务器注册:配置化接入外部服务
- 安全沙箱:工具调用经过权限检查
