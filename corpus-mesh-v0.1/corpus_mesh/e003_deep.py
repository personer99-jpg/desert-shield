"""Deep mechanism analysis for CM-E003 (reproducible).

Reads an experiment out-dir (runs.jsonl + steps.jsonl), regenerates ground
truth from chain seeds, and writes deep_analysis.json with:
- detection/recovery rates per architecture;
- escape taxonomy (correlated agreement, failed recovery, unflagged);
- Corpus Mesh mechanism attribution (audit catches, arbitration outcomes and
  their error rates, reputation switches);
- paired mesh-vs-static comparison on identical chains;
- pooled two-proportion z for step escapes, mesh vs static.

Usage: python -m corpus_mesh.e003_deep --out results/CM-E003/main
"""
from __future__ import annotations

import argparse
import collections
import json
import math
from pathlib import Path

from .e003_tasks import make_chain


def analyze(out_dir: Path) -> dict:
    cfg = json.loads((out_dir / "config.json").read_text())
    mix = cfg["op_mix"]
    logs = [json.loads(l) for l in (out_dir / "steps.jsonl").read_text().splitlines() if l.strip()]
    seen = set()
    logs = [lg for lg in logs if not (lg["run_key"] in seen or seen.add(lg["run_key"]))]

    det = collections.defaultdict(lambda: [0, 0])
    rec = collections.defaultdict(lambda: [0, 0])
    tax = collections.defaultdict(collections.Counter)
    mesh_mech = collections.Counter()
    arb_outcomes = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    false_challenges = collections.defaultdict(int)
    correlated_escapes = collections.defaultdict(int)
    archs_seen = set()

    for lg in logs:
        arch = lg["architecture"]
        archs_seen.add(arch)
        chain = make_chain(lg["horizon"], lg["chain_seed"], mix)
        cur = chain.start
        for op, s in zip(chain.ops, lg["steps"]):
            truth = op.apply(cur)
            wrong = s["worker_value"] != truth
            if wrong:
                det[arch][0] += 1
                if s["challenged"]:
                    det[arch][1] += 1
            if s["challenged"] and not wrong:
                false_challenges[arch] += 1
            if s["challenged"] and wrong:
                rec[arch][0] += 1
                if s["accepted"] == truth:
                    rec[arch][1] += 1
            if s.get("arbitration"):
                arb_outcomes[arch][s["arbitration"]]["total"] += 1
                if s["accepted"] != truth:
                    arb_outcomes[arch][s["arbitration"]]["accepted_wrong"] += 1
            if s["accepted"] != truth:
                if s["challenged"]:
                    tax[arch]["challenged_but_bad_accept"] += 1
                elif wrong:
                    vvals = [c["value"] for c in s["calls"] if c["role"] == "verifier"]
                    if arch in ("static_team", "corpus_mesh", "verified_team") and vvals and vvals[0] == s["worker_value"]:
                        tax[arch]["correlated_agreement_on_wrong"] += 1
                        correlated_escapes[arch] += 1
                    else:
                        tax[arch]["unflagged_other"] += 1
                else:
                    tax[arch]["worker_right_accepted_wrong"] += 1
            cur = s["accepted"]
        if arch == "corpus_mesh":
            ex = lg.get("mesh_extras", {})
            for k in ("audits", "audit_catches", "challenges", "primary_switches"):
                mesh_mech[k] += ex.get(k, 0)
            for k, v in ex.get("arbitrations", {}).items():
                mesh_mech["arb_" + k] += v

    rows = []
    seen_r = set()
    for line in (out_dir / "runs.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r["run_key"] in seen_r:
            continue
        seen_r.add(r["run_key"])
        rows.append(r)

    result: dict = {
        "detection_rate": {
            a: {"errors": d[0], "challenged": d[1], "rate": round(d[1] / d[0], 3) if d[0] else None}
            for a, d in sorted(det.items())
        },
        "recovery_rate": {
            a: {"detected": d[0], "repaired": d[1], "rate": round(d[1] / d[0], 3) if d[0] else None}
            for a, d in sorted(rec.items())
        },
        "escape_taxonomy": {a: dict(c) for a, c in sorted(tax.items())},
        # CM-E004 primary endpoint — always present per architecture, 0 default.
        "correlated_agreement_escapes": {a: correlated_escapes.get(a, 0) for a in sorted(archs_seen)},
        # CM-E004 secondary endpoint: challenged steps where the worker was right.
        "false_challenges": {a: false_challenges.get(a, 0) for a in sorted(archs_seen)},
        "mesh_mechanisms": dict(mesh_mech),
        "arbitration_outcomes": {
            a: {label: dict(c) for label, c in sorted(labels.items())}
            for a, labels in sorted(arb_outcomes.items())
        },
    }

    archs = {r["architecture"] for r in rows}
    if {"corpus_mesh", "static_team"} <= archs:
        byrun = {(r["architecture"], r["horizon"], r["run_idx"]): r for r in rows}
        w = l = mw = ml = pairs = 0
        for (a, h, i), m in byrun.items():
            if a != "corpus_mesh" or ("static_team", h, i) not in byrun:
                continue
            s = byrun[("static_team", h, i)]
            pairs += 1
            w += m["success"] > s["success"]
            l += m["success"] < s["success"]
            mw += m["escaped_errors"] < s["escaped_errors"]
            ml += m["escaped_errors"] > s["escaped_errors"]
        me = sum(r["escaped_errors"] for r in rows if r["architecture"] == "corpus_mesh")
        se = sum(r["escaped_errors"] for r in rows if r["architecture"] == "static_team")
        steps = sum(r["horizon"] for r in rows if r["architecture"] == "corpus_mesh")
        p1, p2 = me / steps, se / steps
        p = (me + se) / (2 * steps)
        z = (p1 - p2) / math.sqrt(p * (1 - p) * 2 / steps) if 0 < p < 1 else 0.0
        result["paired_mesh_vs_static"] = {
            "pairs": pairs,
            "success_wins": w, "success_losses": l, "success_ties": pairs - w - l,
            "escape_better": mw, "escape_worse": ml, "escape_equal": pairs - mw - ml,
            "pooled_step_escapes": {"mesh": me, "static": se, "steps_per_arch": steps},
            "two_proportion_z": round(z, 3),
        }
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    result = analyze(args.out)
    (args.out / "deep_analysis.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
