from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentTrace:
    agent_name: str
    status: str  # done|skipped|error
    summary: str
    output: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProspectContext:
    url: str
    domain: str
    rubro: str | None = None
    provincia: str | None = None

    # señales técnicas/comerciales
    analysis: dict[str, Any] = field(default_factory=dict)

    # comercial
    score: int = 0
    classification: str = "LOW"
    recommendations: list[str] = field(default_factory=list)
    proposal: dict[str, Any] = field(default_factory=dict)
    outreach: dict[str, Any] = field(default_factory=dict)
    follow_up: dict[str, Any] = field(default_factory=dict)

    # trazabilidad
    traces: list[AgentTrace] = field(default_factory=list)

    def add_trace(self, trace: AgentTrace):
        self.traces.append(trace)
