from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from .models import AgentProfile, AgentState, CorpusLink, MeshBlueprint


def default_blueprint() -> MeshBlueprint:
    agents: Dict[str, AgentProfile] = {
        "architect": AgentProfile("architect", "architect", ["planning"], AgentState.ACTIVE),
        "worker_a": AgentProfile("worker_a", "worker", ["arithmetic"], AgentState.ACTIVE),
        "worker_b": AgentProfile("worker_b", "worker", ["arithmetic"], AgentState.ACTIVE),
        "verifier": AgentProfile("verifier", "independent_verifier", ["verification"], AgentState.ACTIVE),
        "adversary": AgentProfile("adversary", "adversary", ["challenge"], AgentState.ACTIVE),
    }
    links = [
        CorpusLink("architect", "worker_a", "task_assignment"),
        CorpusLink("architect", "worker_b", "task_assignment"),
        CorpusLink("worker_a", "verifier", "artifact_verification"),
        CorpusLink("worker_b", "verifier", "artifact_verification"),
        CorpusLink("worker_a", "adversary", "adversarial_review"),
        CorpusLink("worker_b", "adversary", "adversarial_review"),
        CorpusLink("verifier", "architect", "verification_result"),
        CorpusLink("adversary", "architect", "challenge_result"),
    ]
    return MeshBlueprint(
        version="CM-0.1",
        agents=agents,
        links=links,
        constraints={
            "max_agents": 12,
            "self_approval_forbidden": True,
            "objective_evidence_preferred": True,
            "blind_verification": True,
        },
    )


def write_blueprint(path: Path) -> None:
    path.write_text(json.dumps(default_blueprint().to_dict(), indent=2))
