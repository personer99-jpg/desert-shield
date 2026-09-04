from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from .models import AgentProfile, AgentState, CorpusLink, MeshBlueprint


class BlueprintController:
    """Mutable controller for the machine-readable Corpus Mesh blueprint.

    Every structural change increments a generation suffix so experiments can
    preserve the exact topology that produced a result.
    """

    def __init__(self, blueprint: MeshBlueprint):
        self.blueprint = blueprint
        self.generation = 0

    def _bump(self) -> None:
        self.generation += 1
        parent = self.blueprint.version
        self.blueprint.parent_version = parent
        root = parent.split("-G")[0]
        self.blueprint.version = f"{root}-G{self.generation}"

    def spawn(self, agent: AgentProfile, links: Iterable[CorpusLink] = ()) -> None:
        max_agents = int(self.blueprint.constraints.get("max_agents", 12))
        active_count = sum(a.state != AgentState.RETIRED for a in self.blueprint.agents.values())
        if active_count >= max_agents:
            raise RuntimeError("max_agents reached")
        if agent.agent_id in self.blueprint.agents and self.blueprint.agents[agent.agent_id].state != AgentState.RETIRED:
            raise ValueError(f"active agent already exists: {agent.agent_id}")
        self.blueprint.agents[agent.agent_id] = agent
        self.blueprint.links.extend(list(links))
        self._bump()

    def retire(self, agent_id: str, reason: str) -> None:
        agent = self.blueprint.agents[agent_id]
        agent.state = AgentState.RETIRED
        agent.metadata["retirement_reason"] = reason
        for link in self.blueprint.links:
            if link.source == agent_id or link.destination == agent_id:
                link.active = False
        self._bump()

    def promote(self, agent_id: str) -> None:
        self.blueprint.agents[agent_id].state = AgentState.HIGH_PERFORMING
        self._bump()

    def probation(self, agent_id: str, reason: str) -> None:
        agent = self.blueprint.agents[agent_id]
        agent.state = AgentState.PROBATION
        agent.metadata["probation_reason"] = reason
        self._bump()
