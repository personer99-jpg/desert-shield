"""CM-E003: matched-model long-horizon reliability experiment.

Four architectures, all served by the SAME underlying Claude model through the
same adapter with identical generation settings:

  single      one worker call per step, its answer is accepted;
  reflection  worker call, then the same model re-checks with its own previous
              answer in context (correlated, non-blind review);
  static_team worker call + blind independent verifier recompute; on
              disagreement one backup-worker retry is accepted (mirrors the
              synthetic static team: retry is NOT re-verified);
  corpus_mesh CM-0.1.1: reputation-routed primary worker, blind verifier on
              every step, selective blind audit of approved steps, challenged
              steps retried by the alternate worker AND re-verified, provenance
              claims with invalidation, majority arbitration when the retry
              also fails verification.

Ground-truth isolation: architecture functions never receive the expected
values. Prompts are built only from the task definition and the evolving
state. All correctness scoring happens post-hoc in `score_run` by replaying
the logged proposals against the deterministic task semantics. Corpus Mesh
reputation updates use verifier agreement only, never benchmark truth.

Fault injection: the harness can corrupt the worker's parsed value at chosen
steps (before any verification sees it), simulating a compromised worker, and
scores whether each architecture detects, contains, and repairs the fault.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import threading
import time
import zlib
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
from statistics import mean
from typing import Any, Callable, Dict, List, Optional, Protocol, Sequence, Tuple

from .e003_tasks import Chain, OpInstance, OPS, make_chain, step_prompt
from .memory import ProvenanceMemory
from .models import Claim
from .reputation import ReputationStore

ARCHITECTURES = ("single", "reflection", "static_team", "corpus_mesh")

WORKER_SYSTEM = (
    "You are {persona}, a worker agent in a long-horizon reliability "
    "experiment. You have no tools and no calculator. Compute the requested "
    "integer operation yourself, carefully. Show your working briefly, then "
    'output the final answer as a JSON object {{"value": <integer>}} on the '
    "last line."
)

VERIFIER_SYSTEM = (
    "You are an independent verifier agent in a long-horizon reliability "
    "experiment. You have no tools and no calculator. Recompute the requested "
    "integer operation from scratch yourself, carefully. Show your working "
    'briefly, then output the final answer as a JSON object '
    '{"value": <integer>} on the last line.'
)

REFLECT_USER_SUFFIX = (
    "\n\nYou answered this task a moment ago with the value {previous}. "
    "Re-check your work by recomputing from scratch. If your previous answer "
    "was wrong, correct it. Output your final answer as a JSON object "
    '{{"value": <integer>}} on the last line.'
)

RETRY_NOTE = (
    "\n\nNote: a previous attempt at this step was flagged by independent "
    "verification as possibly incorrect. Recompute carefully from scratch."
)


class Adapter(Protocol):
    model: str

    def invoke(self, *, system: str, user: str, metadata: Optional[Dict[str, Any]] = None) -> Any: ...


@dataclass
class CallLog:
    role: str
    persona: str
    value: Optional[int]
    latency_s: float
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_creation_tokens: int
    cost_usd: float
    infra_retries: int
    parse_ok: bool
    text_snippet: str = ""


@dataclass
class StepRecord:
    index: int
    current: int
    worker_raw_value: Optional[int]
    worker_value: Optional[int]
    injected: bool
    injected_offset: Optional[int]
    challenged: bool
    challenge_source: Optional[str]
    audit_used: bool
    arbitration: Optional[str]
    accepted: int
    recovery_calls: int
    recovery_seconds: float
    calls: List[CallLog] = field(default_factory=list)


@dataclass
class RunRecord:
    run_key: str
    architecture: str
    horizon: int
    run_idx: int
    chain_seed: int
    steps: List[StepRecord]
    wall_seconds: float
    mesh_extras: Dict[str, Any] = field(default_factory=dict)


class BudgetExceeded(RuntimeError):
    pass


class BudgetMeter:
    """Thread-safe cumulative cost guard shared across all runs."""

    def __init__(self, cap_usd: float) -> None:
        self.cap_usd = cap_usd
        self.spent_usd = 0.0
        self.calls = 0
        self._lock = threading.Lock()

    def add(self, cost: float) -> None:
        with self._lock:
            self.spent_usd += cost
            self.calls += 1
            if self.cap_usd > 0 and self.spent_usd > self.cap_usd:
                raise BudgetExceeded(
                    f"budget cap {self.cap_usd:.2f} USD exceeded ({self.spent_usd:.2f} spent)"
                )


def _call(
    adapter: Adapter,
    budget: Optional[BudgetMeter],
    *,
    role: str,
    persona: str,
    system: str,
    user: str,
) -> Tuple[CallLog, Optional[int]]:
    r = adapter.invoke(system=system, user=user)
    log = CallLog(
        role=role,
        persona=persona,
        value=r.value,
        latency_s=r.latency_seconds,
        input_tokens=r.input_tokens,
        output_tokens=r.output_tokens,
        cache_read_tokens=r.cache_read_tokens,
        cache_creation_tokens=r.cache_creation_tokens,
        cost_usd=r.cost_usd,
        infra_retries=r.infra_retries,
        parse_ok=r.parse_ok,
        text_snippet=(getattr(r, "text", "") or "")[-400:],
    )
    if budget is not None:
        budget.add(r.cost_usd)
    return log, r.value


def _worker(adapter, budget, current: int, op: OpInstance, persona: str, retry: bool = False):
    user = step_prompt(current, op) + (RETRY_NOTE if retry else "")
    return _call(
        adapter, budget,
        role="worker", persona=persona,
        system=WORKER_SYSTEM.format(persona=persona),
        user=user,
    )


def _verifier(adapter, budget, current: int, op: OpInstance, persona: str = "verifier"):
    # Blind verification: the verifier recomputes from scratch and never sees
    # the proposed answer (blueprint constraint blind_verification=true).
    return _call(
        adapter, budget,
        role="verifier", persona=persona,
        system=VERIFIER_SYSTEM,
        user=step_prompt(current, op),
    )


def _first_not_none(*vals: Optional[int], default: int) -> int:
    for v in vals:
        if v is not None:
            return v
    return default


FaultPlan = Dict[int, int]  # step index -> additive offset


def _inject(value: Optional[int], idx: int, faults: FaultPlan) -> Tuple[Optional[int], bool, Optional[int]]:
    if idx in faults and value is not None:
        return value + faults[idx], True, faults[idx]
    return value, False, None


def run_single(adapter, chain: Chain, rng, budget=None, faults: Optional[FaultPlan] = None) -> List[StepRecord]:
    faults = faults or {}
    steps: List[StepRecord] = []
    current = chain.start
    for i, op in enumerate(chain.ops):
        wlog, raw = _worker(adapter, budget, current, op, "a worker agent")
        v, injected, offset = _inject(raw, i, faults)
        accepted = v if v is not None else current
        steps.append(StepRecord(
            index=i, current=current, worker_raw_value=raw, worker_value=v,
            injected=injected, injected_offset=offset,
            challenged=False, challenge_source=None, audit_used=False,
            arbitration=None, accepted=accepted,
            recovery_calls=0, recovery_seconds=0.0, calls=[wlog],
        ))
        current = accepted
    return steps


def run_reflection(adapter, chain: Chain, rng, budget=None, faults: Optional[FaultPlan] = None) -> List[StepRecord]:
    faults = faults or {}
    steps: List[StepRecord] = []
    current = chain.start
    for i, op in enumerate(chain.ops):
        wlog, raw = _worker(adapter, budget, current, op, "a worker agent")
        v, injected, offset = _inject(raw, i, faults)
        shown = v if v is not None else "unknown"
        rlog, rv = _call(
            adapter, budget,
            role="reflector", persona="a worker agent",
            system=WORKER_SYSTEM.format(persona="a worker agent"),
            user=step_prompt(current, op) + REFLECT_USER_SUFFIX.format(previous=shown),
        )
        changed = rv is not None and v is not None and rv != v
        accepted = _first_not_none(rv, v, default=current)
        steps.append(StepRecord(
            index=i, current=current, worker_raw_value=raw, worker_value=v,
            injected=injected, injected_offset=offset,
            challenged=changed, challenge_source="reflection" if changed else None,
            audit_used=False, arbitration=None, accepted=accepted,
            recovery_calls=0, recovery_seconds=0.0, calls=[wlog, rlog],
        ))
        current = accepted
    return steps


def run_static_team(adapter, chain: Chain, rng, budget=None, faults: Optional[FaultPlan] = None) -> List[StepRecord]:
    faults = faults or {}
    steps: List[StepRecord] = []
    current = chain.start
    for i, op in enumerate(chain.ops):
        wlog, raw = _worker(adapter, budget, current, op, "the primary worker")
        v, injected, offset = _inject(raw, i, faults)
        vlog, u = _verifier(adapter, budget, current, op)
        calls = [wlog, vlog]
        challenged = v is None or u is None or u != v
        accepted = v if not challenged else current
        recovery_calls = 0
        recovery_seconds = 0.0
        if challenged:
            blog, bv = _worker(adapter, budget, current, op, "the backup worker", retry=True)
            calls.append(blog)
            recovery_calls = 1
            recovery_seconds = blog.latency_s
            accepted = _first_not_none(bv, u, v, default=current)
        steps.append(StepRecord(
            index=i, current=current, worker_raw_value=raw, worker_value=v,
            injected=injected, injected_offset=offset,
            challenged=challenged, challenge_source="verifier" if challenged else None,
            audit_used=False, arbitration=None, accepted=accepted,
            recovery_calls=recovery_calls, recovery_seconds=recovery_seconds, calls=calls,
        ))
        current = accepted
    return steps


def run_corpus_mesh(
    adapter, chain: Chain, rng, budget=None, faults: Optional[FaultPlan] = None,
    audit_rate: float = 0.10,
) -> Tuple[List[StepRecord], Dict[str, Any]]:
    faults = faults or {}
    steps: List[StepRecord] = []
    current = chain.start
    reputation = ReputationStore()
    memory = ProvenanceMemory()
    personas = ("worker A", "worker B")
    last_primary = personas[0]
    prev_claim_id: Optional[str] = None
    extras = {
        "audits": 0, "audit_catches": 0, "arbitrations": Counter(),
        "primary_switches": 0, "challenges": 0,
    }

    for i, op in enumerate(chain.ops):
        scores = {p: reputation.score(p, "arith") for p in personas}
        if scores[personas[0]] == scores[personas[1]]:
            primary = last_primary
        else:
            primary = max(personas, key=lambda p: scores[p])
        if primary != last_primary:
            extras["primary_switches"] += 1
        backup = personas[1] if primary == personas[0] else personas[0]
        last_primary = primary

        wlog, raw = _worker(adapter, budget, current, op, primary)
        v, injected, offset = _inject(raw, i, faults)
        vlog, u = _verifier(adapter, budget, current, op)
        calls = [wlog, vlog]
        agree = v is not None and u is not None and u == v

        challenge_source: Optional[str] = None
        audit_used = False
        if not agree:
            challenge_source = "verifier"
        elif rng.random() < audit_rate:
            audit_used = True
            extras["audits"] += 1
            alog, a = _verifier(adapter, budget, current, op, persona="auditor")
            calls.append(alog)
            if a is not None and a != v:
                challenge_source = "audit"
                extras["audit_catches"] += 1

        challenged = challenge_source is not None
        reputation.update(primary, "arith", not challenged)

        claim = Claim.create(
            content=v, origin_agent=primary, skill="arith",
            confidence=1.0, evidence={"step": i},
            dependencies=[prev_claim_id] if prev_claim_id else [],
        )
        memory.add_claim(claim)

        arbitration: Optional[str] = None
        accepted = v if v is not None else current
        recovery_calls = 0
        recovery_seconds = 0.0
        if challenged:
            extras["challenges"] += 1
            memory.invalidate(claim.claim_id, f"challenged by {challenge_source}")
            blog, bv = _worker(adapter, budget, current, op, backup, retry=True)
            rvlog, ru = _verifier(adapter, budget, current, op, persona="retry verifier")
            calls.extend([blog, rvlog])
            recovery_calls = 2
            recovery_seconds = blog.latency_s + rvlog.latency_s
            if bv is not None and ru is not None and ru == bv:
                accepted = bv
                arbitration = "retry_verified"
                reputation.update(backup, "arith", True)
            else:
                candidates = [x for x in (v, u, bv, ru) if x is not None]
                counts = Counter(candidates)
                if counts and counts.most_common(1)[0][1] >= 2:
                    accepted = counts.most_common(1)[0][0]
                    arbitration = "majority"
                else:
                    accepted = _first_not_none(ru, bv, u, v, default=current)
                    arbitration = "fallback"
                reputation.update(backup, "arith", bv == accepted)
            retry_claim = Claim.create(
                content=accepted, origin_agent=backup, skill="arith",
                confidence=1.0, evidence={"step": i, "retry_for": claim.claim_id},
                dependencies=[prev_claim_id] if prev_claim_id else [],
            )
            memory.add_claim(retry_claim)
            prev_claim_id = retry_claim.claim_id
            extras["arbitrations"][arbitration] += 1
        else:
            prev_claim_id = claim.claim_id

        steps.append(StepRecord(
            index=i, current=current, worker_raw_value=raw, worker_value=v,
            injected=injected, injected_offset=offset,
            challenged=challenged, challenge_source=challenge_source,
            audit_used=audit_used, arbitration=arbitration, accepted=accepted,
            recovery_calls=recovery_calls, recovery_seconds=recovery_seconds, calls=calls,
        ))
        current = accepted

    extras["arbitrations"] = dict(extras["arbitrations"])
    extras["memory_status"] = memory.status_counts()
    extras["final_reputation"] = reputation.snapshot()
    return steps, extras


def score_run(chain: Chain, steps: Sequence[StepRecord]) -> Dict[str, Any]:
    """Post-hoc deterministic scoring. The only place ground truth is used."""
    cur = chain.start
    introduced = detected = recovered = escaped = parse_failures = 0
    fault_outcomes: List[Dict[str, Any]] = []
    for op, rec in zip(chain.ops, steps):
        truth = op.apply(cur)
        worker_wrong = rec.worker_value != truth
        if worker_wrong:
            introduced += 1
        if rec.challenged and worker_wrong:
            detected += 1
            if rec.accepted == truth:
                recovered += 1
        if rec.accepted != truth:
            escaped += 1
        if rec.worker_value is None:
            parse_failures += 1
        if rec.injected:
            fault_outcomes.append({
                "step": rec.index,
                "detected": rec.challenged,
                "contained": rec.accepted != rec.worker_value,
                "repaired": rec.accepted == truth,
            })
        cur = rec.accepted
    return {
        "success": cur == chain.expected_final,
        "errors_introduced": introduced,
        "errors_detected": detected,
        "errors_recovered": recovered,
        "escaped_errors": escaped,
        "parse_failures": parse_failures,
        "fault_outcomes": fault_outcomes,
    }


def run_one(
    architecture: str,
    adapter,
    chain: Chain,
    seed: int,
    budget=None,
    faults: Optional[FaultPlan] = None,
    audit_rate: float = 0.10,
) -> Tuple[List[StepRecord], Dict[str, Any]]:
    rng = random.Random(seed)
    extras: Dict[str, Any] = {}
    if architecture == "single":
        steps = run_single(adapter, chain, rng, budget, faults)
    elif architecture == "reflection":
        steps = run_reflection(adapter, chain, rng, budget, faults)
    elif architecture == "static_team":
        steps = run_static_team(adapter, chain, rng, budget, faults)
    elif architecture == "corpus_mesh":
        steps, extras = run_corpus_mesh(adapter, chain, rng, budget, faults, audit_rate)
    else:
        raise ValueError(f"unknown architecture: {architecture}")
    return steps, extras


# ---------------------------------------------------------------------------
# Experiment driver
# ---------------------------------------------------------------------------

def _fault_plan(horizon: int, n_faults: int, seed: int) -> FaultPlan:
    if n_faults <= 0:
        return {}
    rng = random.Random(seed)
    interior = list(range(1, horizon - 1)) or [0]
    positions = sorted(rng.sample(interior, min(n_faults, len(interior))))
    offsets = [rng.choice([7, -7, 13, -13, 101, -101]) for _ in positions]
    return dict(zip(positions, offsets))


def _row_from_run(rr: RunRecord, chain: Chain) -> Dict[str, Any]:
    score = score_run(chain, rr.steps)
    calls = sum(len(s.calls) for s in rr.steps)
    row = {
        "run_key": rr.run_key,
        "architecture": rr.architecture,
        "horizon": rr.horizon,
        "run_idx": rr.run_idx,
        "chain_seed": rr.chain_seed,
        "success": int(score["success"]),
        "errors_introduced": score["errors_introduced"],
        "errors_detected": score["errors_detected"],
        "errors_recovered": score["errors_recovered"],
        "escaped_errors": score["escaped_errors"],
        "parse_failures": score["parse_failures"],
        "model_calls": calls,
        "input_tokens": sum(c.input_tokens for s in rr.steps for c in s.calls),
        "output_tokens": sum(c.output_tokens for s in rr.steps for c in s.calls),
        "cache_read_tokens": sum(c.cache_read_tokens for s in rr.steps for c in s.calls),
        "cost_usd": round(sum(c.cost_usd for s in rr.steps for c in s.calls), 6),
        "wall_seconds": round(rr.wall_seconds, 2),
        "challenges": sum(1 for s in rr.steps if s.challenged),
        "recovery_calls": sum(s.recovery_calls for s in rr.steps),
        "recovery_seconds": round(sum(s.recovery_seconds for s in rr.steps), 2),
        "mean_recovery_latency_s": round(
            mean([s.recovery_seconds for s in rr.steps if s.recovery_calls]), 2
        ) if any(s.recovery_calls for s in rr.steps) else 0.0,
        "injected_faults": sum(1 for s in rr.steps if s.injected),
        "faults_detected": sum(1 for f in score["fault_outcomes"] if f["detected"]),
        "faults_contained": sum(1 for f in score["fault_outcomes"] if f["contained"]),
        "faults_repaired": sum(1 for f in score["fault_outcomes"] if f["repaired"]),
        "infra_retries": sum(c.infra_retries for s in rr.steps for c in s.calls),
        "mesh_extras": rr.mesh_extras,
        "fault_outcomes": score["fault_outcomes"],
    }
    return row


def _wilson(successes: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = successes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def aggregate(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    keys = sorted({(r["architecture"], r["horizon"]) for r in rows})
    for arch, horizon in keys:
        group = [r for r in rows if r["architecture"] == arch and r["horizon"] == horizon]
        n = len(group)
        wins = sum(r["success"] for r in group)
        total_steps = n * horizon
        escaped_steps = sum(r["escaped_errors"] for r in group)
        lo, hi = _wilson(wins, n)
        slo, shi = _wilson(escaped_steps, total_steps)
        out.append({
            "architecture": arch,
            "horizon": horizon,
            "runs": n,
            "success_rate": round(wins / n, 4) if n else 0,
            "success_ci_low": round(lo, 4),
            "success_ci_high": round(hi, 4),
            "step_escape_rate": round(escaped_steps / total_steps, 5) if total_steps else 0,
            "step_escape_ci_low": round(slo, 5),
            "step_escape_ci_high": round(shi, 5),
            "avg_errors_introduced": round(mean(r["errors_introduced"] for r in group), 3),
            "avg_errors_detected": round(mean(r["errors_detected"] for r in group), 3),
            "avg_errors_recovered": round(mean(r["errors_recovered"] for r in group), 3),
            "avg_escaped_errors": round(mean(r["escaped_errors"] for r in group), 3),
            "avg_model_calls": round(mean(r["model_calls"] for r in group), 2),
            "avg_input_tokens": round(mean(r["input_tokens"] for r in group), 1),
            "avg_output_tokens": round(mean(r["output_tokens"] for r in group), 1),
            "avg_cost_usd": round(mean(r["cost_usd"] for r in group), 5),
            "avg_wall_seconds": round(mean(r["wall_seconds"] for r in group), 1),
            "avg_recovery_latency_s": round(
                mean([r["mean_recovery_latency_s"] for r in group if r["recovery_calls"]]), 2
            ) if any(r["recovery_calls"] for r in group) else 0.0,
            "cost_per_success_usd": round(
                sum(r["cost_usd"] for r in group) / wins, 5
            ) if wins else None,
        })
    return out


def fit_decay(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Two lambda estimators per architecture.

    run_level: least-squares slope of log(success_rate) vs horizon (the CM-E001
    estimator; requires success_rate > 0 at every included horizon).
    step_level: -ln(1 - per-step escape rate) pooled over all steps, which uses
    every step as a Bernoulli trial and is far more sample-efficient.
    Bootstrap CIs resample runs with replacement.
    """
    result: Dict[str, Any] = {}
    boot_rng = random.Random(1234)
    for arch in sorted({r["architecture"] for r in rows}):
        group = [r for r in rows if r["architecture"] == arch]

        def _run_level(sample: List[Dict[str, Any]]) -> Optional[float]:
            by_h: Dict[int, List[int]] = {}
            for r in sample:
                by_h.setdefault(r["horizon"], []).append(r["success"])
            pts = [(h, mean(v)) for h, v in by_h.items() if mean(v) > 0]
            if len(pts) < 2:
                return None
            xs = [p[0] for p in pts]
            ys = [math.log(p[1]) for p in pts]
            xbar, ybar = mean(xs), mean(ys)
            denom = sum((x - xbar) ** 2 for x in xs)
            if not denom:
                return None
            return max(0.0, -sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / denom)

        def _step_level(sample: List[Dict[str, Any]]) -> Optional[float]:
            steps = sum(r["horizon"] for r in sample)
            escaped = sum(r["escaped_errors"] for r in sample)
            if not steps:
                return None
            rate = min(escaped / steps, 0.999)
            return -math.log(1 - rate)

        boots_run, boots_step = [], []
        for _ in range(2000):
            sample = [group[boot_rng.randrange(len(group))] for _ in group]
            b1, b2 = _run_level(sample), _step_level(sample)
            if b1 is not None:
                boots_run.append(b1)
            if b2 is not None:
                boots_step.append(b2)

        def _ci(vals: List[float]) -> Optional[List[float]]:
            if len(vals) < 100:
                return None
            vals = sorted(vals)
            return [round(vals[int(0.025 * len(vals))], 6), round(vals[int(0.975 * len(vals))], 6)]

        rl, sl = _run_level(group), _step_level(group)
        result[arch] = {
            "lambda_run_level": round(rl, 6) if rl is not None else None,
            "lambda_run_level_ci95": _ci(boots_run),
            "lambda_step_level": round(sl, 6) if sl is not None else None,
            "lambda_step_level_ci95": _ci(boots_step),
        }
    return result


