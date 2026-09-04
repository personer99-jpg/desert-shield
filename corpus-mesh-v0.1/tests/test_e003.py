"""Unit tests for the CM-E003 real-model harness, driven by a mock adapter."""
import random

import pytest

from corpus_mesh.claude_cli import extract_value
from corpus_mesh.e003 import (
    BudgetExceeded,
    BudgetMeter,
    run_one,
    score_run,
    _fault_plan,
)
from corpus_mesh.e003_tasks import OPS, make_chain, step_prompt

MIX = ["mul3_mod", "add_mul", "rev_add"]


class MockResponse:
    def __init__(self, value, text=""):
        self.value = value
        self.text = text or (f'{{"value": {value}}}' if value is not None else "no answer")
        self.input_tokens = 100
        self.output_tokens = 50
        self.cache_read_tokens = 0
        self.cache_creation_tokens = 0
        self.cost_usd = 0.001
        self.latency_seconds = 0.5
        self.infra_retries = 0
        self.parse_ok = value is not None


class MockAdapter:
    """Scripted model. `script(system, user, call_index)` returns the value."""

    model = "mock-model"

    def __init__(self, script):
        self.script = script
        self.calls = []

    def invoke(self, *, system, user, metadata=None):
        idx = len(self.calls)
        value = self.script(system, user, idx)
        self.calls.append({"system": system, "user": user, "value": value})
        return MockResponse(value)


def _truth_for_prompt(user):
    """Recompute the correct answer from the prompt text alone.

    The mock parses 'Current value: N' and matches the op description against
    a freshly generated chain — instead we cheat: tests keep a side table.
    """
    raise NotImplementedError


def make_oracle(chain):
    """Build a per-step truth lookup keyed by (current, description)."""
    table = {}
    cur = chain.start
    for op in chain.ops:
        table[(cur, op.description)] = op.apply(cur)
        cur = op.apply(cur)
    return table


def perfect_script(chain):
    """A model that always computes correctly, whatever the current state is."""

    def script(system, user, idx):
        current = int(user.split("Current value: ")[1].split(".")[0])
        for op in chain.ops:
            if op.description in user:
                return op.apply(current)
        raise AssertionError(f"prompt does not match any op: {user[:120]}")

    return script


def test_rendered_prompts_have_no_double_braces():
    from corpus_mesh.e003 import (
        REFLECT_USER_SUFFIX,
        RETRY_NOTE,
        VERIFIER_SYSTEM,
        WORKER_SYSTEM,
    )

    rendered = [
        WORKER_SYSTEM.format(persona="worker A"),
        VERIFIER_SYSTEM,
        REFLECT_USER_SUFFIX.format(previous=123),
        RETRY_NOTE,
    ]
    for text in rendered:
        assert "{{" not in text and "}}" not in text
        assert '{"value": <integer>}' in text or "flagged" in text


def test_extract_value_variants():
    assert extract_value('{"value": 42}') == 42
    assert extract_value('working...\n```json\n{"value": -7}\n```') == -7
    assert extract_value('{"value": 3} then revised: {"value": 5}') == 5
    assert extract_value('{"value": "123"}') == 123
    assert extract_value('{"value": 12.0}') == 12
    assert extract_value("no json here") is None
    assert extract_value('{"other": 1}') is None
    assert extract_value('{"value": true}') is None


def test_chain_deterministic_and_bounded():
    c1 = make_chain(50, 123, MIX)
    c2 = make_chain(50, 123, MIX)
    assert c1 == c2
    states = c1.expected_states()
    assert len(states) == 50
    assert all(0 <= s <= 200_000 for s in states)


def test_prompts_contain_no_ground_truth():
    chain = make_chain(20, 5, MIX)
    cur = chain.start
    for op in chain.ops:
        truth = op.apply(cur)
        prompt = step_prompt(cur, op)
        # The prompt is built only from the state and the op parameters.
        assert f"Current value: {cur}." in prompt
        assert op.description in prompt
        params_ok = str(truth) in " ".join(str(v) for v in op.params.values())
        if not params_ok:
            assert str(truth) not in prompt.replace(f"Current value: {cur}.", "")
        cur = truth


def test_all_architectures_succeed_with_perfect_model():
    chain = make_chain(12, 9, MIX)
    for arch in ("single", "reflection", "static_team", "corpus_mesh"):
        adapter = MockAdapter(perfect_script(chain))
        steps, _ = run_one(arch, adapter, chain, seed=1)
        score = score_run(chain, steps)
        assert score["success"], arch
        assert score["escaped_errors"] == 0, arch


