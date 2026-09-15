# Chapter 11: API Resilience -- Retry, Circuit Breaker

`s01 > ... > s10 | [ s11 ] > s12 > s13 > s14 > s15 > s16 > s17`

> *"In production, API calls fail"* -- Exponential backoff, circuit breaker, graceful degradation.

---

## Problem

Network timeouts, rate limits, model overload. The Agent needs to survive failures without crashing.

## Solution

```python
class RetryPolicy:
    def get_delay(self, attempt):
        return min(base * (2 ** attempt), max_delay) * random.uniform(0.5, 1.5)

class CircuitBreaker:
    def record_failure(self):
        self.failures += 1
        if self.failures >= threshold: self.state = "open"

    def can_execute(self):
        if self.state == "closed": return True
        if self.state == "open" and time.time() - self.last_failure > recovery:
            self.state = "half-open"; return True
        return False
```

Three states: **closed** (normal) -> **open** (all requests blocked) -> **half-open** (test one request).

## Summary

- Exponential backoff + jitter for retries
- Circuit breaker: closed / open / half-open
- API resilience is essential for production Agents
