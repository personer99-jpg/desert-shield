# Experiment Protocol

## CM-E001 — Synthetic reliability decay

Purpose: validate the harness and determine whether independent verification/retry produces the expected statistical behavior before introducing real LLM costs.

Architectures:
1. single agent;
2. single agent + confidence-triggered self-reflection;
3. Corpus Mesh v0.1.

Default simulated failure rates:
- worker: 1.5% per action;
- independent verifier: 0.5%;
- adversary: 1.0%.

Horizons: 10, 25, 50, 100, 250 actions.

Primary metric: successful completion probability R(h).

Secondary metrics: errors introduced, detected, recovered, escaped, and fitted exponential reliability-decay lambda.

## CM-E002 — Explicit fault injection

Inject a guaranteed worker fault at a known position and verify that the mesh detects it, retries independently, records provenance, and prevents the bad value from escaping.

## CM-E003 — Real LLM matched-model pilot (next)

Use the same model for baseline and Corpus Mesh. Start with objective coding/terminal tasks where deterministic grading is available. Compare success, cost, tokens, wall time, escaped errors, and recovery.

Do not tune architecture on held-out final evaluation tasks.

## CM-E003A — Real-model plumbing pilot

A dependency-free OpenAI-compatible HTTP adapter and matched-model pilot are now implemented in `corpus_mesh.real_pilot`.

The same model is used for the single-agent, fixed worker+verifier, and Corpus Mesh paths. The pilot records model calls, token usage, estimated provider cost, detected/recovered/escaped errors, and deterministic final success.

Required environment variables:

```bash
export CM_MODEL_API_KEY='...'
export CM_MODEL_NAME='...'
export CM_MODEL_ENDPOINT='https://provider.example/v1/chat/completions'  # optional
python -m corpus_mesh.real_pilot --horizons 10 25 --runs 3
```

This pilot validates real-model wiring. It is not a substitute for external long-horizon environments such as OSWorld/Terminal-Bench.

## CM-E003 — Real Claude matched-model experiment (this run)

Implemented in `corpus_mesh/e003.py` + `corpus_mesh/claude_cli.py` +
`corpus_mesh/e003_tasks.py`. Runs on the authenticated Claude Code CLI in
headless mode; no separate API key.

Architectures (all served by the same Claude model, same generation settings):
1. `single` — one worker call per step;
2. `reflection` — worker call + correlated self-review (model sees its own
   previous answer, non-blind);
3. `static_team` — worker + blind independent verifier recompute; disagreement
   triggers one backup-worker retry which is accepted without re-verification
   (mirrors the synthetic static team);
4. `corpus_mesh` — CM-0.1.1: reputation-routed worker choice (updated from
   verifier agreement only), blind verifier every step, selective blind audit
   of ~10% of approved steps, challenged steps retried by the alternate worker
   persona AND re-verified, provenance claims with invalidation, majority
   arbitration when the retry also fails verification.

Controls:
- same model for every call, asserted per call from the CLI's served-model
  report;
- extended thinking disabled identically for all calls
  (`MAX_THINKING_TOKENS=0`); tools disabled (`--tools ""`) so no agent can
  shell out to a calculator;
- identical worker/verifier prompt text across architectures (personas differ
  by name only);
- paired trials: the same task chains (same seeds) are given to every
  architecture;
- ground truth is never present in any prompt and never enters the execution
  path; scoring is post-hoc replay (`score_run`);
- per-run and cumulative budget cap enforced by the harness.

Task battery: bounded-state deterministic integer ops, difficulty calibrated
against the target model first (`e003 calibrate`, calibration-only seeds) so
the per-step worker error rate is measurable. Chosen mix recorded in
`results/CM-E003/calibration.json` and the run's `config.json`.

Primary metric: R(h) and the reliability-decay rate lambda, estimated two
ways: the CM-E001 run-level log-linear fit, and a step-level estimator
`-ln(1 - per-step escape rate)` that uses every step as a Bernoulli trial
(added because run-level fits are statistically weak at real-model sample
sizes). Bootstrap 95% CIs on both.

Fault injection (CM-E003-FI): the harness corrupts the worker's parsed value
at known interior steps before verification sees it, in every architecture,
and scores detection / containment / repair per injected fault.

### Methodology changes made before drawing conclusions (and why)

1. The shipped `real_pilot.py` verifier was shown the proposed answer. That
   invites agreement bias and contradicts the blueprint constraint
   `blind_verification: true`. CM-E003 verifiers recompute blind; the harness
   compares values.
2. The shipped `real_pilot.py` updated mesh reputation from benchmark ground
   truth (`worker_correct`). CM-E003 reputation updates use verifier
   agreement only. A dedicated no-hidden-oracle test asserts that when worker
   and verifier share the same wrong value, nothing is "detected".
3. The reflection baseline was missing from the real pilot; added, since the
   user-facing comparison requires it.
4. The original task set (single-digit add/sub/xor) has ~0% per-step error
   for current Claude models, which would make every architecture score 100%
   and the experiment uninformative. Replaced with a calibrated harder mix.
5. `real_pilot.py` itself is kept unmodified for the record.

## CM-E004 — Heterogeneous-verifier experiment (pre-registered, not yet run)

Hypothesis: a verifier from a different model family partially decorrelates
failure modes and therefore reduces correlated-agreement escapes (worker and
verifier independently producing the same wrong value — the measured binding
constraint of CM-E003, 19-24% of verified-architecture escapes).

Design: two paired arms of the `verified_team` architecture (worker + blind
verifier + re-verified retries + verifier-favoring escalation), identical
seeds: (A) verifier = same Claude model as worker; (B) verifier = local
open-weights model of a different family. Primary endpoint (pre-registered):
`correlated_agreement_escapes.verified_team` in deep_analysis.json (always
emitted, 0 default). Secondary: pooled step-escape rate, decay lambda,
`false_challenges` (also emitted directly), cost per success.

Documented design property: the escalation vote pools three verifier-model
samples against two worker-model samples and breaks ties toward verifier
values, so the heterogeneous arm deliberately weights arbitration toward the
local verifier model; kill criterion 2 (net escape rate no better because the
weaker verifier gives back the gains) exists precisely to catch the failure
mode this creates.

Kill criteria are written in HANDOFF-CM-E004.md and are binding. Full
protocol: HANDOFF-CM-E004.md.
