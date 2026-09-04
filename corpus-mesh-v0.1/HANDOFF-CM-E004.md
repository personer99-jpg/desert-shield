# HANDOFF: CM-E004 — Heterogeneous-Verifier Experiment

**Audience:** Claude Code running on the researcher's desktop (with a local
GPU). Everything needed is in this repo on this branch. Read this file fully,
then execute top to bottom. Total budget cap for the whole experiment: **$25
of Claude usage** (the local model is free). Do not exceed it.

## Why this experiment (context from CM-E003)

CM-E003 (`RESULTS-CM-E003.md`) established with real Claude agents that:

1. Blind independent verification is the dominant reliability mechanism
   (cuts the reliability-decay rate 2–2.7×). The full Corpus Mesh added no
   demonstrated improvement over a plain worker+verifier team.
2. The binding constraint on ALL same-model verification: ~20-25% of escaped
   errors happened because the worker and the verifier — the same model —
   independently produced the **same wrong value**. No same-model
   architecture can remove these.
3. An adversarial audit decomposed the mesh's arbitration failures and
   produced the fixed policy now implemented as the `verified_team`
   architecture (re-verified retries + verifier-favoring escalation vote).

**CM-E004 hypothesis (pre-registered in EXPERIMENTS.md):** a verifier from a
*different model family* has partially decorrelated failure modes, so it
reduces correlated-agreement escapes. Primary endpoint: the
`correlated_agreement_on_wrong` count in `deep_analysis.json` — NOT the net
escape rate (that is a secondary endpoint; per-arm power is only adequate for
the correlated-escape effect, which is predicted to be large).

## Kill criteria (decided in advance — do not rationalize past them)

- Heterogeneous verifier reduces correlated-agreement escapes by **less than
  ~50%** relative → the architecture line ends; write up the negative result.
- Correlated escapes drop but **net** step-escape rate is no better (weak
  local verifier gives back the gains) → at most ONE alternative local
  verifier model may be tried within budget, then stop.
- Do not re-test reputation routing, provenance memory, audits, or
  multi-persona arbitration on linear chains — CM-E003 already established
  they are inert or harmful there.

## Step 0 — Setup and sanity checks

```bash
cd corpus-mesh-v0.1
python3 -m pytest -q            # all tests must pass before spending anything
```

Local verifier model: any OpenAI-compatible server works. With Ollama:

```bash
ollama pull qwen2.5:14b-instruct   # good arithmetic per size; adjust to VRAM
ollama serve &                      # exposes http://localhost:11434
export CM_MODEL_API_KEY=local       # any non-empty string
```

VRAM guide: 24GB → `qwen2.5:32b` (better); 16GB → `qwen2.5:14b-instruct`;
8-12GB → `qwen2.5:7b-instruct` (weaker — acceptable, see kill criterion 2).
Avoid Llama-3.x-8B for the verifier role: weak arithmetic.

**Calibrate the local verifier first** (~$0, ~2 min) — it must actually be
able to do these ops or the experiment is dead on arrival:

```bash
python3 -m corpus_mesh.e003 calibrate --samples 10 \
    --endpoint http://localhost:11434/v1/chat/completions --model qwen2.5:14b-instruct \
    --ops mul3_mod mul2_mod --out results/CM-E004/local-calibration.json
```

Requirement: local-model error on `mul2_mod` ≤ ~30% and on `mul3_mod` ≤ ~60%.
If worse, try a bigger local model; if none fits, report back and stop.

## Step 1 — Pilot (~$0.50, ~10 min)

Two arms, tiny scale, to validate plumbing end to end:

```bash
# Arm A: same-model baseline (worker AND verifier = claude-haiku via CLI)
python3 -m corpus_mesh.e003 run --architectures verified_team \
    --horizons 6 --runs 2 --op-mix mul3_mod mul2_mod \
    --seed-base 40260904 --out results/CM-E004/pilot-same --budget-cap-usd 2

# Arm B: heterogeneous (worker = claude-haiku, verifier = local model)
python3 -m corpus_mesh.e003 run --architectures verified_team \
    --horizons 6 --runs 2 --op-mix mul3_mod mul2_mod \
    --seed-base 40260904 \
    --verifier-endpoint http://localhost:11434/v1/chat/completions \
    --verifier-model qwen2.5:14b-instruct \
    --out results/CM-E004/pilot-hetero --budget-cap-usd 2
```

Check both `steps.jsonl` files: verifier calls in Arm B must show near-zero
`cost_usd` (local) while worker calls show Claude costs; challenges and
`escalated_vote` arbitrations should appear plausible. If anything looks
wrong, fix before scaling; the harness resumes, so nothing is wasted.

## Step 2 — Main run (~$9-12 of Claude usage, a few hours)

Same seeds in both arms (paired design). `mul3_mod mul2_mod` only — CM-E003
measured the other ops contribute zero escapes in verified architectures
(inert padding that dilutes power).

```bash
python3 -m corpus_mesh.e003 run --architectures verified_team \
    --horizons 10 20 50 --runs 8 --op-mix mul3_mod mul2_mod \
    --seed-base 50260904 --out results/CM-E004/main-same --budget-cap-usd 10

python3 -m corpus_mesh.e003 run --architectures verified_team \
    --horizons 10 20 50 --runs 8 --op-mix mul3_mod mul2_mod \
    --seed-base 50260904 \
    --verifier-endpoint http://localhost:11434/v1/chat/completions \
    --verifier-model qwen2.5:14b-instruct \
    --out results/CM-E004/main-hetero --budget-cap-usd 10
```

640 steps per arm. Run arms sequentially, not concurrently (the CLI spawns
are CPU-heavy; oversubscription inflates the recovery-latency metric — this
bit us in CM-E003).

Optional free extension (recommended if time permits): a third arm with the
*worker* also local (worker=local-A, verifier=local-B vs verifier=local-A) at
10× scale for $0 — a same-vs-different-family replication with real power.

## Step 3 — Analysis

```bash
python3 -m corpus_mesh.e003_deep --out results/CM-E004/main-same
python3 -m corpus_mesh.e003_deep --out results/CM-E004/main-hetero
```

Primary comparison: `escape_taxonomy.verified_team.correlated_agreement_on_wrong`
in the two `deep_analysis.json` files (CM-E003 reference point: ~7 per 680
steps with the richer op mix; expect more with the mul-only mix). Report it
with a Fisher exact test. Secondary: pooled step-escape rate, decay lambda
(`decay.json`), detection/recovery rates, cost per success, and verifier-side
quality (how often the local verifier challenged a *correct* worker value —
false challenges cost calls; count `challenged` steps where the worker was
right, available in `deep_analysis.json` recovery/detection tables).

## Step 4 — Report and commit

Write `RESULTS-CM-E004.md` in the same style as `RESULTS-CM-E003.md`:
verdict against the pre-registered endpoint and kill criteria first, tables,
mechanism notes, limitations, spend. Preserve all raw outputs. State plainly
whether a kill criterion fired. Commit everything and push to this branch.

Rules that carry over from CM-E003 (non-negotiable):
- same seeds across arms; ground truth never in any prompt;
- thinking disabled and tools disabled for every Claude call (the adapter
  does this); the local server gets plain chat completions;
- preserve failed runs and negative results; document any methodology change;
- respect the budget caps in every command; do not raise them.
