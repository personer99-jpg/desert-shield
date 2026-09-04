from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional
import time
import uuid


class AgentState(str, Enum):
    SPAWNED = "spawned"
    PROBATION = "probation"
    ACTIVE = "active"
    HIGH_PERFORMING = "high_performing"
    RETIRED = "retired"


class ClaimStatus(str, Enum):
    PROVISIONAL = "provisional"
    CONFIRMED = "confirmed"
    INVALIDATED = "invalidated"
    REVIEW_REQUIRED = "review_required"


@dataclass
class Task:
    task_id: str
    description: str
    payload: Dict[str, Any]
    skill: str = "general"
    risk: float = 0.5
    dependencies: List[str] = field(default_factory=list)


@dataclass
class AgentProfile:
    agent_id: str
    role: str
    skills: List[str]
    state: AgentState = AgentState.PROBATION
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CorpusLink:
    source: str
    destination: str
    purpose: str
    allowed_types: List[str] = field(default_factory=lambda: ["claim", "evidence", "task"])
    trust_required: float = 0.0
    active: bool = True


@dataclass
class Claim:
    claim_id: str
    content: Any
    origin_agent: str
    skill: str
    confidence: float
    evidence: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    status: ClaimStatus = ClaimStatus.PROVISIONAL
    created_at: float = field(default_factory=time.time)
    verified_by: List[str] = field(default_factory=list)
    invalidated_reason: Optional[str] = None

    @classmethod
    def create(
        cls,
        content: Any,
        origin_agent: str,
        skill: str,
        confidence: float,
        evidence: Dict[str, Any],
        dependencies: Optional[List[str]] = None,
    ) -> "Claim":
        return cls(
            claim_id=f"C-{uuid.uuid4().hex[:10]}",
            content=content,
            origin_agent=origin_agent,
            skill=skill,
            confidence=confidence,
            evidence=evidence,
            dependencies=dependencies or [],
        )


@dataclass
class VerificationResult:
    verifier_id: str
    claim_id: str
    passed: bool
    confidence: float
    reason: str
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MeshBlueprint:
    version: str
    agents: Dict[str, AgentProfile] = field(default_factory=dict)
    links: List[CorpusLink] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    parent_version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        out = asdict(self)
        for agent in out["agents"].values():
            agent["state"] = agent["state"].value if hasattr(agent["state"], "value") else agent["state"]
        return out
