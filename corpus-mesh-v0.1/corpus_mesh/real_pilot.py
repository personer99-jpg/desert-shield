from __future__ import annotations

import argparse
import csv
import json
import os
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

from .agents import apply_op
from .benchmark import make_chain
from .model_adapter import ModelAdapter, OpenAICompatibleHTTPAdapter

SCHEMA = {
    "type": "object",
    "properties": {
        "value": {"type": "integer"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": ["value", "confidence"],
    "additionalProperties": False,
}

VERIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "passed": {"type": "boolean"},
        "correct_value": {"type": "integer"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": ["passed", "correct_value", "confidence"],
    "additionalProperties": False,
}


@dataclass
class PilotMetrics:
    architecture: str
    horizon: int
    success: bool
    model_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    detected_errors: int = 0
    recovered_errors: int = 0
    escaped_errors: int = 0


def _acc(m: PilotMetrics, r) -> None:
    m.model_calls += 1
    m.input_tokens += r.input_tokens
    m.output_tokens += r.output_tokens
    m.cost_usd += r.cost_usd


def _solve(adapter: ModelAdapter, current: int, op: str, operand: int):
    r = adapter.invoke(
        system=(
            "You are a worker in a controlled reliability benchmark. "
            "Perform exactly the requested integer state transition. Return JSON only."
        ),
        user=f"Current integer: {current}. Operation: {op}. Operand: {operand}. Compute the new integer.",
        schema=SCHEMA,
    )
    value = r.structured.get("value")
    if value is None:
        try:
            value = int(r.content.strip())
        except Exception:
            value = None
    return r, value


def _verify(adapter: ModelAdapter, current: int, op: str, operand: int, proposed: Any):
    # Blind verifier gets task + artifact, not worker reasoning.
    r = adapter.invoke(
        system=(
            "You are an independent verifier. Recompute the integer state transition yourself. "
            "Do not trust the proposed answer. Return JSON only."
        ),
        user=(
            f"Current integer: {current}. Operation: {op}. Operand: {operand}. "
            f"Proposed result: {proposed}. Is it correct?"
        ),
        schema=VERIFY_SCHEMA,
    )
    return r, bool(r.structured.get("passed", False)), r.structured.get("correct_value")


def run_single(adapter: ModelAdapter, horizon: int, seed: int) -> PilotMetrics:
    _, tasks, expected = make_chain(horizon, seed)
    m = PilotMetrics("single", horizon, False)
    current = tasks[0].payload["current"] if tasks else 0
    for task in tasks:
        r, value = _solve(adapter, current, task.payload["op"], task.payload["operand"])
        _acc(m, r)
        if not isinstance(value, int):
            m.escaped_errors += 1
            value = current
        current = value
    m.success = current == expected
    return m


def run_static(adapter: ModelAdapter, horizon: int, seed: int) -> PilotMetrics:
    _, tasks, expected = make_chain(horizon, seed)
    m = PilotMetrics("static_team", horizon, False)
    current = tasks[0].payload["current"] if tasks else 0
    for task in tasks:
        op, operand = task.payload["op"], task.payload["operand"]
        r, value = _solve(adapter, current, op, operand)
        _acc(m, r)
        vr, passed, correct_value = _verify(adapter, current, op, operand, value)
        _acc(m, vr)
        deterministic_correct = value == apply_op(current, op, operand)
        if (not passed) and (not deterministic_correct):
            m.detected_errors += 1
        if not passed:
            rr, retry = _solve(adapter, current, op, operand)
            _acc(m, rr)
            if retry == apply_op(current, op, operand) and not deterministic_correct:
                m.recovered_errors += 1
            value = retry
        if value != apply_op(current, op, operand):
            m.escaped_errors += 1
        current = value if isinstance(value, int) else current
    m.success = current == expected
    return m


def run_mesh(adapter: ModelAdapter, horizon: int, seed: int, audit_every: int = 10) -> PilotMetrics:
    _, tasks, expected = make_chain(horizon, seed)
    m = PilotMetrics("corpus_mesh", horizon, False)
    current = tasks[0].payload["current"] if tasks else 0
    reputation = {"worker_a": 1.0, "worker_b": 1.0}
    active = "worker_a"
    for i, task in enumerate(tasks):
        op, operand = task.payload["op"], task.payload["operand"]
        r, value = _solve(adapter, current, op, operand)
        _acc(m, r)
        expected_step = apply_op(current, op, operand)
        worker_correct = value == expected_step

        vr, passed, correct_value = _verify(adapter, current, op, operand, value)
        _acc(m, vr)
        challenged = not passed

        # Selective second independent audit of verifier-accepted work.
        if passed and audit_every > 0 and ((i + 1) % audit_every == 0):
            ar, audit_passed, audit_value = _verify(adapter, current, op, operand, value)
            _acc(m, ar)
            if not audit_passed:
                challenged = True
                correct_value = audit_value

        if challenged and not worker_correct:
            m.detected_errors += 1

        if challenged:
            # Role replacement: retry under a fresh context/worker identity.
            active = "worker_b" if active == "worker_a" else "worker_a"
            rr, retry = _solve(adapter, current, op, operand)
            _acc(m, rr)
            retry_correct = retry == expected_step
            if (not worker_correct) and retry_correct:
                m.recovered_errors += 1
            value = retry
            reputation[active] += 1.0 if retry_correct else -1.0
        else:
            reputation[active] += 1.0 if worker_correct else -1.0

        if value != expected_step:
            m.escaped_errors += 1
        current = value if isinstance(value, int) else current
    m.success = current == expected
    return m


def main() -> None:
    p = argparse.ArgumentParser(description="Corpus Mesh CM-E003 real-model plumbing pilot")
    p.add_argument("--endpoint", default=os.environ.get("CM_MODEL_ENDPOINT", "https://api.openai.com/v1/chat/completions"))
    p.add_argument("--api-key", default=os.environ.get("CM_MODEL_API_KEY"))
    p.add_argument("--model", default=os.environ.get("CM_MODEL_NAME"))
    p.add_argument("--horizons", nargs="+", type=int, default=[10, 25])
    p.add_argument("--runs", type=int, default=3)
    p.add_argument("--seed", type=int, default=17)
    p.add_argument("--input-cost-per-million", type=float, default=0.0)
    p.add_argument("--output-cost-per-million", type=float, default=0.0)
    p.add_argument("--out", type=Path, default=Path("results/CM-E003-pilot"))
    args = p.parse_args()
    if not args.api_key or not args.model:
        raise SystemExit(
            "CM-E003 requires CM_MODEL_API_KEY and CM_MODEL_NAME (or --api-key/--model). "
            "Use any OpenAI-compatible chat-completions endpoint via CM_MODEL_ENDPOINT."
        )

    adapter = OpenAICompatibleHTTPAdapter(
        endpoint=args.endpoint,
        api_key=args.api_key,
        model=args.model,
        input_cost_per_million=args.input_cost_per_million,
        output_cost_per_million=args.output_cost_per_million,
    )

    rows: List[Dict[str, Any]] = []
    for horizon in args.horizons:
        for i in range(args.runs):
            run_seed = args.seed + horizon * 1000 + i
            for fn in (run_single, run_static, run_mesh):
                m = fn(adapter, horizon, run_seed)
                rows.append(m.__dict__)
                print(json.dumps(m.__dict__))

    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "runs.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)

    summary = []
    for arch in sorted({r["architecture"] for r in rows}):
        for horizon in sorted({r["horizon"] for r in rows}):
            group = [r for r in rows if r["architecture"] == arch and r["horizon"] == horizon]
            if not group: continue
            summary.append({
                "architecture": arch,
                "horizon": horizon,
                "runs": len(group),
                "success_rate": mean(int(r["success"]) for r in group),
                "avg_model_calls": mean(r["model_calls"] for r in group),
                "avg_input_tokens": mean(r["input_tokens"] for r in group),
                "avg_output_tokens": mean(r["output_tokens"] for r in group),
                "avg_cost_usd": mean(r["cost_usd"] for r in group),
                "avg_detected_errors": mean(r["detected_errors"] for r in group),
                "avg_recovered_errors": mean(r["recovered_errors"] for r in group),
                "avg_escaped_errors": mean(r["escaped_errors"] for r in group),
            })
    with (args.out / "summary.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=summary[0].keys())
        w.writeheader(); w.writerows(summary)
    print("\nSUMMARY")
    for row in summary:
        print(json.dumps(row))


if __name__ == "__main__":
    main()
