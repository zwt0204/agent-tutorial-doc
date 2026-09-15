# Chapter 17: Autonomous Agents -- Self-Organizing

`s01 > ... > s16 > [ s17 ]`

> *"Teammates scan the board, claim unassigned work"* -- No central dispatch needed.

---

## Problem

Manual task assignment doesn't scale. 10 unclaimed tasks need 10 manual assignments.

## Solution

```
WORK -> stop -> IDLE (poll every 5s for 60s)
    |-> inbox message? -> WORK
    |-> unclaimed task? -> claim -> WORK
    |-> timeout -> SHUTDOWN
```

Identity re-injection after compression: if messages <= 3, insert identity block at start.

## Summary

- Idle polling: check inbox + scan task board
- Auto-claim: pending tasks with no owner
- Identity re-injection after compression
- Timeout shutdown after 60s idle
