"""Claude Code CLI model adapter for CM-E003.

Uses the authenticated `claude` CLI in headless print mode so the experiment
can run on the model access already present in a Claude Code environment,
without a separate API key.

Isolation properties enforced per call:
- `--tools ""` disables every tool, so no agent can shell out to a calculator;
- `--system-prompt` replaces the default Claude Code system prompt with the
  experiment's small role prompt;
- `MAX_THINKING_TOKENS=0` disables extended thinking identically for every
  architecture (documented protocol choice: raises per-step error into a
  measurable range and keeps cost/latency comparable);
- `--no-session-persistence` keeps calls stateless.

The CLI's JSON envelope reports exact input/output tokens, list-price cost in
USD, API latency, and which canonical model served the call. The adapter
records all of it and raises if a call was served by a different model than
requested, which is how the harness enforces the "same model for every
architecture" requirement.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class CallResult:
    text: str
    value: Optional[int]
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_creation_tokens: int
    cost_usd: float
    latency_seconds: float
    model: str
    infra_retries: int = 0
    parse_ok: bool = True
    raw_envelope: Dict[str, Any] = field(default_factory=dict, repr=False)


_JSON_OBJ = re.compile(r"\{[^{}]*\}")


def extract_value(text: str) -> Optional[int]:
    """Pull the last parseable {"value": N} object out of free-form output."""
    result: Optional[int] = None
    for match in _JSON_OBJ.findall(text or ""):
        try:
            obj = json.loads(match)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict) or "value" not in obj:
            continue
        v = obj["value"]
        if isinstance(v, bool):
            continue
        if isinstance(v, int):
            result = v
        elif isinstance(v, float) and v.is_integer():
            result = int(v)
        elif isinstance(v, str):
            try:
                result = int(v.strip())
            except ValueError:
                continue
    return result


class ClaudeCLIAdapter:
    def __init__(
        self,
        *,
        model: str,
        claude_bin: str = "claude",
        timeout_seconds: float = 180.0,
        max_infra_retries: int = 3,
    ) -> None:
        self.model = model
        self.claude_bin = claude_bin
        self.timeout_seconds = timeout_seconds
        self.max_infra_retries = max_infra_retries
        self.name = f"claude-cli:{model}"

    def _env(self) -> Dict[str, str]:
        env = dict(os.environ)
        # Disable extended thinking for every call (matched across
        # architectures) and neutralize any inherited effort setting.
        env["MAX_THINKING_TOKENS"] = "0"
        env.pop("CLAUDE_EFFORT", None)
        return env

    def invoke(self, *, system: str, user: str, metadata: Optional[Dict[str, Any]] = None) -> CallResult:
        cmd = [
            self.claude_bin,
            "-p", user,
            "--system-prompt", system,
            "--tools", "",
            "--no-session-persistence",
            "--output-format", "json",
            "--model", self.model,
        ]
        last_err: Optional[str] = None
        for attempt in range(self.max_infra_retries + 1):
            started = time.perf_counter()
            try:
                proc = subprocess.run(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    env=self._env(),
                )
            except subprocess.TimeoutExpired:
                last_err = f"timeout after {self.timeout_seconds}s"
                time.sleep(2 ** attempt)
                continue
            wall = time.perf_counter() - started
            if proc.returncode != 0:
                last_err = f"exit {proc.returncode}: {proc.stderr[-500:]}"
                time.sleep(2 ** attempt)
                continue
            try:
                envelope = json.loads(proc.stdout)
            except json.JSONDecodeError:
                last_err = f"unparseable CLI envelope: {proc.stdout[:300]}"
                time.sleep(2 ** attempt)
                continue
            if envelope.get("is_error"):
                last_err = f"CLI error envelope: {str(envelope.get('result'))[:300]}"
                time.sleep(2 ** attempt)
                continue

            usage = envelope.get("usage", {}) or {}
            model_usage = envelope.get("modelUsage", {}) or {}
            served = sorted(model_usage.keys())
            canonical = {
                (v or {}).get("canonicalModel", k) for k, v in model_usage.items()
            }
            expected = self.model.split("-2")[0] if re.search(r"-2\d{7}$", self.model) else self.model
            if served and expected not in served and expected not in canonical:
                raise RuntimeError(
                    f"model mismatch: requested {self.model}, served {served} (canonical {sorted(canonical)})"
                )

            text = envelope.get("result") or ""
            value = extract_value(text)
            return CallResult(
                text=text,
                value=value,
                input_tokens=int(usage.get("input_tokens", 0) or 0),
                output_tokens=int(usage.get("output_tokens", 0) or 0),
                cache_read_tokens=int(usage.get("cache_read_input_tokens", 0) or 0),
                cache_creation_tokens=int(usage.get("cache_creation_input_tokens", 0) or 0),
                cost_usd=float(envelope.get("total_cost_usd", 0.0) or 0.0),
                latency_seconds=float(envelope.get("duration_api_ms", wall * 1000) or 0) / 1000.0,
                model=served[0] if served else self.model,
                infra_retries=attempt,
                parse_ok=value is not None,
                raw_envelope={
                    k: envelope.get(k)
                    for k in ("duration_api_ms", "duration_ms", "num_turns", "stop_reason")
                },
            )
        raise RuntimeError(f"claude CLI call failed after {self.max_infra_retries + 1} attempts: {last_err}")
