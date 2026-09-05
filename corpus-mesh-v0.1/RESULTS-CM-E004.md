# CM-E004 — Heterogeneous-Verifier Experiment

**Date:** 2026-09-04 → 2026-09-05 (overnight main run)
**Worker (both arms, every call):** `claude-haiku-4-5-20251001` via Claude CLI (served model asserted per call from the CLI envelope; thinking disabled, tools disabled)
**Verifier Arm A:** same `claude-haiku-4-5-20251001` (same-model baseline)
**Verifier Arm B:** `qwen3:30b-a3b` (Qwen3 30B-A3B MoE, Q4_K_M), local via Ollama 0.17.4 on an RTX 5090 laptop GPU (24 GB VRAM), plain chat completions, temperature 0
**Total campaign spend:** ≈ $15.7 of Claude usage (breakdown below; caps respected on every invocation). Local model: $0.
**Raw data:** `results/CM-E004/` (local-calibration*.json, pilot-same/, pilot-hetero/, main-same/, main-hetero/, aborted-run-1/, main-run.log — each experiment dir with runs.jsonl, steps.jsonl, runs.csv, summary.csv, decay.json, deep_analysis.json, config.json)

## Verdict

**The heterogeneous verifier eliminated correlated-agreement escapes entirely
and neither pre-registered kill criterion fired.**

- **Primary endpoint** (`correlated_agreement_escapes.verified_team`):
  **12/640 steps (Arm A) → 0/640 steps (Arm B)**, identical chains (paired
  seeds). One-sided Fisher exact **p = 0.00023**. The pre-registered kill
  threshold was a reduction below ~50%; the observed reduction is 100%.
- **Secondary endpoint** (net step escapes): **34/640 (5.31%) → 0/640
  (0.00%)**, one-sided Fisher exact p < 10⁻⁶. The kill-criterion-2 scenario —
  a weak local verifier giving back the correlated-escape gains through false
  challenges and bad arbitration — did not occur: **zero false challenges**
  in 640 Arm B steps (vs 36 in Arm A).
- Task success at the longest horizon: **R(50) = 0/8 (Arm A) → 8/8 (Arm B)**.
  Every Arm B run at every horizon succeeded (24/24).

The correlated-error ceiling measured in CM-E003 (~19–24% of verified-arm
escapes from worker and same-model verifier producing the same wrong value)
is confirmed to be same-model-specific: replacing only the verifier with a
different-family local model removed it completely at this sample size.

Interpretation caveat (pre-registration honesty): this arm confounds *family
heterogeneity* with *verifier capability at this task*. The local verifier
made zero detectable errors across ~801 verifier computations (0 false
challenges, 0 wrong escalation votes; 95% upper bound ≈ 0.5% per call), so
CM-E004 cannot distinguish "different family decorrelates failure modes"
from "this verifier is simply near-perfect at bounded modular arithmetic."
What it does establish: a free, local, open-weights verifier of a different
family breaks the same-model ceiling on this task family — decisively and at
zero marginal verifier cost.

## Local-verifier calibration (gate before any spend)

Requirement from the handoff: error ≤ ~30% on `mul2_mod` and ≤ ~60% on
`mul3_mod` (10 samples each, `results/CM-E004/local-calibration*.json`):

| Model | mul3_mod | mul2_mod | Latency/call | Gate |
|---|---|---|---|---|
| qwen2.5:14b (instruct, handoff's example) | 100% | 30% | 8–10 s | **fail** |
| qwen2.5-coder:32b | 90% | 40% | 47–72 s | **fail** |
| **qwen3:30b-a3b** (MoE, thinking) | **0%** | **0%** | 15–26 s | **pass** |

Both qwen2.5-generation candidates failed the gate outright (real arithmetic
errors, zero parse failures). Per the handoff's escape hatch ("try a bigger
local model"), the newer-generation Qwen3 30B-A3B MoE was pulled (~19 GB,
fits 24 GB VRAM, runs at ~3B-active speed) and passed with zero errors.

## Setup

Identical to CM-E003 (`verified_team` architecture: worker + blind verifier +
re-verified retries + verifier-favoring escalation), with:

- op mix `mul3_mod mul2_mod` only (CM-E003 measured the other ops contribute
  zero escapes in verified architectures);
