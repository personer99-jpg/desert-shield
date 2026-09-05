# PRE-REGISTRATION (DRAFT v2) — CM-E005a: Capability-matched cross-family verifier

**Status: DRAFT — awaiting Shane's written approval. Nothing below runs until
he approves this document and its cost table. On approval this text moves
into EXPERIMENTS.md verbatim and becomes binding.**

v2 (2026-09-05): revised after a three-critic adversarial verification pass
(numbers vs raw logs; statistics; decision-consistency). Material changes
from v1: battery target 350 → 420 error events (honest power math), primary
test changed to paired exact McNemar, Stage -1 stop-gate removed (it was
logically inverted), temperature asymmetry documented, seed namespaces
pinned, Stage-2 threshold fixed to ≤4, second go/no-go checkpoint added
before Stage 2, expected cost $4.6 → $5.3 (hard cap $8 unchanged).

## Question

CM-E004's heterogeneous verifier eliminated all correlated-agreement escapes
(12 → 0 in 640 paired steps, one-sided Fisher p = 0.00023), but the verifier
(qwen3:30b-a3b, thinking on) measured ~0% raw error on the task family, so
the result cannot distinguish:

- **H-family:** a different model family decorrelates error VALUES — even a
  mediocre cross-family verifier rarely produces the worker's exact wrong
  answer; from
- **H-capability:** the win is raw verifier accuracy; family is irrelevant.

CM-E005a isolates this by testing a cross-family verifier whose raw error
rate is MATCHED to the same-family (Claude) verifier's, on a battery built
from CM-E004's own recorded errors.

## Fixed reference facts (from raw logs, audited 2026-09-05)

- Same-family collision rate, conditional on worker error: 12/129 ≈ 9.3%
  (CM-E004 Arm A live pipeline; consistent with CM-E003: 7/75, 7/68).
  **Bridging statistic only** — it was measured at provider-default
  temperature in the live pipeline. The Stage-1 primary comparison is
  battery-haiku vs battery-candidate under identical presented conditions;
  battery-haiku's collision count on the 129 recorded items is reported
  against the historical 12 with no gate attached.
- Same-family verifier-side raw recompute error under the VERIFIER prompt:
  36 false challenges / 511 correct-worker steps ≈ 7.0% (historical anchor;
  the binding matching target is the Stage-0 measurement, not this number).
- Same-model attractor benchmark (computed 2026-09-05 from the paired E004
  arms): on the 296 paired steps where the two arms' chains had not yet
  diverged, the Arm-B worker erred on 50; on **15/50 (30%)** the Arm-A
  worker — an independent same-model draw on the same input — produced the
  exact same wrong value. This is the same-model shared-attractor mechanism
  under the WORKER prompt; verifier-prompt framing alone already reduces it
  to ~9.3%. RESULTS must report both so prompt-decorrelation and
  family-decorrelation are not conflated.
- Worker model: claude-haiku-4-5-20251001, asserted per call (dated ID). If
  the served model differs at any point, the current stage STOPS; completed
  stages remain valid (post-hoc scored); partials preserved with NOTE.md.
- Measured Claude cost: ≈ $0.0017/call (CM-E004, lean config).

## Family taxonomy (fixed before any calibration result is seen)

Lineages Claude / Qwen / Llama / Gemma / Phi / Mistral / DeepSeek are
distinct families. Two sizes or versions of one lineage are SAME family
(qwen2.5 vs qwen3 = same family). A model distilled onto another lineage's
base counts as the BASE's family (so deepseek-r1-distill-qwen* = Qwen; such
distills are not additional families). For this experiment the worker is
Claude, so every local candidate is cross-family; the taxonomy binds
interpretation and any later local-local follow-up.

## Seed namespaces (binding)

Three pairwise-disjoint namespaces, asserted disjoint by the harness at
startup: (1) pipeline seeds 50260904* (archived CM-E004 runs and Stage 2);
(2) calibration seeds (Stage 0 sweep + winner-confirmation block); (3)
extension seeds (Stage 1 battery extension chains). Selection never sees
battery items; battery items never come from calibration seeds.

## Stage -1 — Free forensic pass (no model calls; pure log analysis)

