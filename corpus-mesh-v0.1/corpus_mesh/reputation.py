from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class SkillRecord:
    success: float = 1.0
    failure: float = 1.0

    @property
    def score(self) -> float:
        return self.success / (self.success + self.failure)

    def update(self, correct: bool, weight: float = 1.0) -> None:
        if correct:
            self.success += weight
        else:
            self.failure += weight

    def decay(self, factor: float = 0.995) -> None:
        # Preserve the Beta(1,1) prior while decaying old evidence.
        self.success = 1.0 + (self.success - 1.0) * factor
        self.failure = 1.0 + (self.failure - 1.0) * factor


@dataclass
class ReputationStore:
    records: Dict[str, Dict[str, SkillRecord]] = field(default_factory=dict)

    def _record(self, agent_id: str, skill: str) -> SkillRecord:
        return self.records.setdefault(agent_id, {}).setdefault(skill, SkillRecord())

    def score(self, agent_id: str, skill: str) -> float:
        return self._record(agent_id, skill).score

    def update(self, agent_id: str, skill: str, correct: bool, weight: float = 1.0) -> float:
        rec = self._record(agent_id, skill)
        rec.update(correct, weight)
        return rec.score

    def decay_all(self, factor: float = 0.995) -> None:
        for per_skill in self.records.values():
            for rec in per_skill.values():
                rec.decay(factor)

    def snapshot(self) -> Dict[str, Dict[str, float]]:
        return {
            agent: {skill: rec.score for skill, rec in skills.items()}
            for agent, skills in self.records.items()
        }
