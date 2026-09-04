from __future__ import annotations

from dataclasses import dataclass
import json
import time
from typing import Any, Dict, Protocol
from urllib import request, error


@dataclass
class ModelResponse:
    content: str
    structured: Dict[str, Any]
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_seconds: float = 0.0


class ModelAdapter(Protocol):
    """Provider-neutral contract for the real-LLM phase."""

    name: str

    def invoke(
        self,
        *,
        system: str,
        user: str,
        schema: Dict[str, Any] | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> ModelResponse:
        ...


class OpenAICompatibleHTTPAdapter:
    """Dependency-free adapter for OpenAI-compatible chat-completions APIs.

    This intentionally uses urllib instead of a provider SDK so Corpus Mesh can
    run against OpenAI-compatible cloud gateways and local servers without an
    extra Python dependency. The endpoint must expose a /chat/completions-style
    API. Provider-specific pricing is optional and can be supplied per million
    input/output tokens for honest matched-budget accounting.
    """

    def __init__(
        self,
        *,
        endpoint: str,
        api_key: str,
        model: str,
        input_cost_per_million: float = 0.0,
        output_cost_per_million: float = 0.0,
        timeout_seconds: float = 120.0,
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.name = f"openai-compatible:{model}"
        self.input_cost_per_million = input_cost_per_million
        self.output_cost_per_million = output_cost_per_million
        self.timeout_seconds = timeout_seconds

    def invoke(
        self,
        *,
        system: str,
        user: str,
        schema: Dict[str, Any] | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> ModelResponse:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0,
        }
        if schema is not None:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "corpus_mesh_response",
                    "strict": True,
                    "schema": schema,
                },
            }

        req = request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        started = time.perf_counter()
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:1000]
            raise RuntimeError(f"model HTTP {exc.code}: {body}") from exc
        latency = time.perf_counter() - started

        choice = raw.get("choices", [{}])[0]
        content = choice.get("message", {}).get("content", "")
        if isinstance(content, list):
            content = "".join(str(x.get("text", "")) if isinstance(x, dict) else str(x) for x in content)
        structured: Dict[str, Any] = {}
        if content:
            try:
                parsed = json.loads(content)
                if isinstance(parsed, dict):
                    structured = parsed
            except json.JSONDecodeError:
                structured = {}

        usage = raw.get("usage", {}) or {}
        input_tokens = int(usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0)
        output_tokens = int(usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0)
        cost = (
            input_tokens * self.input_cost_per_million / 1_000_000
            + output_tokens * self.output_cost_per_million / 1_000_000
        )
        return ModelResponse(
            content=content,
            structured=structured,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_seconds=latency,
        )
