"""Chapter 11: API resilience - retry, circuit breaker."""
import json, sys, time, random
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from base import get_client, get_model, run_bash, MAX_TURNS

TOOLS = [{"type": "function", "function": {"name": "bash", "description": "Run bash",
    "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}}]


class RetryPolicy:
    def __init__(self, max_retries=3, base_delay=1, max_delay=30):
        self.max_retries, self.base_delay, self.max_delay = max_retries, base_delay, max_delay

    def get_delay(self, attempt):
        return min(self.base_delay * (2 ** attempt), self.max_delay) * random.uniform(0.5, 1.5)


class CircuitBreaker:
    def __init__(self, threshold=5, recovery=60):
        self.failures, self.threshold, self.recovery = 0, threshold, recovery
        self.last_failure, self.state = 0, "closed"

    def record_failure(self):
        self.failures += 1
        self.last_failure = time.time()
        if self.failures >= self.threshold:
            self.state = "open"

    def record_success(self):
        self.failures, self.state = 0, "closed"

    def can_execute(self):
        if self.state == "closed":
            return True
        if self.state == "open" and time.time() - self.last_failure > self.recovery:
            self.state = "half-open"
            return True
        return self.state == "half-open"


retry = RetryPolicy()
breaker = CircuitBreaker()


def resilient_call(messages, **kwargs):
    for attempt in range(retry.max_retries + 1):
        if not breaker.can_execute():
            raise Exception("Circuit breaker open")
        try:
            resp = client.chat.completions.create(model=MODEL, messages=messages, **kwargs)
            breaker.record_success()
            return resp
        except Exception as e:
            breaker.record_failure()
            if attempt == retry.max_retries:
                raise
            delay = retry.get_delay(attempt)
            print(f"[RETRY] {e}, waiting {delay:.1f}s...")
            time.sleep(delay)



def agent_loop(query):
    client = get_client()
    MODEL = get_model()
    messages = [{"role": "user", "content": query}]
    for _ in range(MAX_TURNS):
        resp = resilient_call(messages=messages, tools=TOOLS, max_tokens=8000)
        msg = resp.choices[0].message
        messages.append(msg.model_dump())
        if not msg.tool_calls:
            print(msg.content)
            return
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            output = run_bash(args["command"])
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": output})

if __name__ == "__main__":
    query = input("You: ") if len(sys.argv) < 2 else sys.argv[1]
    agent_loop(query)
