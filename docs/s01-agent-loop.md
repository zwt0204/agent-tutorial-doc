# 第 1 章:Agent Loop -- 一个循环,就是模型与真实世界之间的全部距离

`[ s01 ] s02 > s03 > s04 > s05 > s06 | s07 > s08 > s09 > s10 > s11 > s12`

> *"One loop is all you need"* -- 一个循环 = 一个 Agent。
>
> **Harness 层**: 循环 -- 模型与真实世界的第一道连接。

---

## 本章导读

### 读完这一章,你能做到什么

1. 用一句话说清 Agent 和"调用一次模型 API"的区别。
2. 看懂一轮 Agent 对话在网络上传了哪些 JSON 字段。
3. 自己手写一个不到 30 行、能跑起来的 Agent Loop。
4. 说出这个循环在什么条件下结束,以及为什么必须有轮次上限。
5. 在本机跑通第 1 章配套代码,并让 Agent 帮你执行一条命令。

### 你需要先具备什么

| 需要 | 程度 |
| --- | --- |
| Python | 能看懂函数定义、字典、列表,不需要熟悉高级特性 |
| 命令行 | 能在终端里进入目录、运行 `pip` 和 `python` 命令 |
| 大模型 API | 知道"把消息发给模型、模型返回文本"这件事就够了 |
| 上一章 | 无。这是第 1 章 |

### 术语速查(本章第一次出现的词)

| 术语 | 一句话解释 |
| --- | --- |
| **Agent Loop** | "问模型 → 执行工具 → 把结果喂回去 → 再问模型"的循环 |
| **Harness**(挽具) | 循环之外的所有代码:配置校验、工具注册、审批、轮次上限。模型负责决定,Harness 负责安全地落地 |
| **轮次(turn)** | 一次"发请求给模型"算一轮。注意不是一次工具调用算一轮 |
| **tool_use** | 模型回复中的一个块。非空表示"我要用工具",空表示"我说完了" |
| **tool_result** | 工具执行的返回结果,作为 user 消息追加到对话历史 |
| **stop_reason** | 模型回复的停止原因。`tool_use` 表示要调工具,其他表示结束 |

---

## 先说你现在是什么角色

在还没有 Agent 之前,你用大模型的方式大概是这样的:

你在对话框输入"帮我看看当前目录有哪些 Python 文件"。模型输出了一条命令:

```bash
ls *.py
```

但它自己不跑。你切到终端,粘贴进去,回车,看到输出,再切回对话框,把输出复制进去。模型接着说"好,有 3 个文件,我来分析一下......"

每一次来回,你都在做同一件事:把工具结果手动传回给模型。这个时候,你其实是一个"人工循环" -- 模型和真实世界之间的中间层。

**Agent Loop 做的事情,就是把你从这个中间层里解放出来。** 程序自动把模型的请求执行掉,把结果喂回去,循环往复,直到模型说"我说完了"。

---

## 两个信号,一个循环

整个 Agent Loop 的决策树只有两个分支:

```
模型回复包含 tool_use?
├── 是 → 执行工具,把结果追加到消息历史,再问模型
└── 否 → 结束。模型的最终文本就是回答
```

就这么简单。一个退出条件控制整个流程。

---

## 看一眼真实的数据流

假设你问 Agent:"当前目录有什么文件?"

**第一轮 -- 用户发起:**

```json
messages = [
  {"role": "user", "content": "当前目录有什么文件?"}
]
```

**模型回复 -- 要调工具:**

```json
{
  "content": [
    {"type": "tool_use", "name": "bash", "input": {"command": "ls"}, "id": "call_001"}
  ],
  "stop_reason": "tool_use"
}
```

**程序执行工具,追加结果:**

```json
messages = [
  {"role": "user", "content": "当前目录有什么文件?"},
  {"role": "assistant", "content": [{"type": "tool_use", ...}]},
  {"role": "user", "content": [
    {"type": "tool_result", "tool_use_id": "call_001", "content": "main.py\ntest.py\n"}
  ]}
]
```

**第二轮 -- 再问模型:**

```json
{
  "content": [{"type": "text", "text": "当前目录有 main.py 和 test.py 两个文件。"}],
  "stop_reason": "end_turn"
}
```

`stop_reason` 不是 `tool_use` 了 -- 循环结束。

---

## 五步拆解 + 完整函数

```python
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-20250514"
SYSTEM = "You are a helpful assistant with access to a bash tool."

TOOLS = [
    {
        "name": "bash",
        "description": "Run a bash command and return output",
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
    messages = [{"role": "user", "content": query}]          # 1. 用户 prompt 作为第一条消息

    for turn in range(20):                                    # 2. 轮次上限,防止死循环
        response = client.messages.create(                    # 3. 发给模型
            model=MODEL, system=SYSTEM, messages=messages,
            tools=TOOLS, max_tokens=8000,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":                # 4. 模型没调工具 → 结束
            return

        results = []
        for block in response.content:                        # 5. 执行每个工具调用
            if block.type == "tool_use":
                output = run_bash(block.input["command"])
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })
        messages.append({"role": "user", "content": results})

if __name__ == "__main__":
    query = input("You: ")
    agent_loop(query)
```

不到 30 行,这就是整个 Agent。后面 19 章都在这个循环上叠加机制 -- **循环本身始终不变**。

---

## 为什么必须有轮次上限

模型可能陷入无限调工具的循环(比如反复读同一个文件试图找到不存在的内容)。`for turn in range(20)` 确保程序一定会退出。真实产品中这个上限通常是 50-100 轮。

---

## 试一试

```bash
cd agent-tutorial
python agents/s01_agent_loop.py
```

试试这些 prompt:

1. `列出当前目录的文件`
2. `创建一个 hello.py 文件,里面打印 Hello, World!`
3. `当前是什么时间?`
4. `这个目录下有几个 Python 文件?`

---

## 本章小结

- Agent = 模型 + Harness(循环 + 工具 + 安全边界)
- Agent Loop 是一个"问模型 → 执行工具 → 喂回去"的循环
- `stop_reason != "tool_use"` 是唯一的退出条件
- 轮次上限防止死循环
- 循环本身不随章节变化,后续章节只是在循环外围叠加能力