Compute and report, descriptively (NO stop gate — v1's gate was logically
inverted: a large input-conditional collision rate is the hypothesized
mechanism, not a deflation of it):

1. Pooled cross-input chance-collision null from steps.jsonl wrong-value
   distributions. Predicted ≈ 0 — wrong-value support is input-specific
   (0/122 cross-input recurrences in E004 Arm B). Establishes that observed
   collisions are not chance value-matching.
2. The cross-arm same-input worker-worker collision rate (the 15/50 = 30%
   benchmark above) with a 95% CI — the empirical same-model attractor rate
   battery collision rates are read against.

## Stage 0 — Calibration gate (binding; Claude cap $1)

1. Haiku reference: raw recompute error under the exact verifier prompt on a
   fresh ~250-step battery from calibration seeds (lean config; provider
   default temperature — see temperature policy below). The first 25 calls
   double as the Stage-0 cost pilot: they set the cost/call baseline, and
   the kill-switch is active for the remainder. The measured error rate is
   the binding matching target.
2. Local candidate sweep ($0, held-out): candidate = a (model, think-flag)
   CONFIGURATION. ≤8 configurations × ~100 calls (~800 local calls) on the
   same held-out calibration items: qwen3:30b-a3b think-off; qwen3:14b think
   on/off; qwen3:8b think on/off; gemma3:27b; phi-4:14b; mistral-small.
   (Ollama think flag plumbed into the adapter first; unit-tested.) All
   local candidates run at temperature 0.
3. Selection: configuration minimizing |err − haiku Stage-0 error|, required
   within ±5 percentage points.
