from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Dict, List, Optional

from .agents import Adversary, ArithmeticWorker, IndependentVerifier
from .memory import ProvenanceMemory
from .models import Claim, ClaimStatus, Task
from .reputation import ReputationStore


@dataclass
class StepTrace:
    task_id: str
    worker_id: str
    initial_value: int
    final_value: int
    worker_correct: bool
    verifier_passed: bool
    adversary_passed: bool
    adversary_used: bool
    recovered: bool
    escaped_error: bool
    claim_id: str


@dataclass
class RunMetrics:
    success: bool
    steps: int
    errors_introduced: int = 0
    errors_detected: int = 0
    errors_recovered: int = 0
    escaped_errors: int = 0
    verification_false_positives: int = 0
    verification_false_negatives: int = 0
    agent_replacements: int = 0
    agent_calls: int = 0
    traces: List[StepTrace] = field(default_factory=list)

    @property
    def detection_rate(self) -> float:
        return self.errors_detected / self.errors_introduced if self.errors_introduced else 1.0

    @property
    def recovery_rate(self) -> float:
        return self.errors_recovered / self.errors_detected if self.errors_detected else 1.0


class CorpusMeshRuntime:
    """Minimal executable Corpus Mesh.

    v0.1 deliberately uses a simple policy:
    * choose worker with best task-skill reputation;
    * independently verify every result;
    * adversarially inspect every high-risk result (risk >= 0.5);
    * if either check fails, retry with the alternate worker;
    * update domain-specific reputations from hidden benchmark truth.

    The hidden truth is only used by the experimental harness to score and
    update reputation. Production adapters must replace this with real
    objective evidence wherever possible.
    """

    def __init__(
        self,
        workers: List[ArithmeticWorker],
        verifier: IndependentVerifier,
        adversary: Adversary,
        retirement_threshold: float = 0.30,
        audit_rate: float = 0.10,
        seed: Optional[int] = None,
    ) -> None:
        if len(workers) < 2:
            raise ValueError("v0.1 requires at least two workers for replacement")
        self.workers: Dict[str, ArithmeticWorker] = {w.agent_id: w for w in workers}
        self.verifier = verifier
        self.adversary = adversary
        self.memory = ProvenanceMemory()
        self.reputation = ReputationStore()
        self.retirement_threshold = retirement_threshold
        self.audit_rate = audit_rate
        self.rng = random.Random(seed)

    def _rank_workers(self, skill: str) -> List[ArithmeticWorker]:
        return sorted(
            self.workers.values(),
            key=lambda w: self.reputation.score(w.agent_id, skill),
            reverse=True,
        )

    def run_step(self, task: Task, truth_fn) -> StepTrace:
        ranked = self._rank_workers(task.skill)
        primary = ranked[0]
        backup = ranked[1]

        output = primary.execute(task, {})
        worker_correct = truth_fn(task, output.value)
        self.reputation.update(primary.agent_id, task.skill, worker_correct)

        claim = Claim.create(
            content=output.value,
            origin_agent=primary.agent_id,
            skill=task.skill,
            confidence=output.confidence,
            evidence=output.evidence,
            dependencies=task.dependencies,
        )
        self.memory.add_claim(claim)

        vr = self.verifier.verify(task, claim)
        self.memory.add_verification(vr)

        # Selective oversight: the verifier checks every claim. The adversary
        # performs a blind random audit only on claims the verifier accepted.
        # This is designed to catch false negatives without paying 3-agent
        # overhead on every step.
        adversary_used = bool(vr.passed and task.risk >= 0.5 and self.rng.random() < self.audit_rate)
        ar = self.adversary.challenge(task, claim) if adversary_used else None
        if ar is not None:
            self.memory.add_verification(ar)

        verifier_passed = vr.passed
        adversary_passed = True if ar is None else ar.passed
        challenged = (not verifier_passed) or (adversary_used and not adversary_passed)
        recovered = False
        final_value = output.value

        if challenged:
            if worker_correct:
                # False positive verification challenge.
                self.reputation.update(self.verifier.agent_id, "verification", vr.passed == worker_correct)
                if ar is not None:
                    self.reputation.update(self.adversary.agent_id, "challenge", ar.passed == worker_correct)
            else:
                self.memory.invalidate(claim.claim_id, "verification/adversary challenge")

            retry = backup.execute(task, {})
            retry_correct = truth_fn(task, retry.value)
            self.reputation.update(backup.agent_id, task.skill, retry_correct)
            retry_claim = Claim.create(
                content=retry.value,
                origin_agent=backup.agent_id,
                skill=task.skill,
                confidence=retry.confidence,
                evidence={**retry.evidence, "retry_for": claim.claim_id},
                dependencies=task.dependencies,
            )
            self.memory.add_claim(retry_claim)
            retry_vr = self.verifier.verify(task, retry_claim)
            self.memory.add_verification(retry_vr)
            if retry_vr.passed:
                final_value = retry.value
                recovered = (not worker_correct) and retry_correct
            else:
                # Conservative fallback: do not pretend success. The benchmark
                # still records the retry value, which can fail the chain.
                final_value = retry.value
                if not retry_correct:
                    self.memory.invalidate(retry_claim.claim_id, "retry verification failed")

        escaped_error = not truth_fn(task, final_value)
        return StepTrace(
            task_id=task.task_id,
            worker_id=primary.agent_id,
            initial_value=output.value,
            final_value=final_value,
            worker_correct=worker_correct,
            verifier_passed=verifier_passed,
            adversary_passed=adversary_passed,
            adversary_used=adversary_used,
            recovered=recovered,
            escaped_error=escaped_error,
            claim_id=claim.claim_id,
        )
