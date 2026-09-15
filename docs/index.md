# AI Agent 工程实战:从零构建生产级 Agent Harness

一套渐进式中文教程,带你从最小的 Agent Loop 开始,逐步搭建出一个完整的、可用于生产的 AI Agent 系统。

> 本教程融合 [ryzqi/learn-agent](https://github.com/ryzqi/learn-agent) 与 [shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) 两大教程精华。前者提供深度工程分析与 TypeScript 严格契约,后者提供简洁清晰的渐进式教学结构。本教程取两者之长,以 Python 实现为主,辅以架构图与设计分析,构建一条从直觉到工程的完整学习路径。

---

## 写在前面:你在造的不是 Agent,而是 Harness

**Agency -- 感知、推理、行动的能力 -- 来自模型训练,不是来自外部代码的编排。** 但一个能干活的 Agent 产品,需要模型和 Harness 缺一不可。模型是驾驶者,Harness 是载具。本教程教你造载具。

### Agency 从哪来

Agent 的核心是一个神经网络 -- Transformer、一个被训练出来的函数 -- 经过数十亿次梯度更新,在行动序列数据上学会了感知环境、推理目标、采取行动。

历史已经写好了铁证:

- **2013 -- DeepMind DQN 玩 Atari。** 一个神经网络,只接收原始像素和游戏分数,学会了 7 款 Atari 2600 游戏。没有游戏专属规则。没有决策树。一个模型,从经验中学习。
- **2019 -- OpenAI Five 征服 Dota 2。** 五个神经网络,在 10 个月内与自己对战了 45,000 年的 Dota 2,击败 TI8 世界冠军 OG。没有脚本化的策略。模型完全通过自我对弈学会了团队协作。
- **2024 -- LLM Agent 元年。** Claude 3.5 Sonnet、GPT-4o、Gemini 1.5 -- 大语言模型被部署为编程 Agent。
- **2025 -- Agent 基础设施爆发。** Anthropic 发布 Claude Code,OpenAI 发布 Codex Agent,MCP 成为工具接入的事实标准。
- **2026 -- Agent 进入生产。** Cursor Agent Mode 成为日常开发工具,GitHub Copilot Workspace 支持跨文件重构,SWE-bench 顶级模型解决率超过 70%。

每一个里程碑都指向同一个事实:**Agency -- 那个感知、推理、行动的能力 -- 是训练出来的,不是编出来的。**

### Agent 不是什么

"Agent" 这个词已经被一整个提示词水管工产业劫持了。拖拽式工作流构建器、无代码 "AI Agent" 平台 -- 它们共享同一个幻觉:把 LLM API 调用用 if-else 分支串在一起就算是 "构建 Agent" 了。不是的。**提示词水管工式 "Agent" 是不做模型的程序员的意淫。** 你不可能通过工程手段编码出 Agency。Agency 是学出来的,不是编出来的。

### 心智转换:从 "开发 Agent" 到 "开发 Harness"

Harness 是 Agent 在特定领域工作所需要的一切:

```
Harness = Tools + Knowledge + Observation + Action Interfaces + Permissions
```

模型做决策,Harness 执行。**模型是驾驶者,Harness 是载具。**

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

| 阶段 | 章节 | 解决的问题 |
| --- | --- | --- |
| **执行基础** | 1-4 | 从循环、工具、文件边界走到权限和 Hook 生命周期 |
| **上下文与知识** | 5-10 | 让 Agent 能规划、委派、按需加载知识、压缩上下文、持久化记忆 |
| **可靠执行** | 11-14 | 处理截断、超长输入、限流、重试、任务依赖、后台作业和定时触发 |
| **多 Agent 协作** | 15-18 | 从消息投递走到协议闭环、去中心化认领和 Git Worktree 并行开发 |
| **动态扩展与总装** | 19-20 | 把外部 MCP 工具安全接入动态工具池,验证完整 Harness |

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

---

## 参考来源

- **[ryzqi/learn-agent](https://github.com/ryzqi/learn-agent)** -- 20 章 TypeScript 深度工程教程
- **[shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code)** -- 12 章 Python 渐进式教程
