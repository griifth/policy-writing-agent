from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


AGENT_NAMES = [
    "QueryPlannerAgent",
    "NotebookLMAdapter",
    "MaterialPackAgent",
    "MatrixBuilderAgent",
    "SectionContractAgent",
    "SectionComposerAgent",
    "PlanReviewerAgent",
    "RetrievalCompletenessGate",
    "MaterialPackAudit",
    "MaterialCoverageReviewerAgent",
    "ClaimAuditAgent",
    "KillArgumentAgent",
    "ReportAssembler",
    "IntegrationAgent",
]

PROVIDERS = {"openai", "anthropic"}
DRIVERS = {"local", "llm_api"}
API_DRIVER_SUPPORTED_AGENTS = {
    "SectionContractAgent",
    "SectionComposerAgent",
}


@dataclass(frozen=True)
class AgentRuntime:
    mode: str
    agents: dict[str, dict[str, Any]]

    def agent_config(self, agent_name: str) -> dict[str, Any]:
        return self.agents.get(agent_name, self.agents.get("default", {"driver": self.mode}))

    def driver_for(self, agent_name: str) -> str:
        return str(self.agent_config(agent_name).get("driver", self.mode))

    def validate(self) -> list[dict[str, str]]:
        issues: list[dict[str, str]] = []
        if self.mode not in DRIVERS:
            issues.append({"severity": "ERROR", "agent": "*", "message": f"Unknown agent runtime mode: {self.mode}"})

        for agent_name, config in self.agents.items():
            if agent_name == "default":
                continue
            driver = str(config.get("driver", self.mode))
            if driver not in DRIVERS:
                issues.append({"severity": "ERROR", "agent": agent_name, "message": f"Unknown driver: {driver}"})
                continue
            if driver != "llm_api":
                continue
            if agent_name not in API_DRIVER_SUPPORTED_AGENTS:
                issues.append({"severity": "ERROR", "agent": agent_name, "message": "llm_api driver is not wired for this agent yet."})
                continue

            api = config.get("api", {})
            provider = str(api.get("provider", ""))
            if provider not in PROVIDERS:
                issues.append({"severity": "ERROR", "agent": agent_name, "message": f"Unknown provider: {provider}"})
            if not _api_model(api):
                issues.append({"severity": "ERROR", "agent": agent_name, "message": "Missing model or model_env."})
            api_key_env = str(api.get("api_key_env", ""))
            if not api_key_env:
                issues.append({"severity": "ERROR", "agent": agent_name, "message": "Missing api_key_env."})
            elif not os.environ.get(api_key_env):
                issues.append({"severity": "ERROR", "agent": agent_name, "message": f"Environment variable is not set: {api_key_env}"})
        return issues

    def manifest(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "agents": {
                agent_name: _redact_agent_config(config)
                for agent_name, config in self.agents.items()
            },
        }

    def complete_text(self, agent_name: str, prompt: str) -> str:
        config = self.agent_config(agent_name)
        if config.get("driver", self.mode) != "llm_api":
            raise RuntimeError(f"{agent_name} is configured for local driver, not llm_api.")
        api = config.get("api", {})
        provider = api.get("provider")
        if provider == "openai":
            return _complete_openai(api, prompt)
        if provider == "anthropic":
            return _complete_anthropic(api, prompt)
        raise RuntimeError(f"Unsupported provider for {agent_name}: {provider}")


def build_agent_runtime(config: dict[str, Any] | None) -> AgentRuntime:
    config = config or {}
    mode = str(config.get("mode", config.get("driver", "local")))
    default_driver = str(config.get("default_driver", mode))
    provider_defaults = config.get("provider_defaults", {})
    default_agent_config = {
        "driver": default_driver,
        "api": {},
    }
    agents = {"default": default_agent_config}

    for agent_name in AGENT_NAMES:
        raw = dict(config.get("agents", {}).get(agent_name, {}))
        driver = str(raw.get("driver", default_driver))
        api = _merge_api_config(provider_defaults, raw.get("api", {}))
        agents[agent_name] = {
            "driver": driver,
            "api": api,
        }
    return AgentRuntime(mode=mode, agents=agents)


def _merge_api_config(provider_defaults: dict[str, Any], api: dict[str, Any]) -> dict[str, Any]:
    provider = api.get("provider")
    merged: dict[str, Any] = {}
    if provider and isinstance(provider_defaults.get(provider), dict):
        merged.update(provider_defaults[provider])
    merged.update(api)
    return merged


def _api_model(api: dict[str, Any]) -> str:
    model_env = api.get("model_env")
    if model_env and os.environ.get(str(model_env)):
        return str(os.environ[str(model_env)])
    return str(api.get("model", ""))


def _redact_agent_config(config: dict[str, Any]) -> dict[str, Any]:
    api = dict(config.get("api", {}))
    api_key_env = api.get("api_key_env")
    if api_key_env:
        api["api_key_env_present"] = bool(os.environ.get(str(api_key_env)))
    api.pop("api_key", None)
    return {
        "driver": config.get("driver"),
        "api": api,
    }


def _complete_openai(api: dict[str, Any], prompt: str) -> str:
    api_key = os.environ[str(api["api_key_env"])]
    base_url = str(api.get("base_url", "https://api.openai.com/v1")).rstrip("/")
    body = {
        "model": _api_model(api),
        "input": prompt,
        "temperature": float(api.get("temperature", 0.2)),
        "max_output_tokens": int(api.get("max_tokens", api.get("max_output_tokens", 1200))),
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if api.get("organization"):
        headers["OpenAI-Organization"] = str(api["organization"])
    if api.get("project"):
        headers["OpenAI-Project"] = str(api["project"])
    payload = _post_json(f"{base_url}/responses", headers, body, int(api.get("timeout_sec", 120)))
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]
    chunks: list[str] = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if isinstance(text, str):
                chunks.append(text)
    if chunks:
        return "\n".join(chunks)
    raise RuntimeError("OpenAI response did not contain text output.")


def _complete_anthropic(api: dict[str, Any], prompt: str) -> str:
    api_key = os.environ[str(api["api_key_env"])]
    base_url = str(api.get("base_url", "https://api.anthropic.com")).rstrip("/")
    body = {
        "model": _api_model(api),
        "max_tokens": int(api.get("max_tokens", 1200)),
        "temperature": float(api.get("temperature", 0.2)),
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": str(api.get("anthropic_version", "2023-06-01")),
        "Content-Type": "application/json",
    }
    payload = _post_json(f"{base_url}/v1/messages", headers, body, int(api.get("timeout_sec", 120)))
    chunks = [
        item.get("text")
        for item in payload.get("content", [])
        if isinstance(item, dict) and isinstance(item.get("text"), str)
    ]
    if chunks:
        return "\n".join(chunks)
    raise RuntimeError("Anthropic response did not contain text output.")


def _post_json(url: str, headers: dict[str, str], body: dict[str, Any], timeout_sec: int) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_sec) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LLM API request failed with HTTP {exc.code}: {detail}") from exc