- horizons 10/20/50 × 8 runs per arm = 640 steps per arm;
- **paired design:** identical chain seeds in both arms (`--seed-base
  50260904`); ground truth never in any prompt; scoring is post-hoc replay;
- worker prompts and worker model identical across arms — the arms differ
  ONLY in which model recomputes verification;
- Claude calls: thinking disabled (`MAX_THINKING_TOKENS=0`), tools disabled,
  per-call served-model assertion. Local calls: plain chat completions,
  temperature 0. The local model's visible chain-of-thought is its "show
  your working" — the same license the Claude prompt grants.

## Main results (24 paired runs per arm)

Task success rate R(h):

| Arm | h=10 | h=20 | h=50 |
|---|---|---|---|
| A: same-model verifier | 6/8 | 3/8 | 0/8 |
| B: heterogeneous verifier | **8/8** | **8/8** | **8/8** |

Step-level outcomes (640 steps per arm):

| Metric | Arm A | Arm B |
|---|---|---|
| Raw worker errors | 129 (20.2%) | 122 (19.1%) |
| Detected (challenged) | 117 (90.7%) | **122 (100%)** |
| Repaired after detection | 99 (84.6%) | **122 (100%)** |
| Correlated-agreement escapes | **12** | **0** |
| Challenged-but-bad-accept escapes | 22 | 0 |
| Net escaped steps | 34 (5.31%) | **0 (0.00%)** |
| λ_step (95% CI) | 0.0546 [0.036, 0.074] | 0.0 [0, ~0.006]* |
| False challenges | 36 | **0** |

\* Zero escapes in 640 steps: rule-of-three 95% upper bound ≈ 3/640 → λ ≤
~0.0047. Even the upper bound is ~12× below Arm A's point estimate.

Worker error rates are statistically identical across arms (129 vs 122 on
paired chains), confirming the arms differ only through verification.

Arbitration decomposition:

| Path | Arm A | Arm B |
|---|---|---|
| retry_verified | 85 (8 accepted wrong, 9.4%) | 83 (0 wrong) |
| escalated_vote | 68 (14 accepted wrong, 20.6%) | 39 (0 wrong) |

Arm A's escalation-vote failure rate (20.6%) replicates CM-E003's finding
that same-model arbitration is the weak link; with a heterogeneous verifier
the identical policy went 39/39.

## Cost and latency

| | Arm A | Arm B |
|---|---|---|
| Claude calls | 1,654 | ~1,679 total, 762 paid (verifier calls local/free) |
| Claude cost (main run) | $2.78 | $1.30 |
| Cost/success at h=50 | — (0 successes) | $0.095 |
| Mean recovery latency | 8.3 s | 96.2 s |
| Wall-clock | ~35 min | ~4.5 h |

The heterogeneous arm is cheaper per call and infinitely better per success
at h=50, but pays a large wall-clock price: the local verifier's thinking
takes 15–26 s/call and serializes on one GPU (recovery latency is further
inflated by queueing — see limitations).

## Kill criteria — none fired

1. "Reduction < ~50% → architecture line ends": observed 100% reduction
   (12 → 0, p = 0.00023). **Not fired.**
2. "Correlated escapes drop but net escape rate no better": net rate went
   5.31% → 0.00% with zero false challenges. **Not fired.** No alternative
   local verifier was needed.
3. Reputation routing, provenance memory, audits, and multi-persona
   arbitration were not re-tested, per instruction.

## Environment and methodology notes (all changes documented)

The experiment logic, prompts, seeds, budget caps, and endpoints are exactly
as pre-registered. The following environmental accommodations were required
to run the Claude CLI headlessly on this Windows machine, none of which
change call semantics:

1. `claude_cli.py`: `claude_bin` may be multiple whitespace-separated tokens
   — the npm `claude.cmd` shim routes through cmd.exe, which truncates
   multi-line prompt arguments at the first newline (verified empirically:
   flags after the prompt were silently dropped). All calls invoke
   `node .../cli.js` directly.
2. `claude_cli.py`: served-model assertion also accepts the exact dated model
   ID — the current CLI reports `modelUsage` keys with the date suffix.
3. `claude_cli.py`: subprocess decoding pinned to UTF-8 with replacement —
   Windows' default cp1252 decoding intermittently crashed runs (byte 0x9d)
   and produced mojibake in stored snippets.