def _steplog(rr: RunRecord) -> Dict[str, Any]:
    return {
        "run_key": rr.run_key,
        "architecture": rr.architecture,
        "horizon": rr.horizon,
        "chain_seed": rr.chain_seed,
        "steps": [
            {
                **{k: v for k, v in asdict(s).items() if k != "calls"},
                "calls": [asdict(c) for c in s.calls],
            }
            for s in rr.steps
        ],
        "mesh_extras": rr.mesh_extras,
    }


def run_experiment(
    adapter,
    out_dir: Path,
    horizons: Sequence[int],
    runs: int,
    seed_base: int,
    op_mix: Sequence[str],
    architectures: Sequence[str] = ARCHITECTURES,
    audit_rate: float = 0.10,
    n_faults: int = 0,
    max_workers: int = 6,
    budget_cap_usd: float = 0.0,
) -> List[Dict[str, Any]]:
    from concurrent.futures import ThreadPoolExecutor, as_completed

    out_dir.mkdir(parents=True, exist_ok=True)
    config = {
        "model": getattr(adapter, "model", "?"),
        "horizons": list(horizons),
        "runs": runs,
        "seed_base": seed_base,
        "op_mix": list(op_mix),
        "architectures": list(architectures),
        "audit_rate": audit_rate,
        "n_faults": n_faults,
        "budget_cap_usd": budget_cap_usd,
        "thinking": "disabled (MAX_THINKING_TOKENS=0) for all architectures",
    }
    cfg_path = out_dir / "config.json"
    if cfg_path.exists():
        prior = json.loads(cfg_path.read_text())
        for key in ("model", "seed_base", "op_mix", "audit_rate", "n_faults"):
            if prior.get(key) != config[key]:
                raise SystemExit(
                    f"resume mismatch in {cfg_path}: {key} was {prior.get(key)!r}, now {config[key]!r}. "
                    "Use a fresh --out directory."
                )
    cfg_path.write_text(json.dumps(config, indent=2))

    runs_path = out_dir / "runs.jsonl"
    done = set()
    rows: List[Dict[str, Any]] = []
    if runs_path.exists():
        for line in runs_path.read_text().splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue  # partial line from an interrupted writer; re-run that job
            if row["run_key"] in done:
                continue  # duplicate append from an interrupted writer
            done.add(row["run_key"])
            rows.append(row)

    jobs = []
    for horizon in horizons:
        for run_idx in range(runs):
            chain_seed = seed_base + horizon * 1000 + run_idx
            for arch in architectures:
                run_key = f"{arch}-h{horizon}-r{run_idx}"
                if run_key in done:
                    continue
                jobs.append((arch, horizon, run_idx, chain_seed, run_key))

    budget = BudgetMeter(budget_cap_usd)
    lock = threading.Lock()
    steps_path = out_dir / "steps.jsonl"

    def _job(arch, horizon, run_idx, chain_seed, run_key):
        chain = make_chain(horizon, chain_seed, op_mix)
        faults = _fault_plan(horizon, n_faults, chain_seed + 77) if n_faults else {}
        started = time.perf_counter()
        steps, extras = run_one(
            arch, adapter, chain, seed=chain_seed + zlib.crc32(arch.encode()) % 100000,
            budget=budget, faults=faults, audit_rate=audit_rate,
        )
        rr = RunRecord(
            run_key=run_key, architecture=arch, horizon=horizon, run_idx=run_idx,
            chain_seed=chain_seed, steps=steps,
            wall_seconds=time.perf_counter() - started, mesh_extras=extras,
        )
        row = _row_from_run(rr, chain)
        with lock:
            with runs_path.open("a") as f:
                f.write(json.dumps(row) + "\n")
            with steps_path.open("a") as f:
                f.write(json.dumps(_steplog(rr)) + "\n")
        return row

    failures: List[Dict[str, str]] = []
    print(f"CM-E003: {len(jobs)} runs to execute ({len(done)} already complete)")
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futs = {pool.submit(_job, *j): j for j in jobs}
        for fut in as_completed(futs):
            j = futs[fut]
            try:
                row = fut.result()
                rows.append(row)
                print(json.dumps({k: row[k] for k in (
                    "run_key", "success", "escaped_errors", "errors_detected",
                    "model_calls", "cost_usd")}))
            except BudgetExceeded as exc:
                failures.append({"run_key": j[4], "error": str(exc)})
                print(f"ABORTED {j[4]}: {exc}")
            except Exception as exc:  # noqa: BLE001 - record and continue
                failures.append({"run_key": j[4], "error": repr(exc)})
                print(f"FAILED {j[4]}: {exc!r}")
    if failures:
        with (out_dir / "failures.jsonl").open("a") as f:
            for fail in failures:
                f.write(json.dumps(fail) + "\n")

    write_analysis(out_dir, rows)
    print(f"total spent this invocation: ${budget.spent_usd:.2f} across {budget.calls} calls")
    return rows


