# Chapter 18: Worktree Isolation -- Parallel Execution

`s01 > ... > s17 > [ s18 ]`

> *"Each works in their own directory, no interference"*

---

## Problem

Shared directory. Two Agents editing `config.py` simultaneously -- uncommitted changes pollute each other.

## Solution

```
Control plane (.tasks/)          Execution plane (.worktrees/)
task_1.json                      auth-refactor/
  status: in_progress <------>   branch: wt/auth-refactor
  worktree: "auth-refactor"
```

Tools: `wt_create(name)`, `wt_run(name, cmd)`, `wt_remove(name)`, `wt_list()`.

## Summary

- Directory-per-task isolation
- Task binding: create worktree advances task status
- Event logging for lifecycle tracking
- Crash recovery from disk state
