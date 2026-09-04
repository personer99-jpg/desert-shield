# Aborted main run 1 (preserved as-is)

Killed deliberately after 20 of 160 runs (~$0.45 spent) for two reasons:

1. A cosmetic double-brace artifact in the verifier system prompt
   (`{{"value": <integer>}}` — an f-string escape left in a string that is
   never `.format()`ed). Zero parse failures were observed, and the artifact
   was identical across architectures, so it was not a fairness confound —
   but restarting clean was cheaper than carrying the caveat.
2. Concurrency retuning: 8 CLI worker processes oversubscribed the 4-core
   container (load average 27), inflating wall-clock latencies that feed the
   recovery-latency metric. Restarted with 5 workers.

The restarted main run also trims horizon 35 (keeping 5/10/20/50) to fit the
CPU-bound call throughput budget. No results from this directory are used in
the CM-E003 analysis.