def test_no_hidden_oracle_when_verifier_shares_the_error():
    """Definitive leak test: worker AND verifier return the same wrong value.

    With blind verification and no benchmark oracle available to the mesh,
    nothing can detect the error. If any architecture 'detects' here, ground
    truth is leaking into the execution path.
    """
    chain = make_chain(6, 11, MIX)

    def wrong_script(system, user, idx):
        current = int(user.split("Current value: ")[1].split(".")[0])
        for op in chain.ops:
            if op.description in user:
                return op.apply(current) + 1  # consistently wrong, same value
        raise AssertionError("unmatched prompt")

    for arch in ("static_team", "corpus_mesh", "reflection", "single"):
        adapter = MockAdapter(wrong_script)
        steps, _ = run_one(arch, adapter, chain, seed=2)
        score = score_run(chain, steps)
        assert score["errors_detected"] == 0, arch
        assert score["escaped_errors"] == chain.horizon, arch
        assert not score["success"], arch


def test_static_team_detects_and_recovers_single_worker_slip():
    chain = make_chain(8, 21, MIX)
    state = {"worker_calls": 0}

    def script(system, user, idx):
        current = int(user.split("Current value: ")[1].split(".")[0])
        truth = None
        for op in chain.ops:
            if op.description in user:
                truth = op.apply(current)
        assert truth is not None
        if "verifier" in system:
            return truth
        state["worker_calls"] += 1
        # Third worker call is wrong; retries are correct.
        if state["worker_calls"] == 3 and "flagged" not in user:
            return truth + 5
        return truth

    adapter = MockAdapter(script)
    steps, _ = run_one("static_team", adapter, chain, seed=3)
    score = score_run(chain, steps)
    assert score["errors_introduced"] == 1
    assert score["errors_detected"] == 1
    assert score["errors_recovered"] == 1
    assert score["escaped_errors"] == 0
    assert score["success"]


def test_fault_injection_static_repairs_single_does_not():
    chain = make_chain(10, 31, MIX)
    faults = {4: 13}

    adapter = MockAdapter(perfect_script(chain))
    steps, _ = run_one("single", adapter, chain, seed=4, faults=faults)
    score = score_run(chain, steps)
    assert score["fault_outcomes"] == [
        {"step": 4, "detected": False, "contained": False, "repaired": False}
    ]
    assert not score["success"]

    adapter = MockAdapter(perfect_script(chain))
    steps, _ = run_one("static_team", adapter, chain, seed=4, faults=faults)
    score = score_run(chain, steps)
    assert score["fault_outcomes"] == [
        {"step": 4, "detected": True, "contained": True, "repaired": True}
    ]
    assert score["success"]

    adapter = MockAdapter(perfect_script(chain))
    steps, extras = run_one("corpus_mesh", adapter, chain, seed=4, faults=faults)
    score = score_run(chain, steps)
    assert score["fault_outcomes"][0]["detected"]
    assert score["fault_outcomes"][0]["repaired"]
    assert score["success"]


def test_mesh_retry_is_reverified_and_arbitrated():
    chain = make_chain(4, 41, MIX)
    calls = {"n": 0}

    def script(system, user, idx):
        current = int(user.split("Current value: ")[1].split(".")[0])
        truth = None
        for op in chain.ops:
            if op.description in user:
                truth = op.apply(current)
        assert truth is not None
        calls["n"] += 1
        if "verifier" in system:
            return truth
        if "flagged" in user:
            return truth  # retries correct
        # workers always wrong on first attempt
        return truth + 3

    adapter = MockAdapter(script)
    steps, extras = run_one("corpus_mesh", adapter, chain, seed=5)
    score = score_run(chain, steps)
    assert score["errors_introduced"] == chain.horizon
    assert score["errors_detected"] == chain.horizon
    assert score["errors_recovered"] == chain.horizon
    assert score["success"]
    assert all(s.arbitration == "retry_verified" for s in steps)
    assert extras["challenges"] == chain.horizon


def test_budget_meter_raises():
    meter = BudgetMeter(0.01)
    meter.add(0.005)
    with pytest.raises(BudgetExceeded):
        meter.add(0.006)


def test_fault_plan_deterministic_and_interior():
    plan = _fault_plan(12, 3, 99)
    assert plan == _fault_plan(12, 3, 99)
    assert len(plan) == 3
    assert all(1 <= idx <= 10 for idx in plan)
    assert all(off != 0 for off in plan.values())


def test_parse_failure_paths_do_not_crash():
    chain = make_chain(5, 51, MIX)

    def flaky(system, user, idx):
        if idx % 3 == 0:
            return None
        current = int(user.split("Current value: ")[1].split(".")[0])
        for op in chain.ops:
            if op.description in user:
                return op.apply(current)
        raise AssertionError

    for arch in ("single", "reflection", "static_team", "corpus_mesh"):
        adapter = MockAdapter(flaky)
        steps, _ = run_one(arch, adapter, chain, seed=6)
        score = score_run(chain, steps)
        assert isinstance(score["success"], bool)