def write_analysis(out_dir: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    summary = aggregate(rows)
    decay = fit_decay(rows)
    flat = [{k: v for k, v in r.items() if k not in ("mesh_extras", "fault_outcomes")} for r in rows]
    with (out_dir / "runs.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(flat[0].keys()))
        w.writeheader()
        w.writerows(flat)
    with (out_dir / "summary.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        w.writeheader()
        w.writerows(summary)
    (out_dir / "decay.json").write_text(json.dumps(decay, indent=2))
    print("\nSUMMARY")
    for r in summary:
        print(json.dumps(r))
    print("\nDECAY")
    print(json.dumps(decay, indent=2))


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------

def calibrate(adapter, out_path: Path, samples: int, seed: int, ops: Sequence[str]) -> None:
    """Measure the model's raw per-op error rate with single worker calls.

    Uses calibration-only seeds; results choose the op mix for the main run.
    """
    rng = random.Random(seed)
    report: Dict[str, Any] = {"model": getattr(adapter, "model", "?"), "samples": samples, "ops": {}}
    for name in ops:
        op_type = OPS[name]
        wrong = 0
        parse_fail = 0
        costs, lats = [], []
        for _ in range(samples):
            current = rng.randint(1000, 9999)
            inst = op_type.instance(rng)
            truth = inst.apply(current)
            r = adapter.invoke(
                system=WORKER_SYSTEM.format(persona="a worker agent"),
                user=step_prompt(current, inst),
            )
            costs.append(r.cost_usd)
            lats.append(r.latency_seconds)
            if r.value is None:
                parse_fail += 1
                wrong += 1
            elif r.value != truth:
                wrong += 1
        lo, hi = _wilson(wrong, samples)
        report["ops"][name] = {
            "error_rate": round(wrong / samples, 3),
            "ci95": [round(lo, 3), round(hi, 3)],
            "parse_failures": parse_fail,
            "avg_cost_usd": round(mean(costs), 5),
            "avg_latency_s": round(mean(lats), 2),
        }
        print(f"{name}: error {wrong}/{samples} = {wrong/samples:.1%}  "
              f"(cost ~${mean(costs):.4f}/call, {mean(lats):.1f}s/call)")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))


class OpenAICompatShim:
    """Adapts the OpenAI-compatible HTTP adapter to the CM-E003 call contract,
    so the same experiment can run against local/self-hosted models."""

    def __init__(self, *, endpoint: str, model: str) -> None:
        import os

        from .claude_cli import extract_value
        from .model_adapter import OpenAICompatibleHTTPAdapter

        api_key = os.environ.get("CM_MODEL_API_KEY", "")
        if not api_key:
            raise SystemExit("--endpoint requires CM_MODEL_API_KEY (any non-empty string for most local servers)")
        self._inner = OpenAICompatibleHTTPAdapter(endpoint=endpoint, api_key=api_key, model=model)
        self._extract = extract_value
        self.model = model
        self.name = self._inner.name

    def invoke(self, *, system: str, user: str, metadata: Optional[Dict[str, Any]] = None):
        from .claude_cli import CallResult

        r = self._inner.invoke(system=system, user=user)
        value = r.structured.get("value") if isinstance(r.structured.get("value"), int) else None
        if value is None:
            value = self._extract(r.content)
        return CallResult(
            text=r.content, value=value,
            input_tokens=r.input_tokens, output_tokens=r.output_tokens,
            cache_read_tokens=0, cache_creation_tokens=0,
            cost_usd=r.cost_usd, latency_seconds=r.latency_seconds,
            model=self.model, infra_retries=0, parse_ok=value is not None,
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(description="CM-E003 matched-model long-horizon experiment")
    sub = p.add_subparsers(dest="cmd", required=True)

    def _common(sp):
        sp.add_argument("--model", default="claude-haiku-4-5-20251001")
        sp.add_argument("--claude-bin", default="claude")
        sp.add_argument(
            "--endpoint",
            default=None,
            help="OpenAI-compatible chat-completions URL (e.g. a local vLLM/"
                 "Ollama server). When set, uses CM_MODEL_API_KEY instead of "
                 "the Claude CLI.",
        )

    c = sub.add_parser("calibrate", help="measure raw per-op error rates")
    _common(c)
    c.add_argument("--samples", type=int, default=12)
    c.add_argument("--seed", type=int, default=900001)
    c.add_argument("--ops", nargs="+", default=list(OPS.keys()))
    c.add_argument("--out", type=Path, default=Path("results/CM-E003/calibration.json"))

    r = sub.add_parser("run", help="run the experiment")
    _common(r)
    r.add_argument("--horizons", nargs="+", type=int, default=[5, 10, 20])
    r.add_argument("--runs", type=int, default=2)
    r.add_argument("--seed-base", type=int, default=20260904)
    r.add_argument("--op-mix", nargs="+", default=["mul3_mod", "add_mul", "rev_add"])
    r.add_argument("--architectures", nargs="+", default=list(ARCHITECTURES))
    r.add_argument("--audit-rate", type=float, default=0.10)
    r.add_argument("--n-faults", type=int, default=0)
    r.add_argument("--max-workers", type=int, default=6)
    r.add_argument("--budget-cap-usd", type=float, default=25.0)
    r.add_argument("--out", type=Path, required=True)

    a = sub.add_parser("analyze", help="recompute summary from an out dir")
    a.add_argument("--out", type=Path, required=True)

    args = p.parse_args()

    if args.cmd == "analyze":
        rows, seen = [], set()
        for line in (args.out / "runs.jsonl").read_text().splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row["run_key"] in seen:
                continue
            seen.add(row["run_key"])
            rows.append(row)
        write_analysis(args.out, rows)
        return

    if args.endpoint:
        adapter = OpenAICompatShim(endpoint=args.endpoint, model=args.model)
    else:
        from .claude_cli import ClaudeCLIAdapter
        adapter = ClaudeCLIAdapter(model=args.model, claude_bin=args.claude_bin)

    if args.cmd == "calibrate":
        calibrate(adapter, args.out, args.samples, args.seed, args.ops)
    elif args.cmd == "run":
        run_experiment(
            adapter,
            out_dir=args.out,
            horizons=args.horizons,
            runs=args.runs,
            seed_base=args.seed_base,
            op_mix=args.op_mix,
            architectures=args.architectures,
            audit_rate=args.audit_rate,
            n_faults=args.n_faults,
            max_workers=args.max_workers,
            budget_cap_usd=args.budget_cap_usd,
        )


if __name__ == "__main__":
    main()
