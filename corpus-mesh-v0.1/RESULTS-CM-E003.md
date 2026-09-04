# CM-E003 — Real Claude Matched-Model Experiment

**Date:** 2026-09-04
**Model (every call, every architecture):** `claude-haiku-4-5` (served model asserted per call from the CLI envelope)
**Total campaign spend:** ≈ $16 (calibration $0.16, pilot $0.43, aborted run $0.43, main $12.99, fault injection $1.94) — 6,100+ model calls, ~4.4M tokens
**Raw data:** `results/CM-E003/` (calibration.json, pilot/, aborted-run-1/, main/, fault-injection/ — each with runs.jsonl, steps.jsonl, runs.csv, summary.csv, decay.json, deep_analysis.json, config.json)

## Verdict

**C. Corpus Mesh provided no meaningful improvement** over the strongest
simple baseline (a fixed worker + blind independent verifier team) at this
sample size, while costing ~12% more calls and 2× the recovery latency.

Nuance that matters:

- Both verification-based architectures (static team and Corpus Mesh)
  **decisively outperformed** the single agent and the self-reflection agent.
  Decay-rate CIs do not overlap. But that benefit comes from the independent
  verifier, which the plain static team already has — it is not evidence for
  Corpus Mesh's distinctive machinery.
- Corpus Mesh's point estimates were consistently equal-or-slightly-better
  than the static team (pooled step escapes 4.27% vs 5.29%, z = −0.89,
  p ≈ 0.37; paired on identical chains: 4 wins, 4 losses, 24 ties). At the
  longest horizon the run-level result actually favored the static team
  (1/8 vs 0/8 successes).
- The central hypothesis — *"Corpus Mesh reduces the rate at which
  reliability deteriorates as horizon increases"* — is **not supported**
  against the static team. The mesh's small step-level edge sits entirely at
  h=50 (18 vs 24 escaped steps of 400) and is not statistically
  distinguishable from noise.
- Exactly one Corpus Mesh mechanism measurably earned its cost (retry
  re-verification); one measurably failed (arbitration tie-breaks); the rest
  were inert. See "Mechanism attribution".

## Setup

Long-horizon task = a chain of h dependent integer operations; a run succeeds
only if the final value is exactly correct. Per-step operations were
calibrated against the target model first (`calibration.json`): the chosen mix
(mul3_mod / mul2_mod / add_mul / rev_add, uniform) produced a measured ~10-11%
raw worker error per step, statistically identical across architectures
(76 / 73 / 75 / 68 errors introduced per 680 steps).

Controls held fixed across all four architectures:

- same model, asserted per call; extended thinking disabled for every call;
  tools disabled (no calculator); temperature at provider default for all;
- identical worker/verifier prompt text (personas differ by name only);
- paired trials — identical chains (same seeds) for every architecture;
- ground truth never present in any prompt and never in the execution path
  (scoring is post-hoc replay; a no-hidden-oracle unit test enforces this);
- mesh reputation updates use verifier agreement only, never benchmark truth.

Architectures: **single** (1 call/step), **reflection** (self-review with own
answer in context, 2 calls/step), **static_team** (blind verifier recompute +
unverified backup retry on disagreement, ~2.1 calls/step), **corpus_mesh**
CM-0.1.1 (reputation-routed workers, blind verifier, 10% blind audit of
approved steps, re-verified retry, provenance claims, majority arbitration,
~2.2 calls/step).

## Main results (8 paired runs × horizons 5/10/20/50)

Task success rate R(h) [95% Wilson CI]:

| Architecture | h=5 | h=10 | h=20 | h=50 |
|---|---|---|---|---|
| single | 0.750 | 0.250 | 0.125 | 0.000 [0, .32] |
| reflection | 1.000 | 0.250 | 0.250 | 0.000 [0, .32] |
| static_team | 0.875 | 0.625 | 0.375 | **0.125** [.02, .47] |
| corpus_mesh | 1.000 | 0.625 | 0.375 | 0.000 [0, .32] |

