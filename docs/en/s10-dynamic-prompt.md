# Chapter 10: Dynamic Context -- Modular System Prompts

`s01 > ... > s09 > [ s10 ] > s11 > s12`

> *"System prompts aren't one blob -- they're assembled from multiple Providers"*

---

## Problem

System prompts need workspace info, skill lists, relevant memory. Writing them as a static string means changing code for every update.

## Solution

```python
class DynamicPrompt:
    def __init__(self):
        self.providers = []

    def register(self, name, fn, priority=0):
        self.providers.append({"name": name, "fn": fn, "priority": priority})
        self.providers.sort(key=lambda x: x["priority"])

    def build(self, ctx=None):
        return "\n\n".join(p["fn"](ctx or {}) for p in self.providers)
```

Register providers at different priorities. Runtime assembly. No loop duplication.

## Summary

- DynamicPrompt assembles system prompts from registered providers
- Provider pattern makes context sources pluggable
- Runtime generation avoids copying loop logic
