# Chapter 7: Skill System -- On-Demand Knowledge

`s01 > ... > s06 > [ s07 ] | s08 > s09 > s10 > s11 > s12`

> *"Tell the Agent what exists, let it pull what it needs"*

---

## Problem

System prompts can't hold everything. 100 skill files would dilute the model's attention, making it worse at everything.

## Solution: Two-Step Loading

1. Scan `skills/` directory -> get summary list (a few hundred tokens)
2. Agent calls `load_skill("name")` when needed -> loads full content

```python
class SkillManager:
    def __init__(self):
        self.skills = {}
        for f in SKILLS_DIR.glob("*.md"):
            content = f.read_text(encoding="utf-8")
            self.skills[f.stem] = {"summary": content.split("\n")[0], "path": f}

    def list_skills(self): ...
    def load(self, name): ...
```

## Summary

- Two-step loading: summary first, full content on demand
- Skills live on the filesystem, easy to maintain
- Agent decides when and what to load
