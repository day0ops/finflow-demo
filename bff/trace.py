import time

from models import PolicyEvent, TraceData


class TraceCapture:
    def __init__(self, intent: str) -> None:
        self.intent = intent
        self.agents: list[str] = []
        self.policy_events: list[PolicyEvent] = []
        self.status_code = 200
        self._start = time.monotonic()

    def add_agent(self, name: str) -> None:
        self.agents.append(name)

    def add_policy_event(self, event: PolicyEvent) -> None:
        self.policy_events.append(event)

    def build(self) -> TraceData:
        elapsed = int((time.monotonic() - self._start) * 1000)
        return TraceData(
            intent=self.intent,
            agents=self.agents,
            latency_ms=elapsed,
            status_code=self.status_code,
            policy_events=self.policy_events,
        )
