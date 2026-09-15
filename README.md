[English](./README-en.md) | 中文

# AI Agent 工程实战:从零构建生产级 Agent Harness

一套渐进式中文教程,带你从最小的 Agent Loop 开始,逐步搭建出一个完整的、可用于生产的 AI Agent 系统。

> 本教程融合 [ryzqi/learn-agent](https://github.com/ryzqi/learn-agent) 与 [shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) 两大教程精华。前者提供深度工程分析与 TypeScript 严格契约,后者提供简洁清晰的渐进式教学结构。本教程取两者之长,以 Python 实现为主,辅以架构图与设计分析,构建一条从直觉到工程的完整学习路径。

---

## 写在前面:你在造的不是 Agent,而是 Harness

在讨论代码之前,先把一件事说清楚。

**Agency -- 感知、推理、行动的能力 -- 来自模型训练,不是来自外部代码的编排。** 但一个能干活的 Agent 产品,需要模型和 Harness 缺一不可。模型是驾驶者,Harness 是载具。本教程教你造载具。

### Agency 从哪来

Agent 的核心是一个神经网络 -- Transformer、一个被训练出来的函数 -- 经过数十亿次梯度更新,在行动序列数据上学会了感知环境、推理目标、采取行动。Agency 这个东西从来不是外面那层代码赋予的,而是模型在训练中学到的。

历史已经写好了铁证:

- **2013 -- DeepMind DQN 玩 Atari。** 一个神经网络,只接收原始像素和游戏分数,学会了 7 款 Atari 2600 游戏。没有游戏专属规则。没有决策树。一个模型,从经验中学习。那个模型就是 Agent。
- **2019 -- OpenAI Five 征服 Dota 2。** 五个神经网络,在 10 个月内与自己对战了 45,000 年的 Dota 2,击败 TI8 世界冠军 OG。没有脚本化的策略。模型完全通过自我对弈学会了团队协作。
- **2024 -- LLM Agent 元年。** Claude 3.5 Sonnet、GPT-4o、Gemini 1.5 -- 大语言模型被部署为编程 Agent。Cursor、Windsurf、Cline 等 AI IDE 兴起,Agent 直接在终端读写文件、执行命令、调试代码。
- **2025 -- Agent 基础设施爆发。** Anthropic 发布 Claude Code,开源 Agent Harness 的工程范式;OpenAI 发布 Codex Agent,支持后台异步编程;Google 发布 Jules,多 Agent 协作修复代码;MCP (Model Context Protocol) 成为工具接入的事实标准。
- **2026 -- Agent 进入生产。** Cursor Agent Mode 成为日常开发工具,GitHub Copilot Workspace 支持跨文件重构,Claude Code 和 Codex 被企业大规模采用。Agent 不再是演示,而是生产力基础设施。SWE-bench 顶级模型解决率超过 70%,Agent 在真实开源项目中的 bug 修复能力达到中级工程师水平。

每一个里程碑都指向同一个事实:**Agency -- 那个感知、推理、行动的能力 -- 是训练出来的,不是编出来的。**

### Agent 不是什么

"Agent" 这个词已经被一整个提示词水管工产业劫持了。

拖拽式工作流构建器、无代码 "AI Agent" 平台、提示词链编排库 -- 它们共享同一个幻觉:把 LLM API 调用用 if-else 分支、节点图、硬编码路由逻辑串在一起就算是 "构建 Agent" 了。

不是的。它们做出来的东西是鲁布·戈德堡机械 -- 一个过度工程化的、脆弱的过程式规则流水线。**提示词水管工式 "Agent" 是不做模型的程序员的意淫。** 你不可能通过工程手段编码出 Agency。Agency 是学出来的,不是编出来的。

### 心智转换:从 "开发 Agent" 到 "开发 Harness"

当一个人说 "我在开发 Agent" 时,他只可能是两个意思之一:

1. **训练模型。** 通过强化学习、微调、RLHF 调整权重。这是 DeepMind、OpenAI、Anthropic 在做的事。
2. **构建 Harness。** 编写代码,为模型提供一个可操作的环境。这是我们大多数人在做的事,也是本教程的核心。

Harness 是 Agent 在特定领域工作所需要的一切:

```
Harness = Tools + Knowledge + Observation + Action Interfaces + Permissions

    Tools:          文件读写、Shell、网络、数据库、浏览器
    Knowledge:      产品文档、领域资料、API 规范、风格指南
    Observation:    git diff、错误日志、浏览器状态、传感器数据
    Action:         CLI 命令、API 调用、UI 交互
    Permissions:    沙箱隔离、审批流程、信任边界
```

模型做决策,Harness 执行。模型做推理,Harness 提供上下文。**模型是驾驶者,Harness 是载具。**

### Harness 工程师到底在做什么

如果你在读这个教程,你很可能是一名 Harness 工程师 -- 这是一个强大的身份。你真正的工作是:

- **实现工具。** 给 Agent 一双手。设计它们时要原子化、可组合、描述清晰。
- **策划知识。** 给 Agent 领域专长。按需加载,不要前置塞入。
- **管理上下文。** 子 Agent 隔离工作、上下文压缩缩短历史、任务系统让目标持久化。
- **控制权限。** 给 Agent 边界。沙箱化文件访问,对破坏性操作要求审批。

**造好 Harness。Agent 会完成剩下的。**

---

## 本教程解决什么问题

模型负责推理和决定下一步;Harness 负责把决定安全地落到真实环境。教程围绕四个核心问题递进:

1. **Agent 如何行动?** 用一个稳定的循环读取模型回复、执行工具、追加结果。
2. **Agent 如何被约束?** 用文件边界、权限策略、Hook 和结构化协议控制副作用。
3. **Agent 如何处理长任务?** 用 TODO、子 Agent、Skill、上下文压缩、记忆、后台任务和 Cron 延长有效工作时间。
4. **多个 Agent 如何协作并接入外部能力?** 用任务认领、Mailbox、协议审批、Worktree 和 MCP 形成可恢复、可审计的协作运行时。

**核心原则:每章只增加一个主要能力,前章行为继续保留。循环本身始终不变。**

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

可以按五个阶段阅读:

| 阶段 | 章节 | 解决的问题 |
| --- | --- | --- |
| **执行基础** | 1-4 | 从循环、工具、文件边界走到权限和 Hook 生命周期 |
| **上下文与知识** | 5-10 | 让 Agent 能规划、委派、按需加载知识、压缩上下文、持久化记忆 |
| **可靠执行** | 11-14 | 处理截断、超长输入、限流、重试、任务依赖、后台作业和定时触发 |
| **多 Agent 协作** | 15-18 | 从消息投递走到协议闭环、去中心化认领和 Git Worktree 并行开发 |
| **动态扩展与总装** | 19-20 | 把外部 MCP 工具安全接入动态工具池,验证完整 Harness |

---

## 20 章地图

| 章 | 主题 | 本章新增的关键能力 |
| ---: | --- | --- |
| 1 | Agent Loop | 一个循环,模型请求、工具结果、继续/结束的最小循环 |
| 2 | 工具与文件 | 注册表、Zod 输入、workspace 安全路径、读写文件 |
| 3 | 权限系统 | 审批、审计、四态权限决定和统一工具错误边界 |
| 4 | Hook 解耦 | UserPromptSubmit、PreToolUse、PostToolUse、Stop 四个生命周期点 |
| 5 | 会话计划 | 完整快照、状态校验、陈旧计划提醒,避免长任务漂移 |
| 6 | 子 Agent | 隔离历史、共享运行边界、禁止递归委派、限制轮数 |
| 7 | Skill 系统 | 先扫描摘要,再按名称加载正文,知识按需进入上下文 |
| 8 | 上下文压缩 | 结果落盘、分层裁剪、摘要恢复上下文预算 |
| 9 | 文件记忆 | 从 canonical history 提取、整理并跨会话检索持久记忆 |
| 10 | 动态上下文 | Provider 按固定顺序生成运行态系统提示,避免复制 Loop |
| 11 | API 韧性 | 重试策略、断路器、速率限制、降级与超时 |
| 12 | 任务引擎 | 5 个工具、3 个状态、DAG 依赖、持久化到磁盘 |
| 13 | 异步操作 | 后台执行、结果轮询、超时保护、事件通知 |
| 14 | Cron 调度 | 定时触发、间隔执行、与任务系统联动 |
| 15 | Inbox 机制 | JSONL 收件箱、append-only、drain-on-read |
| 16 | 协议审批 | 结构化交接、审批闭环、审计日志 |
| 17 | 自治 Agent | 空闲轮询、自动认领、身份重注入、超时关机 |
| 18 | Worktree 隔离 | 任务绑定、目录隔离、事件流、崩溃恢复 |
| 19 | MCP 集成 | 动态工具发现、安全沙箱、协议桥接 |
| 20 | 完整 Harness | 验证前 19 章能力在同一 AgentRunner 中协同工作 |

---

## 快速开始

### 环境要求

- Python 3.10+
- 任意大模型 API 的密钥(OpenAI / DeepSeek / 通义千问 / Claude 等) 

### 安装

```bash
git clone https://github.com/zwt0204/agent-tutorial.git
cd agent-tutorial
pip install openai
```

### 配置 API

创建 `.env` 文件,填入你的 API 信息(支持任何 OpenAI 兼容接口):

```bash
# OpenAI
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o

# 或 DeepSeek
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=deepseek-chat

# 或通义千问
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=qwen-plus

# 或任何 OpenAI 兼容接口
OPENAI_BASE_URL=your-base-url
OPENAI_API_KEY=your-key
OPENAI_MODEL=your-model
```

> **提示**: 大多数国产大模型(DeepSeek、通义、智谱、Moonshot 等)都支持 OpenAI 兼容接口,统一用 `openai` 库即可。

### 运行第 1 章

```bash
python agents/s01_agent_loop.py
# 输入: "列出当前目录的文件"
```

### 运行测试(无需 API Key)

```bash
python3 tests/test_all.py
# === ALL 11 TESTS PASSED ===
```


### 离线阅读

没有 API Key 也可以阅读学习。教程中的架构图、设计分析和伪代码都不依赖网络。

---

## 推荐阅读方式

1. **先读每章的"本章导读"**,明确这一章要证明什么。
2. **从直觉出发**,理解问题场景,再看解决方案。
3. **阅读核心代码**,对照架构图理解数据流。
4. **动手运行实验**,观察实际行为。
5. **对比前后章节**:只找新增能力,以及新增能力为什么不能塞回旧模块。

**想先跑起来再读原理?** 每章末尾都有"试一试"实验,可以直接跳过去动手。

---

## 参考来源与关系

本教程参考以下公开项目的思想、章节组织和工程讨论:

- **[ryzqi/learn-agent](https://github.com/ryzqi/learn-agent)** -- 从零搭建生产级 AI Agent Harness 的 20 章中文教程,以 TypeScript 实现,深度拆解 Claude Code 架构。本教程借鉴其深度工程分析、严格类型契约和 429 个测试的验证体系。
- **[shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code)** -- 累进式 Agent Harness 教程,以 Python 实现,简洁清晰。本教程借鉴其"每课只增加一个机制、最后重新集成"的教学方法和"Harness 工程师"的心智模型。

两份参考项目关注点不同:前者提供更宽的 Agent 原理、上下文、记忆、工具和多 Agent 视野;后者深入 Claude Code 风格 Harness 的内部机制。本教程把两种视角收敛为一条从直觉到工程的完整学习路径。

---

## 许可证与贡献

本教程的文章与代码以仓库实际文件中的声明为准。欢迎在 [GitHub Issues](https://github.com/zwt0204/agent-tutorial/issues) 讨论阅读疑问、架构取舍和改进建议。

改进教程时,建议保持"一章一主题、代码与文章同步、先验证后宣称完成"的节奏。
