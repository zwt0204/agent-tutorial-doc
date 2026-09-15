"""Chapter 19: MCP integration - dynamic tool discovery."""
import json, sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from base import get_client, get_model, run_bash, MAX_TURNS


class MCPManager:
    def __init__(self):
        self.servers = {}

    def register(self, name, config):
        self.servers[name] = {"config": config, "status": "connected", "tools": []}

    def discover(self, name):
        tools = [{"name": f"{name}_action", "description": f"Action from {name}"}]
        self.servers[name]["tools"] = tools
        return tools

    def call(self, name, tool_name, params):
        return f"Called {tool_name} on {name} with {params}"

    def list_all(self):
        if not self.servers:
            return "No MCP servers"
        lines = []
        for n, info in self.servers.items():
            lines.append(f"- {n}: {info['status']} ({len(info['tools'])} tools)")
        return "\n".join(lines)


# mcp initialized lazily

TOOLS = [
    {"type": "function", "function": {"name": "bash", "description": "Run bash",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "mcp_register", "description": "Register MCP server",
        "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "url": {"type": "string"}}, "required": ["name", "url"]}}},
    {"type": "function", "function": {"name": "mcp_discover", "description": "Discover tools from server",
        "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "mcp_list", "description": "List MCP servers",
        "parameters": {"type": "object", "properties": {}}}},
]



def agent_loop(query):
    mcp = MCPManager()
    client = get_client()
    MODEL = get_model()
    messages = [{"role": "user", "content": query}]
    for _ in range(MAX_TURNS):
        resp = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS, max_tokens=8000)
        msg = resp.choices[0].message
        messages.append(msg.model_dump())
        if not msg.tool_calls:
            print(msg.content)
            return
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            if tc.function.name == "bash":
                output = run_bash(args["command"])
            elif tc.function.name == "mcp_register":
                mcp.register(args["name"], {"url": args["url"]})
                output = f"Registered: {args['name']}"
            elif tc.function.name == "mcp_discover":
                tools = mcp.discover(args["name"])
                output = f"Discovered {len(tools)} tools"
            elif tc.function.name == "mcp_list":
                output = mcp.list_all()
            else:
                output = "Unknown"
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(output)})

if __name__ == "__main__":
    query = input("You: ") if len(sys.argv) < 2 else sys.argv[1]
    agent_loop(query)
