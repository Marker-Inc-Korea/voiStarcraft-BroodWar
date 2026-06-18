from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable

from .models import ParsedCommand
from .schema import SchemaError, parse_command_dict


class StrictLLMCommandParser:
    """Validates LLM JSON output before it can reach runtime state."""

    def parse_json(self, content: str) -> list[ParsedCommand]:
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise SchemaError(f"invalid JSON from LLM: {exc}") from exc
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list):
            raise SchemaError("LLM output must be a command object or list of command objects")
        return [parse_command_dict(item) for item in data]


Requester = Callable[[urllib.request.Request, float], bytes]


@dataclass(frozen=True)
class LLMProviderConfig:
    api_key: str
    model: str
    base_url: str = "https://api.openai.com/v1/chat/completions"
    timeout_seconds: float = 30.0

    @classmethod
    def from_env(cls) -> "LLMProviderConfig":
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("VOI_LLM_API_KEY")
        if not api_key:
            raise SchemaError("missing OPENAI_API_KEY or VOI_LLM_API_KEY")
        return cls(
            api_key=api_key,
            model=os.environ.get("VOI_LLM_MODEL", "gpt-4.1-mini"),
            base_url=os.environ.get("VOI_LLM_BASE_URL", "https://api.openai.com/v1/chat/completions"),
            timeout_seconds=float(os.environ.get("VOI_LLM_TIMEOUT_SECONDS", "30")),
        )


class OpenAICompatibleCommandParser:
    """Calls an OpenAI-compatible chat-completions endpoint, then applies the strict JSON gate."""

    def __init__(
        self,
        config: LLMProviderConfig,
        requester: Requester | None = None,
        strict_parser: StrictLLMCommandParser | None = None,
    ) -> None:
        self.config = config
        self.requester = requester or self._default_requester
        self.strict_parser = strict_parser or StrictLLMCommandParser()

    def parse_text(self, text: str) -> list[ParsedCommand]:
        content = self._complete(text)
        return self.strict_parser.parse_json(content)

    def _complete(self, text: str) -> str:
        payload = {
            "model": self.config.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Convert the user's Brood War commander instruction into strict JSON matching the "
                        "voi-bw-commander ParsedCommand schema. Return one command object or an array only."
                    ),
                },
                {"role": "user", "content": text},
            ],
        }
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.config.base_url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            raw = self.requester(request, self.config.timeout_seconds)
        except urllib.error.URLError as exc:
            raise SchemaError(f"LLM provider request failed: {exc}") from exc
        try:
            data = json.loads(raw.decode("utf-8"))
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise SchemaError("LLM provider response did not contain choices[0].message.content") from exc

    @staticmethod
    def _default_requester(request: urllib.request.Request, timeout_seconds: float) -> bytes:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return response.read()
