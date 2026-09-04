from corpus_mesh.agents import Adversary, ArithmeticWorker, DeterministicJudge, IndependentVerifier
from corpus_mesh.mesh import CorpusMeshRuntime
from corpus_mesh.models import Task


def test_mesh_recovers_from_primary_worker_failure():
    # Primary always fails; backup never fails; verifier/adversary are perfect.
    mesh = CorpusMeshRuntime(
        workers=[
            ArithmeticWorker("bad", "worker", error_rate=1.0, seed=1),
            ArithmeticWorker("good", "worker", error_rate=0.0, seed=2),
        ],
        verifier=IndependentVerifier("v", "verifier", error_rate=0.0, seed=3),
        adversary=Adversary("a", "adversary", error_rate=0.0, seed=4),
    )
    task = Task("T", "add", {"current": 10, "op": "add", "operand": 5}, skill="arithmetic", risk=0.7)
    trace = mesh.run_step(task, DeterministicJudge.is_correct)
    assert trace.worker_correct is False
    assert trace.recovered is True
    assert trace.final_value == 15
    assert trace.escaped_error is False
