# Corpus Mesh v0.1

An experimental, model-independent runtime for testing whether a self-auditing multi-agent architecture can reduce reliability decay on long-horizon tasks.

## What exists in v0.1

- machine-readable mesh blueprint and mutable topology controller;
- agent lifecycle: spawn, probation, promotion, retirement;
- domain-specific Bayesian-style reputation;
- structured provenance memory;
- belief dependency invalidation and downstream review marking;
- worker + independent verifier + adversary + hidden deterministic benchmark judge;
- replacement/retry path after detected failures;
- single-agent and self-reflection baselines;
- synthetic long-horizon benchmark and reliability-decay estimate;
- reproducible seeded runs with CSV/JSON outputs.

## Important limitation

The initial benchmark uses simulated agents with configurable error rates. It is an **engineering validation harness**, not evidence that Corpus Mesh improves frontier LLMs. Its job is to verify the experimental machinery and make the architecture falsifiable before spending money on real-model runs.

The next phase is to add model adapters (OpenAI/Anthropic/Gemini or local models), matched token/cost budgets, and real benchmark environments.

## Run

```bash
python -m corpus_mesh --runs 200 --horizons 10 25 50 100 250 --out results/latest
```

or after installing:

```bash
pip install -e .
corpus-mesh-benchmark --runs 200
```

## Test

```bash
python -m pytest
```

## Research rule

Do not claim an improvement from the synthetic benchmark. A real result requires the same underlying model, same tools, comparable cost/compute budgets, repeated trials, and an external or deterministic grader.

## Real-model pilot (CM-E003A)

Corpus Mesh now includes a dependency-free OpenAI-compatible HTTP adapter. Configure any compatible model endpoint:

```bash
export CM_MODEL_API_KEY='...'
export CM_MODEL_NAME='...'
# defaults to OpenAI chat-completions; override for compatible gateways/local servers
export CM_MODEL_ENDPOINT='https://api.openai.com/v1/chat/completions'
python -m corpus_mesh.real_pilot --horizons 10 25 --runs 3
```

The harness uses the same underlying model for all architectures and records calls, tokens, estimated cost, error detection/recovery, and deterministic success.

## Real-model experiment (CM-E003) — completed

The full matched-model experiment lives in `corpus_mesh/e003.py` (see
`EXPERIMENTS.md` for the protocol and `RESULTS-CM-E003.md` for results and
verdict). It runs on the authenticated Claude Code CLI — no API key needed:

```bash
python -m corpus_mesh.e003 calibrate --samples 10 --out results/CM-E003/calibration.json
python -m corpus_mesh.e003 run --horizons 5 10 20 50 --runs 8 \
    --op-mix mul3_mod mul2_mod add_mul rev_add \
    --out results/CM-E003/main --budget-cap-usd 25
python -m corpus_mesh.e003_deep --out results/CM-E003/main   # mechanism analysis
```

To replicate on any OpenAI-compatible endpoint (e.g. a local vLLM/Ollama
server on your own GPU) instead of the Claude CLI:

```bash
export CM_MODEL_API_KEY='...'   # any non-empty string for most local servers
python -m corpus_mesh.e003 run --endpoint http://localhost:11434/v1/chat/completions \
    --model llama3.1:70b --horizons 5 10 20 50 --runs 8 --out results/CM-E004/local
```
