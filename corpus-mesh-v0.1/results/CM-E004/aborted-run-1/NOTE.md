# Aborted main run 1 (2026-09-04) — preserved per protocol

Arm A (main-same) ran to its $10 budget cap and stopped at 17/24 completed
runs (h=10 and h=20 complete, h=50 mostly aborted: 6 runs hit the cap, 1
failed on a harness crash). Arm B (main-hetero) was killed ~30 minutes in,
before any run completed. Spend: $10.08 (arm A) + ~$0.30 (arm B partial).

Two causes, both environmental, neither experimental:

1. **Context bloat (cost inflation ~20×).** Every Claude CLI call carried a
   ~45k-token cached context of claude.ai account-level MCP connector tool
   schemas (~130 tools: Google Drive, Gmail, Figma, Hugging Face, ...) that
   the CLI injects after an OAuth login populates its connector cache.
   `--tools ""` does not suppress them. Median cost was ~$0.006/call vs the
   ~$0.0003/call measured at pilot design time; the arm-A cap was hit at
   ~73% completion. Fix: `--strict-mcp-config` (verified: 129 input tokens,
   $0.00032/call, zero cache baseline).

2. **Windows decode crashes.** The adapter's `subprocess(text=True)` decoded
   CLI output as cp1252; UTF-8 bytes without cp1252 mappings (e.g. 0x9d)
   crashed runs intermittently (1 run FAILED with a TypeError; one thread
   traceback). Fix: `encoding="utf-8", errors="replace"` in
   `claude_cli.py` (also removes the `Ã—` mojibake seen in text snippets).

Decision: rather than completing the remaining runs under bloated-context
conditions (~$5+ more, and h=50 would still be thin), both arms were re-run
from scratch under the lean context so that every run in both arms shares
identical conditions (~$1.50 projected for the full re-run). The arms must
match each other; a mid-experiment context change between (or within) arms
would break the paired design.

These aborted results are NOT directly comparable to the fresh main run:
the 45k tool-schema preamble plausibly affects worker/verifier error rates.
They are preserved as evidence and for the spend accounting only.
