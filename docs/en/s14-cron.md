# Chapter 14: Cron Scheduler -- Timed Triggers

`s01 > ... > s13 | [ s14 ] > s15 > s16 > s17`

> *"Agents need to wake up and work on their own"*

---

## Problem

Agents only run during user interaction. Some tasks need periodic execution: check updates, clean cache, generate reports.

## Solution

```python
class CronScheduler:
    def add_job(self, name, interval_minutes, fn):
        schedule.every(interval_minutes).minutes.do(fn)
```

Tools: `cron_add(name, interval, command)`, `cron_list()`. Jobs run in daemon threads.

## Summary

- Cron triggers Agent behavior on schedule
- Integrates with task system
- Works unattended in background