4. All harness calls run with a dedicated bare `CLAUDE_CONFIG_DIR` and
   `--strict-mcp-config`, and with session env vars scrubbed. Without this,
   the CLI injects the user's global CLAUDE.md, MCP servers, and ~45k tokens
   of claude.ai connector tool schemas into every call (~20–230× cost).
5. **Aborted first main run preserved** (`results/CM-E004/aborted-run-1/`,
   NOTE.md inside): Arm A ran under the 45k-token bloated context, hit its
   $10 cap at 17/24 runs, and was restarted from scratch under the lean
   context so that all runs in both arms share identical conditions. The
   bloated partial data is preserved for the record and is not commingled.
6. Arm B's initial invocation ran 6 concurrent workers; the seven h=50 runs
   saturated the single-GPU Ollama queue past the 120 s HTTP timeout and
   failed cleanly (recorded in `failures.jsonl`). They were resumed with
   `--max-workers 2` (execution knob only; same seeds, prompts, models).
7. Pilot (`pilot-same/`, `pilot-hetero/`, seed-base 40260904, $0.60) ran
   under the bloated context (the inflation was discovered after it); its
   role was plumbing validation only and its data is not used in analysis.

## Limitations

- **Capability vs family confound** (also flagged in the verdict): the local
  verifier's measured error rate on these ops is ~0%, so decorrelation and
  raw accuracy cannot be separated. A verifier matched to the worker's
  ~20% error rate but from a different family would isolate the
  decorrelation mechanism; no candidate passing that profile was available.
- **Temperature-0 determinism:** the escalation vote pools three local
  verifier samples that are near-identical at temperature 0 with identical
  prompts — effectively one sample counted three times, making arbitration
  even more verifier-favoring than designed. With a near-perfect verifier
  this was purely beneficial; with a mediocre one it would be dangerous.
  Kill criterion 2 was the guard, and the design property was documented in
  the pre-registration.
- **Recovery-latency comparability:** Arm B's 96.2 s mean recovery latency
  includes Ollama queue waits (6 workers early, 2 workers in the h=50
  resume); it measures this deployment, not the model's intrinsic latency
  (~15–26 s/call).
- Single task family (bounded integer arithmetic chains), single worker
  model at one capability level, n = 640 steps/arm. Zero observed escapes
  bound Arm B's true escape rate only to ≤ ~0.5% (95%).
- The optional third arm (local worker + local verifiers at 10× scale) was
  not run — Arm B alone consumed ~4.5 h of GPU serial time; a 10× local-only
  replication is a natural follow-up and costs $0 of Claude usage.

## Spend accounting

| Item | Claude usage |
|---|---|
| Local-verifier calibration (3 models × 20 calls) | $0 (local) |
| Adapter validation probes | ≈ $0.45 |
| Pilot (both arms, seed 40260904) | $0.60 |
| Aborted main run (bloated context; preserved) | $10.08 + ≈$0.4 unlogged in-flight |
| Main run Arm A (lean) | $2.78 |
| Main run Arm B (lean, incl. resume) | $1.30 |
| **Total** | **≈ $15.7 of $25** |

Every invocation ran under its handoff-specified `--budget-cap-usd`; no cap
was raised. The one cap that was ever hit ($10, aborted Arm A) stopped the
run exactly as designed.

## Recommended next steps (from measured evidence only)

1. **Adopt heterogeneous verification as the default** for verified teams on
   verifiable-recompute tasks: it removed 100% of correlated escapes and
   100% of arbitration failures here, at $0 marginal verifier cost and
   ~2× cheaper Claude spend per step.
2. **Run the free 10× local-only replication** (worker=local-A vs
   verifier=local-A / local-B) to (a) power the decorrelation claim
   properly and (b) separate family-heterogeneity from verifier-capability
   by choosing a local worker/verifier pair with matched error rates.
3. **Test a capability-matched heterogeneous verifier** (one with ~15–25%
   error on these ops) to isolate the decorrelation mechanism that CM-E004
   could not.
4. Latency engineering if this pattern ships: batch verification, a smaller
   distilled verifier, or verifier-call parallelism sized to GPU memory —
   the 96 s recovery latency is a deployment artifact, not intrinsic.
