# 第 11 章:API 韧性 -- 决定 Agent 商业化成败的隐藏细节

`s01 > ... > s10 | [ s11 ] > s12 > s13 > s14 > s15 > s16 > s17`

> *"生产环境中,API 调用会失败"* -- 重试、断路器、降级。
>
> **Harness 层**: 韧性 -- 让 Agent 在故障中存活。

---

## 问题

生产环境中,API 调用会失败:网络超时、速率限制、模型过载。Agent 需要优雅地处理这些故障,而不是直接崩溃。

## 解决方案

```python
import time, random

class RetryPolicy:
    def __init__(self, max_retries=3, base_delay=1, max_delay=30):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    def get_delay(self, attempt: int) -> float:
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        return delay * random.uniform(0.5, 1.5)

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = 0
        self.state = "closed"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"

    def record_success(self):
        self.failure_count = 0
        self.state = "closed"

    def can_execute(self) -> bool:
        if self.state == "closed":
            return True
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
                return True
            return False
        return True

def resilient_api_call(messages, **kwargs):
    for attempt in range(retry_policy.max_retries + 1):
        if not circuit_breaker.can_execute():
            raise Exception("Circuit breaker is open")
        try:
            response = client.messages.create(model=MODEL, messages=messages, **kwargs)
            circuit_breaker.record_success()
            return response
        except anthropic.RateLimitError:
            delay = retry_policy.get_delay(attempt)
            time.sleep(delay)
        except anthropic.APIError as e:
            circuit_breaker.record_failure()
            if attempt == retry_policy.max_retries:
                raise
            time.sleep(retry_policy.get_delay(attempt))
```

## 核心概念

- **指数退避 + 抖动**:重试间隔指数增长,加随机抖动避免雪崩
- **断路器**:连续失败超过阈值,短路所有请求,定期尝试恢复
- **半开放状态**:断路器定期放行一个请求,成功则关闭,失败则重新打开

## 试一试

```bash
python agents/s11_api_resilience.py
```

模拟限流场景,观察重试和断路器行为。

## 本章小结

- 重试策略:指数退避 + 抖动
- 断路器:closed / open / half-open 三态
- API 韧性是生产级 Agent 的必备能力
