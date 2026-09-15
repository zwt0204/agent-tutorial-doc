# Chapter 15: Inbox -- Async Messaging

`s01 > ... > s14 > [ s15 ] > s16 > s17`

> *"Teammates need to communicate without blocking each other"*

---

## Problem

Multiple Agents need communication: lead assigns tasks, teammates report progress, broadcast system events.

## Solution

```
.team/inbox/
    alice.jsonl   <- append-only, drain-on-read
    bob.jsonl
```

```python
class MessageBus:
    def send(self, sender, to, content): ...
    def read_inbox(self, name): ...  # reads + drains
    def broadcast(self, sender, content): ...
```

## Summary

- JSONL mailbox: append-only, drain-on-read
- send / read_inbox / broadcast
- Async communication doesn't block execution
