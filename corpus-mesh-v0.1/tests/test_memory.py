from corpus_mesh.memory import ProvenanceMemory
from corpus_mesh.models import Claim, ClaimStatus


def mk(origin, content, deps=None):
    return Claim.create(content, origin, "test", 0.9, {}, deps or [])


def test_invalidation_propagates_downstream():
    m = ProvenanceMemory()
    a = m.add_claim(mk("a", "root"))
    b = m.add_claim(mk("b", "child", [a.claim_id]))
    c = m.add_claim(mk("c", "grandchild", [b.claim_id]))

    affected = m.invalidate(a.claim_id, "bad premise")

    assert a.status == ClaimStatus.INVALIDATED
    assert b.status == ClaimStatus.REVIEW_REQUIRED
    assert c.status == ClaimStatus.REVIEW_REQUIRED
    assert set(affected) == {b.claim_id, c.claim_id}