Per-step escaped-error rate (all steps pooled per horizon; n = 40/80/160/400):

| Architecture | h=5 | h=10 | h=20 | h=50 | pooled λ_step [95% CI] |
|---|---|---|---|---|---|
| single | .050 | .125 | .138 | .105 | 0.119 [.093, .145] |
| reflection | .000 | .088 | .075 | .103 | 0.092 [.070, .111] |
| static_team | .025 | .038 | .050 | .060 | 0.054 [.034, .073] |
| corpus_mesh | .000 | .038 | .050 | .045 | **0.044** [.029, .059] |

λ_step = −ln(1 − pooled per-step escape rate); bootstrap CIs over runs. The
verification pair (static, mesh) separates cleanly from the unverified pair
(single, reflection); mesh vs static does not separate.

Reliability-decay reading: an escaped-error rate that is roughly flat in h
(it is) means R(h) decays exponentially, as hypothesized — for every
architecture. Verification lowers the decay *rate* about 2–2.7×. The mesh
does not measurably lower it further.

## Mechanism attribution (measured, `deep_analysis.json`)

| Mechanism | Evidence | Verdict |
|---|---|---|
| Blind independent verifier | Detection of worker errors: static 91%, mesh 90% (vs reflection 78%, single 0%) | **The dominant mechanism.** Present in the plain static team too. |
| Retry re-verification (mesh-only) | Challenge resolutions via verified retry accepted a wrong value 9% of the time (5/53); static's unverified retries produced 29 bad accepts vs mesh's 22 | **The only distinctive mesh mechanism that helped.** Worth ~7 escapes per 680 steps. |
| Majority arbitration on deadlock (mesh-only) | 32 tie-break arbitrations, 13 accepted wrong (41%); fallback path 4/5 wrong | **Measurably harmful path.** All 22 mesh post-challenge failures came from arbitration/fallback, none from verified retries. |
| Selective 10% blind audit | 72 audits → 4 catches | Marginal. Cheap, but ~18 extra calls per caught error. |
| Reputation routing | 18 primary switches; no detectable effect on outcomes | Inert here (reputation signal = verifier agreement, which is noisy at ~10% verifier-side error). |
| Provenance dependency invalidation | Structurally inert in a linear chain with same-step detection — nothing downstream exists when a claim is invalidated | Untested by this task shape; no evidence either way. |

### The correlated-error ceiling

7 escapes each (static and mesh — same steps, paired chains) came from the
worker and the blind verifier independently producing the **same wrong
value**. That is 24% of static's and 32% of mesh's total escapes. With a
single underlying model, "independent" samples share failure modes; personas
do not decorrelate weights. The pilot showed the same effect inside the
mesh's arbitration: both worker personas produced the identical wrong value
while both verifier samples agreed on the correct one — a 2-2 deadlock. This
is the binding constraint on every same-model verification architecture, and
the synthetic CM-E001 benchmark could not see it because it modeled errors
as independent coin flips.

## Fault injection (CM-E003-FI: 8 runs × h=12 × 3 injected corruptions each)

Harness-injected additive corruption of the worker's value at known interior
steps, before any verification sees it:

| Architecture | Detected | Contained | Repaired | Runs fully successful |
|---|---|---|---|---|
| single | 0/24 | 0/24 | 0/24 | 0/8 |
| reflection | 24/24 | 24/24 | 23/24 | 3/8 |
| static_team | 24/24 | 24/24 | 22/24 | 3/8 |
| corpus_mesh | 24/24 | 24/24 | 23/24 | 5/8 |

Corpus Mesh detects, contains, and repairs injected faults essentially
perfectly — but so do the simpler checked architectures. Two notable
findings: (1) *foreign* corruption is easy — every architecture with any
checking caught 100% of injected faults, because an additive offset lands on
values the model would not produce itself; the hard errors are the organic,
model-generated ones. (2) Self-reflection shows a revealing asymmetry: 100%
detection of injected corruption vs 78% of its own organic errors — direct
evidence that self-review fails through shared blind spots, which is the
principled argument for independent verification.

