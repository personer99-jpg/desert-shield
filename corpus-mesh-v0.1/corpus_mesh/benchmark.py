from __future__ import annotations

import argparse
import csv
import json
import math
import random
from dataclasses import asdict
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Tuple

from .agents import Adversary, ArithmeticWorker, DeterministicJudge, IndependentVerifier, apply_op
from .mesh import CorpusMeshRuntime, RunMetrics
from .models import Task


OPS = ("add", "sub", "xor")


def make_chain(horizon: int, seed: int) -> Tuple[int, List[Task], int]:
    rng = random.Random(seed)
    start = rng.randint(5, 40)
    current = start
    tasks: List[Task] = []
    for i in range(horizon):
        op = rng.choice(OPS)
        operand = rng.randint(1, 15)
        task = Task(
            task_id=f"T-{i:04d}",
            description=f"Apply {op} {operand}",
            payload={"current": current, "op": op, "operand": operand},
            skill="arithmetic",
            risk=0.7,
            dependencies=[tasks[-1].task_id] if tasks else [],
        )
        tasks.append(task)
        current = apply_op(current, op, operand)
    return start, tasks, current


def run_single_agent(horizon: int, seed: int, worker_error: float) -> RunMetrics:
    _, tasks, expected_final = make_chain(horizon, seed)
    worker = ArithmeticWorker("single", "worker", error_rate=worker_error, seed=seed + 101)
    current = tasks[0].payload["current"] if tasks else 0
    introduced = 0
    escaped = 0
    for task in tasks:
        # The evolving current state is whatever the agent produced last time.
        task.payload["current"] = current
        out = worker.execute(task, {})
        if out.evidence.get("injected_error"):
            introduced += 1
        current = out.value
        # Once an error changes state, subsequent hidden expected values diverge;
        # scoring is therefore done against the original chain final state.
    success = current == expected_final
    escaped = 0 if success else 1
    return RunMetrics(
        success=success,
        steps=horizon,
        errors_introduced=introduced,
        errors_detected=0,
        errors_recovered=0,
        escaped_errors=escaped,
        agent_calls=horizon,
    )


def run_reflection_agent(horizon: int, seed: int, worker_error: float) -> RunMetrics:
    _, tasks, expected_final = make_chain(horizon, seed)
    worker = ArithmeticWorker("reflector", "worker", error_rate=worker_error, seed=seed + 201)
    # Self-reflection is correlated: second pass uses the same worker and only
    # happens for low-confidence outputs.
    current = tasks[0].payload["current"] if tasks else 0
    introduced = detected = recovered = 0
    calls = 0
    for task in tasks:
        task.payload["current"] = current
        out = worker.execute(task, {})
        calls += 1
        if out.evidence.get("injected_error"):
            introduced += 1
        if out.confidence < 0.85:
            detected += 1
            retry = worker.execute(task, {})
            calls += 1
            if DeterministicJudge.is_correct(task, retry.value):
                recovered += 1
            out = retry
        current = out.value
    success = current == expected_final
    return RunMetrics(
        success=success,
        steps=horizon,
        errors_introduced=introduced,
        errors_detected=detected,
        errors_recovered=recovered,
        escaped_errors=0 if success else 1,
        agent_calls=calls,
    )


def run_static_team(
    horizon: int,
    seed: int,
    worker_error: float,
    verifier_error: float,
) -> RunMetrics:
    """Fixed worker+verifier team with retry, but no adversary, reputation,
    provenance dependency recovery, or dynamic routing.
    """
    _, tasks, expected_final = make_chain(horizon, seed)
    primary = ArithmeticWorker("static_worker", "worker", error_rate=worker_error, seed=seed + 251)
    backup = ArithmeticWorker("static_backup", "worker", error_rate=worker_error, seed=seed + 252)
    verifier = IndependentVerifier("static_verifier", "verifier", error_rate=verifier_error, seed=seed + 253)
    current = tasks[0].payload["current"] if tasks else 0
    m = RunMetrics(success=False, steps=horizon)
    for task in tasks:
        task.payload["current"] = current
        out = primary.execute(task, {})
        m.agent_calls += 1
        primary_correct = DeterministicJudge.is_correct(task, out.value)
        if not primary_correct:
            m.errors_introduced += 1
        from .models import Claim
        claim = Claim.create(out.value, primary.agent_id, task.skill, out.confidence, out.evidence)
        vr = verifier.verify(task, claim)
        m.agent_calls += 1
        if not vr.passed and not primary_correct:
            m.errors_detected += 1
        final = out.value
        if not vr.passed:
            retry = backup.execute(task, {})
            m.agent_calls += 1
            final = retry.value
            if (not primary_correct) and DeterministicJudge.is_correct(task, retry.value):
                m.errors_recovered += 1
        if not DeterministicJudge.is_correct(task, final):
            m.escaped_errors += 1
        current = final
    m.success = current == expected_final
    return m


