from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Any, Callable, Dict, Optional

from .models import Claim, Task, VerificationResult


@dataclass
class AgentOutput:
    value: Any
    confidence: float
    evidence: Dict[str, Any]


class Agent:
    def __init__(self, agent_id: str, role: str, error_rate: float = 0.0, seed: Optional[int] = None):
        self.agent_id = agent_id
        self.role = role
        self.error_rate = error_rate
        self.rng = random.Random(seed)

    def execute(self, task: Task, context: Dict[str, Any]) -> AgentOutput:
        raise NotImplementedError


class ArithmeticWorker(Agent):
    """Deterministic synthetic worker used by the v0.1 benchmark.

    It computes the next value in a chain. With probability error_rate it
    returns a perturbed answer, simulating an agent mistake.
    """

    def execute(self, task: Task, context: Dict[str, Any]) -> AgentOutput:
        current = task.payload["current"]
        op = task.payload["op"]
        operand = task.payload["operand"]
        expected = apply_op(current, op, operand)
        value = expected
        injected = False
        if self.rng.random() < self.error_rate:
            value = expected + self.rng.choice([-3, -2, -1, 1, 2, 3])
            injected = True
        # Confidence is intentionally noisy and only weakly calibrated. An
        # error must not advertise itself to a reflection baseline.
        base = 0.90 + self.rng.uniform(-0.10, 0.08)
        if injected:
            base -= self.rng.uniform(0.00, 0.03)
        confidence = max(0.50, min(0.99, base))
        return AgentOutput(value=value, confidence=confidence, evidence={"injected_error": injected})


class IndependentVerifier(Agent):
    def verify(self, task: Task, claim: Claim) -> VerificationResult:
        expected = apply_op(task.payload["current"], task.payload["op"], task.payload["operand"])
        # Simulate an imperfect independent verifier.
        verifier_mistake = self.rng.random() < self.error_rate
        actual_pass = claim.content == expected
        passed = (not actual_pass) if verifier_mistake else actual_pass
        return VerificationResult(
            verifier_id=self.agent_id,
            claim_id=claim.claim_id,
            passed=passed,
            confidence=0.93 if not verifier_mistake else 0.55,
            reason="independent recomputation",
            evidence={"verifier_mistake": verifier_mistake},
        )


class Adversary(Agent):
    def challenge(self, task: Task, claim: Claim) -> VerificationResult:
        expected = apply_op(task.payload["current"], task.payload["op"], task.payload["operand"])
        actual_problem = claim.content != expected
        # Adversary can miss a real problem or make a false accusation.
        mistaken = self.rng.random() < self.error_rate
        detects_problem = (not actual_problem) if mistaken else actual_problem
        # A challenge "passes" when adversary finds no defect.
        return VerificationResult(
            verifier_id=self.agent_id,
            claim_id=claim.claim_id,
            passed=not detects_problem,
            confidence=0.88 if not mistaken else 0.52,
            reason="adversarial challenge",
            evidence={"adversary_mistake": mistaken, "challenged": detects_problem},
        )


class DeterministicJudge:
    """Hidden benchmark oracle. Not available to agents during task execution."""

    @staticmethod
    def expected(task: Task) -> Any:
        return apply_op(task.payload["current"], task.payload["op"], task.payload["operand"])

    @classmethod
    def is_correct(cls, task: Task, value: Any) -> bool:
        return value == cls.expected(task)


def apply_op(current: int, op: str, operand: int) -> int:
    if op == "add":
        return current + operand
    if op == "sub":
        return current - operand
    if op == "mul":
        return current * operand
    if op == "xor":
        return current ^ operand
    raise ValueError(f"unsupported op: {op}")