## Cost and latency

| Architecture | Avg calls (h=50) | Avg cost (h=50) | Cost/success (h=50) | Mean recovery latency |
|---|---|---|---|---|
| single | 50 | $0.121 | — (0 successes) | — |
| reflection | 100 | $0.262 | — (0 successes) | in-line (2nd call each step) |
| static_team | 106 | $0.273 | $2.18 | 4.0 s |
| corpus_mesh | 120 | $0.311 | — (0 successes) | 7.7 s |

At every horizon where both succeeded, mesh cost-per-success was within ~12%
of static's. Reflection is strictly dominated: static-team reliability class
was available at essentially the same price.

## Methodology changes made before drawing conclusions

1. **Blind verification enforced.** The shipped `real_pilot.py` showed the
   verifier the proposed answer, inviting agreement bias and contradicting
   the blueprint's `blind_verification: true`. CM-E003 verifiers recompute
   from scratch; the harness compares values.
2. **Ground-truth leak removed.** `real_pilot.py` updated mesh reputation
   from benchmark truth. CM-E003 reputation uses verifier agreement only; a
   no-hidden-oracle unit test asserts that when worker and verifier share the
   same wrong value, nothing is "detected".
3. **Reflection baseline added** (missing from the real pilot).
4. **Task difficulty calibrated** — the original add/sub/xor tasks are ~0%
   error for current Claude models and would have made the experiment
   insensitive. `xor_add` was excluded at 80% error (verification-by-recompute
   collapses when the recomputation is usually wrong too).
5. **Step-level decay estimator added** — run-level log-linear fits are
   statistically weak at real-model sample sizes; per-step escapes use every
   step as a Bernoulli trial.
6. One main run was aborted at 20/160 runs and preserved
   (`aborted-run-1/NOTE.md`): a cosmetic prompt artifact plus CPU
   oversubscription that was inflating measured recovery latencies.
   `real_pilot.py` itself is kept unmodified for the record.

## Limitations

- n = 8 runs per cell: run-level CIs are wide; conclusions lean on the
  step-level estimator (680 steps/architecture) and paired comparisons.
- Single task family (bounded integer arithmetic chains) and a single model
  at one capability level, with thinking disabled. A mechanism that is inert
  here (provenance invalidation, reputation) could matter in richer settings
  (long-lived agents, heterogeneous skills, non-verifiable steps).
- The mesh tested is CM-0.1.1 as specified — a deliberately minimal mesh.
- The pilot and this run share the CLI environment's default sampling
  settings; temperature was not independently controlled (identical for all
  architectures).

## Recommended next mutation (CM-0.2), from measured evidence only

1. **Keep:** blind independent verification + *verified* retries (9% failure
   vs 41% for tie-breaks). Make re-verification of retries unconditional.
2. **Replace majority-tie-break arbitration with escalation.** All 22 mesh
   post-challenge escapes came from the arbitration/fallback paths. On a
   deadlock, spend 1–2 additional *independent* recomputations rather than
   tie-breaking toward the workers; accept only a value that achieves a
   strict majority of independent computations.
3. **Attack the correlated-error ceiling with heterogeneity.** 24–32% of
   verified-architecture escapes were worker/verifier agreement on the same
   wrong value; no same-model mechanism can remove these. Two measured-risk
   options: (a) a different model family as verifier (e.g., a local
   open-weights model — near-zero marginal cost on owned hardware); (b)
   transformed verification — verify by inverse operation or modular
   checksum rather than recomputation, so worker and verifier cannot share
   the same arithmetic failure path.
4. **Drop or retarget:** reputation routing (no measurable effect) and the
   flat 10% audit (18 calls per catch) — if kept, target audits at
   high-consequence steps rather than uniformly.
5. Re-run CM-E003 at larger n (the harness resumes; ~$13 per 128-run block)
   before believing any mesh-vs-static difference: the current data cannot
   resolve deltas smaller than ~2 percentage points of per-step escape rate.
