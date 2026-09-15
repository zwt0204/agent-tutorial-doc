# 第 14 章:Cron 调度 -- 定时触发任务

`s01 > ... > s13 | [ s14 ] > s15 > s16 > s17`

> *"Agent 需要自己醒来做事"* -- 定时触发、间隔执行、与任务系统联动。
>
> **Harness 层**: 调度 -- 让 Agent 在无人值守时也能工作。

---

## 问题

Agent 只在用户交互时运行。但有些任务需要定期执行:检查更新、清理缓存、生成报告。

## 解决方案

```python
import schedule
from datetime import datetime

class CronScheduler:
    def __init__(self):
        self.jobs = []

    def add_job(self, name: str, interval_minutes: int, fn):
        def job():
            print(f"[{datetime.now()}] Running: {name}")
            fn()
        schedule.every(interval_minutes).minutes.do(job)
        self.jobs.append({"name": name, "interval": interval_minutes})

    def run_pending(self):
        schedule.run_pending()

    def list_jobs(self) -> str:
        lines = ["Scheduled jobs:"]
        for job in self.jobs:
            lines.append(f"- {job['name']}: every {job['interval']}min")
        return "\n".join(lines)

cron = CronScheduler()
```

## 试一试

```bash
python agents/s14_cron.py
```

1. `添加一个每 5 分钟执行的清理任务`
2. `查看所有定时任务`
3. `手动触发一次清理`

## 本章小结

- Cron 调度:定时触发 Agent 行为
- 与任务系统联动:定时创建或更新任务
- 无人值守:Agent 在后台自主工作
