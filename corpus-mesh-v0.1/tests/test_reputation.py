from corpus_mesh.reputation import ReputationStore


def test_domain_specific_reputation_moves_with_verified_outcomes():
    r = ReputationStore()
    start = r.score("agent", "python")
    after_success = r.update("agent", "python", True)
    after_failure = r.update("agent", "python", False, weight=2)

    assert start == 0.5
    assert after_success > start
    assert after_failure < after_success
    assert r.score("agent", "ux") == 0.5