def run_corpus_mesh(
    horizon: int,
    seed: int,
    worker_error: float,
    verifier_error: float,
    adversary_error: float,
) -> RunMetrics:
    _, tasks, expected_final = make_chain(horizon, seed)
    mesh = CorpusMeshRuntime(
        workers=[
            ArithmeticWorker("worker_a", "worker", error_rate=worker_error, seed=seed + 301),
            ArithmeticWorker("worker_b", "worker", error_rate=worker_error, seed=seed + 401),
        ],
        verifier=IndependentVerifier("verifier", "verifier", error_rate=verifier_error, seed=seed + 501),
        adversary=Adversary("adversary", "adversary", error_rate=adversary_error, seed=seed + 601),
        audit_rate=0.10,
        seed=seed + 701,
    )

    current = tasks[0].payload["current"] if tasks else 0
    metrics = RunMetrics(success=False, steps=horizon)
    for task in tasks:
        task.payload["current"] = current
        trace = mesh.run_step(task, DeterministicJudge.is_correct)
        metrics.traces.append(trace)
        metrics.agent_calls += 2  # worker + verifier
        if trace.adversary_used:
            metrics.agent_calls += 1
        if (not trace.verifier_passed) or (trace.adversary_used and not trace.adversary_passed):
            metrics.agent_calls += 2  # retry worker + retry verifier
        if not trace.worker_correct:
            metrics.errors_introduced += 1
        challenged = (not trace.verifier_passed) or (trace.adversary_used and not trace.adversary_passed)
        if challenged and not trace.worker_correct:
            metrics.errors_detected += 1
        if trace.recovered:
            metrics.errors_recovered += 1
        if trace.escaped_error:
            metrics.escaped_errors += 1
        current = trace.final_value

    metrics.success = current == expected_final
    return metrics


def aggregate(rows: List[Dict]) -> List[Dict]:
    grouped: Dict[Tuple[str, int], List[Dict]] = {}
    for row in rows:
        grouped.setdefault((row["architecture"], row["horizon"]), []).append(row)
    out = []
    for (arch, horizon), group in sorted(grouped.items()):
        out.append({
            "architecture": arch,
            "horizon": horizon,
            "runs": len(group),
            "success_rate": mean(r["success"] for r in group),
            "avg_errors_introduced": mean(r["errors_introduced"] for r in group),
            "avg_errors_detected": mean(r["errors_detected"] for r in group),
            "avg_errors_recovered": mean(r["errors_recovered"] for r in group),
            "avg_escaped_errors": mean(r["escaped_errors"] for r in group),
            "avg_agent_calls": mean(r["agent_calls"] for r in group),
        })
    return out


def estimate_decay(summary: List[Dict], architecture: str) -> float:
    pts = [(r["horizon"], r["success_rate"]) for r in summary if r["architecture"] == architecture and r["success_rate"] > 0]
    if len(pts) < 2:
        return float("nan")
    xs = [p[0] for p in pts]
    ys = [math.log(p[1]) for p in pts]
    xbar, ybar = mean(xs), mean(ys)
    denom = sum((x - xbar) ** 2 for x in xs)
    if not denom:
        return float("nan")
    slope = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / denom
    return max(0.0, -slope)


def run_benchmark(
    horizons: Iterable[int],
    runs: int,
    seed: int,
    worker_error: float,
    verifier_error: float,
    adversary_error: float,
) -> Tuple[List[Dict], List[Dict], Dict[str, float]]:
    rows: List[Dict] = []
    for horizon in horizons:
        for i in range(runs):
            run_seed = seed + horizon * 100_000 + i
            for arch, fn in [
                ("single", lambda: run_single_agent(horizon, run_seed, worker_error)),
                ("reflection", lambda: run_reflection_agent(horizon, run_seed, worker_error)),
                ("static_team", lambda: run_static_team(horizon, run_seed, worker_error, verifier_error)),
                ("corpus_mesh", lambda: run_corpus_mesh(horizon, run_seed, worker_error, verifier_error, adversary_error)),
            ]:
                m = fn()
                rows.append({
                    "architecture": arch,
                    "horizon": horizon,
                    "run": i,
                    "success": int(m.success),
                    "errors_introduced": m.errors_introduced,
                    "errors_detected": m.errors_detected,
                    "errors_recovered": m.errors_recovered,
                    "escaped_errors": m.escaped_errors,
                    "agent_calls": m.agent_calls,
                })
    summary = aggregate(rows)
    decay = {arch: estimate_decay(summary, arch) for arch in ("single", "reflection", "static_team", "corpus_mesh")}
    return rows, summary, decay


def write_outputs(out_dir: Path, rows: List[Dict], summary: List[Dict], decay: Dict[str, float]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "runs.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    with (out_dir / "summary.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=summary[0].keys())
        w.writeheader()
        w.writerows(summary)
    (out_dir / "decay.json").write_text(json.dumps(decay, indent=2))


def main() -> None:
    p = argparse.ArgumentParser(description="Corpus Mesh v0.1 synthetic long-horizon benchmark")
    p.add_argument("--horizons", nargs="+", type=int, default=[10, 25, 50, 100, 250])
    p.add_argument("--runs", type=int, default=200)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--worker-error", type=float, default=0.015)
    p.add_argument("--verifier-error", type=float, default=0.005)
    p.add_argument("--adversary-error", type=float, default=0.01)
    p.add_argument("--out", type=Path, default=Path("results/latest"))
    args = p.parse_args()

    rows, summary, decay = run_benchmark(
        args.horizons,
        args.runs,
        args.seed,
        args.worker_error,
        args.verifier_error,
        args.adversary_error,
    )
    write_outputs(args.out, rows, summary, decay)

    print("architecture,horizon,success_rate,avg_errors_introduced,avg_errors_detected,avg_errors_recovered,avg_agent_calls")
    for r in summary:
        print(
            f'{r["architecture"]},{r["horizon"]},{r["success_rate"]:.3f},'
            f'{r["avg_errors_introduced"]:.2f},{r["avg_errors_detected"]:.2f},{r["avg_errors_recovered"]:.2f},'
            f'{r["avg_agent_calls"]:.2f}'
        )
    print("\nreliability_decay_lambda")
    for arch, value in decay.items():
        print(f"{arch}: {value:.6f}")


if __name__ == "__main__":
    main()
