# Chapter 8: Context Compression -- Unlimited Conversations

`s01 > ... > s07 > [ s08 ] > s09 > s10 > s11 > s12`

> *"Context always fills up; you need a way to make room"* -- Three-layer compression.

---

## Problem

Context windows are finite. Reading 30 files and running 20 commands easily exceeds 100k tokens. Without compression, an Agent can't work in large projects.

## Solution: Three Layers

```
Layer 1: micro_compact (every turn, silent)
  Replace old tool results with "[Previous: used bash]"

Layer 2: auto_compact (token threshold)
  Save transcript to disk, LLM summarizes, replace all messages

Layer 3: manual compact
  Agent calls compact tool explicitly, same as auto_compact
```

## Implementation

```python
def micro_compact(messages):
    # Find old tool_results, replace with placeholder
    for _, _, part in tool_results[:-KEEP_RECENT]:
        if len(part.get("content", "")) > 100:
            part["content"] = "[Previous result truncated]"

def auto_compact(messages):
    # Save full transcript to .transcripts/
    # LLM summarizes, replace messages with summary
    resp = client.chat.completions.create(model=MODEL, messages=[...])
    messages.clear()
    messages.append({"role": "user", "content": f"[Compressed]\n{summary}"})
```

## Summary

- micro_compact: zero-perception, replaces old results silently
- auto_compact: LLM summarizes when tokens exceed threshold
- Full history saved to transcripts for recovery
- Information isn't lost, just moved out of active context
