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
