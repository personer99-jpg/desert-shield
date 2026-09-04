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