4. Winner confirmation (anti-winner's-curse, $0): the selected configuration
   is re-measured on a fresh ~250-item confirmation block (disjoint
   calibration seeds); the ±5pp band binds on the CONFIRMATION measurement.

**K1 (kill):** no configuration within band on confirmation → STOP, write
NOTE.md, report; the fallback (transformed verification, CM-E003 rec 3b) is
a separate future pre-registration, not an amendment.

**Temperature policy (documented asymmetry):** the Claude Code CLI exposes
no temperature control, so haiku runs at provider default in every stage —
exactly as in CM-E003/E004 — while local candidates run at temperature 0,
matching E004's arm conditions. The asymmetry is inherited from the archived
baseline, applies identically in calibration and battery (so the matching
target and the battery see the same haiku sampling), and is reported in
RESULTS as a limitation.

## Stage 1 — Collision battery (PRIMARY; Claude cap $5)

**Battery:** the 129 recorded Arm A worker-error steps (inputs `current` +
exact wrong values `worker_raw_value` from
results/CM-E004/main-same/steps.jsonl; feasibility verified against the logs
2026-09-05), EXTENDED to **≥420 total error events** by fresh haiku worker
calls on new chains from extension seeds (~1,455 calls expected at ~20%
error). Extension chains carry accepted (possibly wrong) values forward —
ground truth never enters the execution path; a worker error is scored
post-hoc as output ≠ correct function of the PRESENTED input.

**Order + adaptive rule (reference-first, type-I preserving):** the haiku
reference arm runs first. After its first 150 items, C_ref is re-estimated
and the required n is recomputed by the pre-registered formula
n = ceil(power_n(C_ref, C_ref/2, 0.80, one-sided α=0.05, exact test)),
capped by the Stage-1 dollar cap, blind to all test-arm data. Then the
matched candidate scores the identical items ($0, local).

Each error event is presented to each verifier as a blind recompute
(verifier prompt, one sample; haiku at provider default, candidate at temp
0); scoring is post-hoc replay.

**Primary endpoint:** conditional collision rate. For battery error item i
(input x_i, worker wrong value w_i), verifier v's output is y_v(i);
collision indicator X_v(i) = 1[y_v(i) == w_i]. C_ref and C_test are means
over the identical N items.
**Primary test:** one-sided exact McNemar on the paired indicators:
b = #{X_ref=1, X_test=0}, c = #{X_ref=0, X_test=1};
p = exact binomial P(X ≥ b | b+c trials, ½), α = 0.05 (alternative: the
same-family reference collides more).
**Effect size:** R = 1 − C_test/C_ref, 95% CI from 10,000 bootstrap
resamples clustered by source chain (events cluster within chains; a
cluster-robust sensitivity p accompanies the primary McNemar p).
**Descriptive context (no subtraction, no test):** the pooled chance null
E_v = Σ_i q̂_v(w_i) (expected ≈ 0) and the 15/50 attractor benchmark.
**Secondary:** raw collision counts with one-sided Fisher (legacy
comparability); P(collision | both wrong); each verifier's raw error on the
battery error items — a **binding battery-conditional matching check**: the
two verifiers' raw recompute error on battery items must agree within ±5pp
or the H-family interpretation is downgraded to descriptive (the battery is
error-selected, i.e. hard-for-haiku inputs; matching on average items need
not transfer). Candidate raw error on the recorded non-error items ($0,
local) is reported against haiku's historical 36/511 with the asymmetry
noted. Per-family verified-outcome ledger rows are emitted (see Ledger).

**Success:** McNemar p < 0.05 AND R ≥ 0.50.
**K2 (kill):** McNemar p ≥ 0.05 OR R < 0.50 → the family-decorrelation
claim DIES; record "capability, not family, is the operative variable";
revise the CM-E004 write-up wording; do NOT run Stage 2. (Either outcome
still supports the standing CM-E004 deployment result.)

**Power (computed, not asserted):** exact-test power at 420 events/arm for
9.30% → 4.65% is ~0.80-0.81 (normal approx n=370; Fleiss-corrected n=412;
simulation 0.81 at 412); at 350 it is only ~0.74-0.75, and the 129 recorded
events alone give ~0.33-0.43 — hence the pre-registered extension BEFORE any
peeking. The COMPOUND rule (p<0.05 AND R≥0.50) has ~0.53 power against a
true exact halving at any n (the point estimate sits on the threshold) and
~0.88 against a true 65% reduction: this experiment reliably detects LARGE
decorrelation effects (E004 observed 100%); a true-but-modest halving may be
killed, and K2's wording reflects that this is by design — the family claim
is only worth carrying forward if the effect is large.

## Checkpoint — before Stage 2 (explicit second go/no-go)

If Stage 1 succeeds, Stage 2 does NOT auto-start. Shane is shown: Stage-1
verdict, actual spend to date, and a fresh Stage-2 dollar figure whose
baseline comes from a ~20-call Stage-2 pilot in the EXACT pipeline
configuration (plus the archived Arm B reference of $1.30/762 worker
calls). Stage 2 proceeds only on his approval.

## Stage 2 — Pipeline confirmation (ONLY after the checkpoint; Claude cap $3)

One 640-step verified_team arm: worker haiku, verifier = matched candidate,
seed-base 50260904, horizons 10/20/50 × 8 — paired against the ARCHIVED
CM-E004 Arm A (identical seeds, worker, ops; ONE disclosed verification-path
difference: local escalation-vote samples at temperature 0.7, because the
documented temp-0 triple-count artifact is dangerous with a fallible
verifier — attribution therefore reads "family swap + vote-sampling fix",
not "family swap alone").
**Endpoint:** correlated_agreement_escapes 12 → **≤4**/640 (one-sided Fisher
p = 0.037; note 5/640 gives p = 0.070 and FAILS α = 0.05). Stage 2 is
powered only for near-elimination: under a true pipeline halving,
P(≤4) ≈ 0.29 — it is a confirmation gate for large effects, per K2's logic.
Net escapes, false challenges, R(h), cost, latency: DESCRIPTIVE ONLY (a
matched-mediocre verifier is EXPECTED to raise false challenges; not a kill
signal here). Kill-switch baseline: the Stage-2 pilot's cost/call.

Pre-run harness changes (each unit-tested, committed before any run):
1. Ollama think-flag support in the adapter.
2. Local escalation-vote samples at temperature 0.7 (+ unit test).
3. Battery-replay script (~150 LOC) reusing steps.jsonl + the post-hoc
   scoring path, with a no-hidden-oracle test.
4. Cost kill-switch (below) + seed-namespace disjointness assertion.

## Per-family outcome ledger (starts here)

`results/ledger/family_outcomes.jsonl` — one row per (experiment, model
configuration, role): {date, experiment, model, family, role, task_family,
n_calls, raw_error_rate, collisions, notes}. Emitted by Stage 0/1/2 scoring
and by every future experiment. Private (not part of the public write-up's
data release); this is the seed of the commercial per-family performance
asset.

## Cost table (per the 2026-09-05 cost rules)

"Budgeted worst" = 1.5× expected — the planning buffer. The TRUE worst case
(the CM-E004 context-injection class was 20-230×) is bounded not by this
table but by the kill-switch and the hard caps below.

| Item | Calls (expected) | $ expected | $ budgeted worst (×1.5) | Cap |
|---|---|---|---|---|
| Stage -1 forensic pass | 0 model calls | 0 | 0 | — |
| Stage 0 haiku verifier calibration (first 25 calls = cost pilot) | ~250 | 0.43 | 0.65 | $1 |
| Stage 0 local sweep (≤8 configs) | ~800 local | 0 | 0 | — |
| Stage 0 winner confirmation | ~250 local | 0 | 0 | — |
| Stage 1 pilot (exact battery config, longest-step sample) | ~30 | 0.05 | 0.08 | in $5 |
| Stage 1 battery extension (worker calls) | ~1,455 | 2.47 | 3.71 | in $5 |
| Stage 1 haiku reference recomputes | ~420 | 0.71 | 1.07 | in $5 |
| Stage 1 candidate recomputes | ~420 local | 0 | 0 | — |
| Stage 2 pipeline arm (worker calls; verifier local) | ~950 + 20 pilot | 1.65 | 2.48 | $3 |
| **Campaign total** | | **≈ 5.3** | **≈ 8.0** | **$8 hard** |

Stage caps ($1 + $5 + $3 = $9) are per-stage maxima; the **campaign hard cap
$8** binds overall and is never raised. Budgeted-worst projection ≈ $7.99
fits it with no slack — if Stage 1's adaptive rule pushes n above ~420, the
overage comes out of Stage 2's headroom or Stage 2 is descoped at the
checkpoint; the $8 cap does not move. GPU ≤ 10 h total; wall-clock ≈ 2-3
days end to end (Stage 0 hours; battery overnight; Stage 2 overnight).

**Cost-control mechanics (binding):**
- Every stage has a pilot in its EXACT configuration before volume spend
  (Stage 0: its first 25 calls; Stage 1: the ~30-call longest-step pilot;
  Stage 2: a ~20-call pipeline pilot at the checkpoint). Each pilot's
  measured cost/call is the kill-switch baseline for that stage, and Stage
  1's extrapolated dollar figure is shown to Shane before the battery
  proceeds.
- Automatic kill-switch: an invocation aborts if the rolling mean cost/call
  over the last 25 calls exceeds 1.5× its stage baseline, or any single
  call exceeds 3× — the CM-E004 silent-inflation failure class cannot burn
  money unnoticed.
- Every invocation carries `--budget-cap-usd` at or below its stage cap;
  caps never raised mid-experiment; per-call spend logged continuously to
  runs.jsonl/steps.jsonl.
- Any scope or configuration change voids this estimate: new table, new
  approval.
- No cloud-API arm exists in this experiment; a cross-frontier verifier arm
  is a SEPARATE future line item requiring Shane's explicit approval.

## Standing invariants (unchanged from CM-E003/E004)

Paired seeds; ground truth never in any prompt or execution path; post-hoc
replay scoring; per-call served-model assertion (dated ID); lean
CLAUDE_CONFIG_DIR with --strict-mcp-config and scrubbed env; aborted runs
and negative results preserved with NOTE.md; RESULTS-CM-E005A.md is
adversarially audited against raw steps.jsonl before being believed.

## Relation to other candidates

The free 10× all-local replication (CM-E004 rec 2) is DEFERRED, not dropped:
it becomes the contingent follow-up if Stage 1 lands in the ambiguous zone
(significant but R near 0.50) or if a local-worker replication of the
ceiling is wanted for the write-up. CM-E005b (second task family) follows
the E005a readout either way.

## Deliverables

RESULTS-CM-E005A.md (verdict vs pre-registered endpoints first, incl. the
15/50 attractor benchmark beside both collision rates), raw data under
results/CM-E005A/, the started family-outcome ledger, and — either way K2
resolves — the corrected wording for the public write-up.
