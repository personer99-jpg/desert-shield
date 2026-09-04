from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, Iterable, List, Set

from .models import Claim, ClaimStatus, VerificationResult


class ProvenanceMemory:
    """Structured claim store with reverse dependency traversal.

    A dependency is another claim id. When a claim is invalidated, every
    downstream claim is marked REVIEW_REQUIRED rather than silently deleted.
    """

    def __init__(self) -> None:
        self.claims: Dict[str, Claim] = {}
        self.dependents: Dict[str, Set[str]] = defaultdict(set)
        self.verifications: Dict[str, List[VerificationResult]] = defaultdict(list)

    def add_claim(self, claim: Claim) -> Claim:
        self.claims[claim.claim_id] = claim
        for parent in claim.dependencies:
            self.dependents[parent].add(claim.claim_id)
        return claim

    def get(self, claim_id: str) -> Claim:
        return self.claims[claim_id]

    def add_verification(self, result: VerificationResult) -> None:
        self.verifications[result.claim_id].append(result)
        claim = self.claims[result.claim_id]
        if result.verifier_id not in claim.verified_by:
            claim.verified_by.append(result.verifier_id)
        if result.passed:
            claim.status = ClaimStatus.CONFIRMED

    def invalidate(self, claim_id: str, reason: str) -> List[str]:
        root = self.claims[claim_id]
        root.status = ClaimStatus.INVALIDATED
        root.invalidated_reason = reason

        affected: List[str] = []
        q = deque([claim_id])
        seen = {claim_id}
        while q:
            current = q.popleft()
            for child in self.dependents.get(current, set()):
                if child in seen:
                    continue
                seen.add(child)
                claim = self.claims[child]
                if claim.status != ClaimStatus.INVALIDATED:
                    claim.status = ClaimStatus.REVIEW_REQUIRED
                affected.append(child)
                q.append(child)
        return affected

    def relevant(self, ids: Iterable[str]) -> List[Claim]:
        return [self.claims[i] for i in ids if i in self.claims]

    def status_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = defaultdict(int)
        for claim in self.claims.values():
            counts[claim.status.value] += 1
        return dict(counts)
