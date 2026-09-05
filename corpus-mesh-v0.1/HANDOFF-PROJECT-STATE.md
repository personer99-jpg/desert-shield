# Corpus Mesh — Project State Handoff

**Written:** 2026-09-05. Self-contained: assumes the reader has NO prior
context. Read this first, then the referenced files as needed.

## What this project is

An independent research program by Shane (personer99-jpg on GitHub) testing
whether multi-agent architectures reduce the rate at which AI agent
reliability decays as autonomous task horizon grows. Everything lives in:

- **Repo:** `personer99-jpg/desert-shield` (the repo also contains an
  unrelated static website at its root — ignore it)
- **Branch:** `claude/corpus-mesh-cm-e003-kw3phv`
- **Project dir:** `corpus-mesh-v0.1/`

Key files: `README.md`, `EXPERIMENTS.md` (all protocols incl.
pre-registrations), `RESULTS.md` (synthetic), `RESULTS-CM-E003.md`,
`RESULTS-CM-E004.md`, `HANDOFF-CM-E004.md` (executed), source in
`corpus_mesh/`, tests in `tests/` (20, all passing), raw data in `results/`.

## Experimental history and verdicts (chronological)

**CM-E001 (synthetic, pre-existing):** simulated agents with coin-flip
errors. Found verification+retry dominates; full mesh ≈ simple
worker+verifier team. Also rejected always-on adversarial review (Run 1).

**CM-E003 (real Claude, 2026-09-04):** 4 architectures — single agent,
self-reflection, static worker+blind-verifier team, full Corpus Mesh
CM-0.1.1 — all on claude-haiku-4-5, thinking/tools disabled, paired task
chains (calibrated integer-op chains, horizons 5/10/20/50, 8 runs each,
~$16 total). **Verdict C: no demonstrated improvement of the mesh over the
plain worker+verifier team** (pooled step escapes 4.27% vs 5.29%, z=−0.89;
paired 4W/4L/24T). Verification itself cut the reliability-decay rate
2–2.7× vs unverified baselines. Mechanism attribution: re-verified retries
helped (9% wrong vs 41%/75% for tie-break paths); reputation routing,
audits, provenance were inert or untestable; self-reflection caught 100% of
externally injected faults but only 78% of its own organic errors (shared
blind spots). **Key discovery: the correlated-error ceiling** — ~20-25% of
escaped errors were the worker and verifier (same model) independently
producing the SAME wrong value. An adversarial audit later corrected two
factual errors in the report and found the mesh's "majority arbitration"
harm was specifically a 2-2 deadlock tie-break bug toward the worker
(75% wrong); see the Errata section of RESULTS-CM-E003.md.

**Decision panel (2026-09-04):** pivot — abandon the six-mechanism mesh,
pursue the correlated-error ceiling with a heterogeneous (different model
family) verifier. Pre-registered as CM-E004 with binding kill criteria.

**CM-E004 (2026-09-04/05, run on Shane's Windows desktop + GPU):** two
paired arms of the `verified_team` architecture (worker + blind verifier +
re-verified retries + verifier-favoring escalation), 640 steps/arm,
horizons 10/20/50, identical seeds. Arm A: verifier = same claude-haiku.
Arm B: verifier = **local qwen3:30b-a3b via Ollama** (chosen by a
calibration gate: qwen2.5:14b and qwen2.5-coder:32b FAILED the arithmetic
bar; qwen3:30b-a3b passed at ~0% error). **Result: the heterogeneous
verifier eliminated all escapes** — correlated-agreement escapes 12→0
(one-sided Fisher p=0.00023, the pre-registered primary endpoint), net
escapes 34→0, R(50) 0/8→8/8, false challenges 36→0, and the hetero arm was
cheaper ($1.20 vs $2.78 Claude spend; local verifier calls are free).
Neither kill criterion fired. **Honest confound, flagged in the report:**
the local verifier measured ~0% error on this task family, so "different
family decorrelates errors" cannot be separated from "this verifier is
simply near-perfect at bounded modular arithmetic." Total program spend to
date: ~$32.

## The research arc in one paragraph

The original Corpus Mesh architecture was honestly falsified: its value
reduced to independent verification (already standard) plus one small patch
(verify the retries). But the falsification process surfaced the same-model
correlated-error ceiling, and attacking that with a free local
heterogeneous verifier produced the program's strongest result: perfect
reliability at the longest horizon tested, at lower cost. The durable
assets are (1) the harness — paired seeds, post-hoc-replay scoring with a
no-hidden-oracle test, per-call cost/token accounting, calibration gates,
fault injection, budget caps, resumability; (2) the discipline — 
pre-registration, kill criteria, preserved negative results, adversarial
audit of own reports.

## Working rules that made this credible (keep them)

1. Pre-register endpoints and kill criteria before spending; they are
   binding — no rationalizing past them.
2. Calibrate task difficulty and model capability BEFORE the experiment
   (a $0.16 gate has twice saved the program from an insensitive run).
3. Paired seeds across arms; ground truth never in any prompt or execution
   path; scoring is post-hoc replay only.
4. Budget caps in every run command (`--budget-cap-usd`); never raise them
   mid-experiment.
5. Preserve every aborted run and negative result with a NOTE.md.
6. Adversarially audit reports against raw logs before believing them —
   this caught real errors twice.
7. Verify any claim (including from a previous session's commit message)
   against `runs.jsonl` / `steps.jsonl` / `deep_analysis.json` before
   repeating it.

## Environment facts (Shane's desktop)

Windows; Ollama with qwen3:30b-a3b works; the `claude` CLI works headless —
three Windows fixes are already in `corpus_mesh/claude_cli.py` (multi-token
`--claude-bin` e.g. `"node C:\...\cli.js"`, UTF-8 subprocess decoding,
dated-model-ID assertion). Harness entry points:

```bash
python -m corpus_mesh.e003 calibrate|run|analyze ...   # see README.md
python -m corpus_mesh.e003_deep --out <results-dir>    # mechanism analysis
python -m pytest                                        # 20 tests
```

## Open questions — candidate next steps (pick WITH Shane, then
pre-register in EXPERIMENTS.md before running)

1. **CM-E005a — isolate the mechanism:** capability-matched decorrelation
   test. Find a different-family verifier whose raw error rate on the task
   family is comparable to the worker's (~20%), or raise task difficulty
   until qwen3's error rate is nonzero, so decorrelation can be separated
   from raw capability. Cheap (mostly local).
2. **CM-E005b — generalize the task family:** move beyond arithmetic chains
   to tasks where verification isn't just recomputation (e.g. code edits
   graded by tests, structured-data transformations) — the claim's external
   validity currently rests on one toy family. Medium cost.
3. **Write-up:** the corrected CM-E003 negative/mechanism study + CM-E004
   heterogeneous-verifier result is a coherent, publishable arc (workshop
   paper / arXiv / blog). Zero model cost.
4. **Scale CM-E004 free:** all-local replication (local worker + local
   verifiers, same-family vs cross-family) at 10× sample for $0.
5. Explicitly parked: reputation routing, provenance memory, audits, and
   multi-persona arbitration stay dead unless a task family exists where
   they are structurally testable (per the panel's kill criteria).

## Suggested kickoff for a fresh session

Pull the branch, read this file, skim RESULTS-CM-E003.md and
RESULTS-CM-E004.md, run the tests, then discuss with Shane which next step
to pursue and pre-register it before spending anything.
