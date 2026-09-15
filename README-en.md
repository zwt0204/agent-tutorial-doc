中文 | [English](./README-en.md)

# AI Agent Engineering: Building a Production-Grade Agent Harness from Scratch

A progressive tutorial that takes you from the minimal Agent Loop to a complete, production-ready AI Agent system.

> This tutorial synthesizes the best of [ryzqi/learn-agent](https://github.com/ryzqi/learn-agent) (deep engineering analysis in TypeScript with 429 tests) and [shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) (concise progressive Python teaching). It combines the depth of the former with the clarity of the latter, using Python implementations, architecture diagrams, and design analysis to build a complete learning path from intuition to engineering.

---

## Before We Start: You're Not Building an Agent -- You're Building a Harness

**Agency -- the ability to perceive, reason, and act -- comes from model training, not from external code orchestration.** But a working Agent product requires both a model and a Harness. The model is the driver; the Harness is the vehicle. This tutorial teaches you to build the vehicle.

### Where Agency Comes From

An Agent's core is a neural network -- a Transformer, a function trained through billions of gradient updates on action-sequence data to perceive environments, reason about goals, and take actions. Agency was never bestowed by the code around it; it was learned during training.

History provides the evidence:

- **2013 -- DeepMind DQN plays Atari.** A single neural network, receiving only raw pixels and game scores, learned to play 7 Atari 2600 games. No game-specific rules. No decision trees. One model, learning from experience. That model was the Agent.
- **2019 -- OpenAI Five conquers Dota 2.** Five neural networks played 45,000 years of Dota 2 against themselves in 10 months, defeating TI8 champions OG. No scripted strategies. The models learned teamwork entirely through self-play.
- **2024 -- The LLM Agent year.** Claude 3.5 Sonnet, GPT-4o, Gemini 1.5 -- large language models deployed as coding Agents. AI IDEs like Cursor, Windsurf, and Cline emerged, with Agents reading/writing files, executing commands, and debugging code directly in the terminal.
- **2025 -- Agent infrastructure explosion.** Anthropic released Claude Code, open-sourcing the Agent Harness engineering paradigm; OpenAI released Codex Agent with background async programming; Google released Jules for multi-Agent collaboration; MCP (Model Context Protocol) became the de facto standard for tool integration.
- **2026 -- Agents enter production.** Cursor Agent Mode became a daily development tool, GitHub Copilot Workspace supports cross-file refactoring, Claude Code and Codex adopted at enterprise scale. Agents are no longer demos -- they are productivity infrastructure. Top models solve over 70% of SWE-bench, matching mid-level engineer performance on real open-source bug fixes.

Every milestone points to the same fact: **Agency -- the ability to perceive, reason, and act -- is trained, not coded.**

### What an Agent Is Not

The word "Agent" has been hijacked by an entire prompt-plumbing industry.

Drag-and-drop workflow builders. No-code "AI Agent" platforms. Prompt chain orchestration libraries. They share the same illusion: stringing LLM API calls together with if-else branches, node graphs, and hardcoded routing logic counts as "building an Agent."

It doesn't. What they build is a Rube Goldberg machine -- an over-engineered, fragile, procedural rule pipeline with an LLM wedged in as a glorified text-completion node. **Prompt-plumbing "Agents" are the fantasy of programmers who don't build models.** They try to brute-force intelligence through procedural logic -- massive rule trees, node graphs, prompt-waterfall chains -- then pray enough glue code will somehow produce autonomous behavior. It won't. You cannot engineer Agency. It is learned, not coded.

### Mental Shift: From "Building Agents" to "Building Harnesses"

When someone says "I'm building an Agent," they can only mean one of two things:

1. **Training a model.** Via reinforcement learning, fine-tuning, RLHF, or other gradient-based methods. This is what DeepMind, OpenAI, and Anthropic do.

2. **Building a Harness.** Writing code that provides a model with an operable environment. This is what most of us do, and it's the core of this tutorial.

A Harness is everything an Agent needs to work in a specific domain:

```
Harness = Tools + Knowledge + Observation + Action Interfaces + Permissions

    Tools:          File I/O, Shell, networking, databases, browsers
    Knowledge:      Product docs, domain data, API specs, style guides
    Observation:    Git diffs, error logs, browser state, sensor data
    Action:         CLI commands, API calls, UI interactions
    Permissions:    Sandbox isolation, approval workflows, trust boundaries
```

The model makes decisions. The Harness executes. The model reasons. The Harness provides context. **The model is the driver. The Harness is the vehicle.**

---

## What This Tutorial Solves

The model handles reasoning and deciding the next step; the Harness safely translates decisions into real-world effects. The tutorial progresses through four core questions:

1. **How does an Agent act?** A stable loop reads model replies, executes tools, and appends results.
2. **How is an Agent constrained?** File boundaries, permission policies, hooks, and structured protocols control side effects.
3. **How does an Agent handle long tasks?** TODO, sub-Agents, Skills, context compression, memory, background tasks, and Cron extend effective working time.
4. **How do multiple Agents collaborate and integrate external capabilities?** Task claiming, Mailboxes, protocol approval, Worktrees, and MCP form a recoverable, auditable collaborative runtime.

**Core principle: Each chapter adds exactly one new capability. Previous chapter behavior is preserved. The loop itself never changes.**

---

## Roadmap

```text
Agent Loop
  -> Tools & File Boundaries
  -> Permissions & Hooks
  -> Planning, Sub-Agents, Skills
  -> Artifacts, Context Compression, Cross-Session Memory
  -> Dynamic Prompts, API Resilience, Task DAGs
  -> Background Tasks, Cron
  -> Teammates, Mailbox, Protocol & Plan Approval
  -> SQLite Claiming, Worktree Isolation
  -> MCP Dynamic Tool Pools
  -> Complete Harness
```

Five reading phases:

| Phase | Chapters | Problems Solved |
| --- | --- | --- |
| **Execution Foundation** | 1-4 | Loop, tools, file boundaries, permissions, hooks |
| **Context & Knowledge** | 5-10 | Planning, delegation, on-demand knowledge, compression, memory |
| **Reliable Execution** | 11-14 | Truncation, rate limits, retries, task dependencies, scheduling |
| **Multi-Agent Collaboration** | 15-18 | Message delivery, protocol closure, decentralized claiming, parallel isolation |
| **Dynamic Extension** | 19-20 | MCP tool integration, full harness verification |

---

## Chapter Map

| Ch | Topic | Key New Capability |
| ---: | --- | --- |
| 1 | Agent Loop | Minimal loop: model request, tool results, continue/stop |
| 2 | Tools & Files | Dispatch map, safe paths, read/write/edit |
| 3 | Permissions | 4-state policy, approval, audit logging |
| 4 | Hooks | PreToolUse, PostToolUse, Stop lifecycle callbacks |
| 5 | Session Planning | TODO injection, state tracking |
| 6 | Sub-Agents | Isolated context delegation |
| 7 | Skill System | Scan summaries, load on demand |
| 8 | Context Compression | Micro-compact, auto-compact, transcripts |
| 9 | File Memory | Persistent cross-session recall |
| 10 | Dynamic Context | Provider-based system prompt assembly |
| 11 | API Resilience | Retry, circuit breaker, backoff |
| 12 | Task Engine | DAG with dependencies, disk persistence |
| 13 | Async Tasks | Background execution, result polling |
| 14 | Cron Scheduler | Timed triggers, periodic jobs |
| 15 | Inbox | JSONL mailbox, drain-on-read |
| 16 | Protocols | Structured handoff, approval workflows |
| 17 | Autonomous Agents | Idle polling, auto-claim, identity re-injection |
| 18 | Worktree Isolation | Directory-per-task, event logging |
| 19 | MCP Integration | Dynamic tool discovery, protocol bridging |
| 20 | Complete Harness | Unified runtime verifying all 19 capabilities |

---

## Quick Start

### Requirements

- Python 3.10+
- Any OpenAI-compatible API key (OpenAI / DeepSeek / Qwen / Claude etc.)

### Install

```bash
git clone https://github.com/zwt0204/agent-tutorial.git
cd agent-tutorial
pip install openai
```

### Configure API

Create a `.env` file with your API settings (works with any OpenAI-compatible endpoint):

```bash
# OpenAI
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o

# Or DeepSeek
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=deepseek-chat

# Or Qwen
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=qwen-plus

# Or any OpenAI-compatible endpoint
OPENAI_BASE_URL=your-base-url
OPENAI_API_KEY=your-key
OPENAI_MODEL=your-model
```

> **Note**: Most Chinese LLMs (DeepSeek, Qwen, Zhipu, Moonshot, etc.) support OpenAI-compatible interfaces. Use the `openai` library uniformly.

### Run Chapter 1

```bash
python3 agents/s01_agent_loop.py
# Input: "list files in the current directory"
```

### Run Tests (No API Key Required)

```bash
python3 tests/test_all.py
# === ALL 11 TESTS PASSED ===
```

### Read Offline

No API key needed to read the tutorial. Architecture diagrams, design analysis, and pseudocode work entirely offline.

---

## Recommended Reading Approach

1. **Read each chapter's "Chapter Preview"** to understand what it proves.
2. **Start from intuition** -- understand the problem scenario before the solution.
3. **Read the core code** and trace the data flow against the architecture diagram.
4. **Run the experiments** at the end of each chapter.
5. **Compare with previous chapters** -- identify only the new capability and why it couldn't fit in the old module.

**Want to run first, read later?** Each chapter ends with a "Try It" section you can jump to directly.

---

## References

This tutorial draws on ideas, chapter organization, and engineering discussions from:

- **[ryzqi/learn-agent](https://github.com/ryzqi/learn-agent)** -- A 20-chapter Chinese tutorial on building production-grade Agent Harnesses from scratch, implemented in TypeScript with deep Claude Code architecture analysis. We draw from its deep engineering analysis, strict type contracts, and 429-test verification system.
- **[shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code)** -- A progressive Agent Harness tutorial in Python, concise and clear. We draw from its "one mechanism per lesson, re-integrate at the end" teaching methodology and "Harness Engineer" mental model.

The two reference projects differ in focus: the former provides broader Agent principles, context, memory, tools, and multi-Agent perspectives; the latter dives deep into Claude Code-style Harness internals. This tutorial converges both perspectives into a single learning path from intuition to engineering.

---

## License & Contributions

Articles and code follow the declarations in the repository. Discussion welcome via [GitHub Issues](https://github.com/zwt0204/agent-tutorial/issues).

When improving the tutorial, maintain the rhythm of "one chapter, one topic, code and prose in sync, verify before claiming completion."
