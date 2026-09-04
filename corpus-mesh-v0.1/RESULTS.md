# Corpus Mesh v0.1 — Initial Engineering Results

These are **synthetic harness-validation results**, not evidence of improved frontier AI capability.

> **Update 2026-09-04:** the real-model matched experiment has now been run —
> see **[RESULTS-CM-E003.md](RESULTS-CM-E003.md)**. Verdict: no meaningful
> improvement over a plain worker + blind-verifier team at the tested sample
> size; independent verification is the dominant mechanism; one mesh
> mechanism (verified retries) helped, one (arbitration tie-breaks)
> measurably hurt. The synthetic results below are preserved unchanged.

## Run 1 — universal adversary (rejected)

500 seeded trials per horizon; worker simulated error 1.5%, verifier error 0.5%, adversary error 1.0%.

At 250 steps:

| Architecture | Success | Avg agent calls |
|---|---:|---:|
| Single | 3.0% | 250.0 |
| Reflection | 4.8% | 319.9 |
| Static worker+verifier | 92.0% | 504.8 |
| Corpus Mesh, adversary every step | 91.6% | 764.5 |

Conclusion: adversarial review on every step was redundant and expensive. CM-0.1 did **not** beat the simpler static team. The design was rejected.

## Run 2 — selective blind adversarial audit (CM-0.1.1)

1,000 seeded trials per horizon. The verifier checks every claim; the adversary randomly audits 10% of verifier-approved high-risk claims.

At 250 steps:

| Architecture | Success | Avg agent calls |
|---|---:|---:|
| Single | 3.5% | 250.0 |
| Reflection | 5.0% | 319.4 |
| Static worker+verifier | 91.1% | 504.9 |
| Corpus Mesh selective audit | 92.0% | 534.4 |

Fitted exponential reliability-decay lambda across 10, 25, 50, 100, 250 steps:

| Architecture | lambda (lower is better) |
|---|---:|
| Single | 0.013295 |
| Reflection | 0.011846 |
| Static worker+verifier | 0.000373 |
| Corpus Mesh selective audit | 0.000318 |

Interpretation: selective monitoring removed most of the unnecessary overhead and produced a small positive signal in reliability decay. The 250-step success difference is too small to treat as statistically or scientifically decisive. It justifies further experiments.

## What the experiment already taught us

1. More agents are not automatically better.
2. Universal cross-monitoring wastes compute.
3. Independent verification is the dominant mechanism in this simple synthetic environment.
4. Selective/random adversarial audits are a better candidate than continuous adversarial review.
5. Cost must be measured beside reliability or the architecture can appear better merely by spending more inference.
6. The test harness caught a benchmark leak where simulated confidence originally revealed errors to the reflection baseline. That leak was removed before the recorded CM-0.1.1 run.

## Next scientific step

Replace simulated arithmetic agents with the same real LLM across all architectures and use objectively graded coding/terminal tasks. Hold model, tools, task distribution, and cost budget as constant as practical. Add ablations for provenance memory, reputation routing, fault injection, selective audit rate, and replacement policy.
