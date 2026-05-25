from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


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
    "EvidenceUseReviewerAgent",
    "SectionContractReviewerAgent",
    "ClaimAuditAgent",
    "ReportQualityReviewerAgent",
    "DriftReviewerAgent",
    "KillArgumentAgent",
    "ReportAssembler",
    "IntegrationAgent",
]

RUNTIME_PROFILES = {"notebooklm_only", "api_assisted"}
DRIVERS = {"codex", "api"}
API_PROVIDERS = {"openai", "anthropic"}
API_DRIVER_SUPPORTED_AGENTS = {"SectionComposerAgent"}
KNOWLEDGE_AGENT_NAMES = {"NotebookLMAdapter"}


@dataclass(frozen=True)
class AgentRuntime:
    profile: str
    default_driver: str
    knowledge_runtime: dict[str, Any]
    orchestrator: dict[str, Any]
    api_providers: dict[str, dict[str, Any]]
    agents: dict[str, dict[str, Any]]
    capability_policy: dict[str, Any]
    unsupported_config: list[str]

    @property
    def mode(self) -> str:
        return self.profile

    def agent_config(self, agent_name: str) -> dict[str, Any]:
        return self.agents.get(agent_name, self.agents.get("default", {"driver": self.default_driver}))

    def driver_for(self, agent_name: str) -> str:
        return str(self.agent_config(agent_name).get("driver", self.default_driver))

    def validate(self) -> list[dict[str, str]]:
        issues: list[dict[str, str]] = []
        if self.profile not in RUNTIME_PROFILES:
            issues.append(
                {
                    "severity": "ERROR",
                    "agent": "*",
                    "message": f"Unknown runtime_profile: {self.profile}. Expected notebooklm_only or api_assisted.",
                }
            )

        if self.default_driver not in DRIVERS:
            issues.append(
                {
                    "severity": "ERROR",
                    "agent": "*",
                    "message": f"Unknown default_driver: {self.default_driver}. Expected codex or api.",
                }
            )

        if self.knowledge_runtime.get("provider") != "notebooklm_cli":
            issues.append(
                {
                    "severity": "ERROR",
                    "agent": "NotebookLMAdapter",
                    "message": "Knowledge runtime must use provider: notebooklm_cli.",
                }
            )

        allowed_calls = self.capability_policy.get("external_calls")
        expected_calls = ["notebooklm_cli"] if self.profile == "notebooklm_only" else ["notebooklm_cli", "llm_api"]
        if _normalize_calls(allowed_calls) != expected_calls:
            issues.append(
                {
                    "severity": "ERROR",
                    "agent": "*",
                    "message": f"Capability policy external_calls must be exactly {expected_calls}.",
                }
            )

        expected_llm_api = self.profile == "api_assisted"
        if self.capability_policy.get("llm_api") is not expected_llm_api:
            issues.append(
                {
                    "severity": "ERROR",
                    "agent": "*",
                    "message": f"Capability policy must set llm_api: {str(expected_llm_api).lower()} for {self.profile}.",
                }
            )

        if self.capability_policy.get("notebooklm_skill_mutation") is not False:
            issues.append(
                {
                    "severity": "ERROR",
                    "agent": "*",
                    "message": "Capability policy must set notebooklm_skill_mutation: false.",
                }
            )

        if self.orchestrator.get("driver") != "codex":
            issues.append(
                {
                    "severity": "ERROR",
                    "agent": "IntegrationAgent",
                    "message": "The main orchestrator must remain Codex-driven.",
                }
            )

        for item in self.unsupported_config:
            issues.append(
                {
                    "severity": "ERROR",
                    "agent": "*",
                    "message": f"Unsupported runtime config: {item}. Use agent_runtime.api_providers and per-agent provider/model fields.",
                }
            )

        for agent_name, config in self.agents.items():
            if agent_name == "default":
                continue
            driver = str(config.get("driver", self.default_driver))
            if driver not in DRIVERS:
                issues.append(
                    {
                        "severity": "ERROR",
                        "agent": agent_name,
                        "message": f"Unknown driver: {driver}. Expected codex or api.",
                    }
                )
                continue
            if agent_name in KNOWLEDGE_AGENT_NAMES and driver != "codex":
                issues.append(
                    {
                        "severity": "ERROR",
                        "agent": agent_name,
                        "message": "NotebookLMAdapter is the knowledge gateway and cannot be switched to an API driver.",
                    }
                )
            if driver == "api":
                issues.extend(self._validate_api_agent(agent_name, config))
        return issues

    def _validate_api_agent(self, agent_name: str, config: dict[str, Any]) -> list[dict[str, str]]:
        issues: list[dict[str, str]] = []
        if self.profile != "api_assisted":
            issues.append(
                {
                    "severity": "ERROR",
                    "agent": agent_name,
                    "message": "API drivers are only allowed when runtime_profile is api_assisted.",
                }
            )
        if agent_name not in API_DRIVER_SUPPORTED_AGENTS:
            issues.append(
                {
                    "severity": "ERROR",
                    "agent": agent_name,
                    "message": "This agent is not wired to the API execution path yet.",
                }
            )

        provider_name = str(config.get("provider", ""))
        model = str(config.get("model", ""))
        provider = self.api_providers.get(provider_name, {})
        if provider_name not in API_PROVIDERS:
            issues.append(
                {
                    "severity": "ERROR",
                    "agent": agent_name,
                    "message": f"Unsupported API provider: {provider_name}. Expected openai or anthropic.",
                }
            )
        elif provider_name not in self.api_providers:
            issues.append(
                {
                    "severity": "ERROR",
                    "agent": agent_name,
                    "message": f"Missing agent_runtime.api_providers.{provider_name} configuration.",
                }
            )
        if not model:
            issues.append({"severity": "ERROR", "agent": agent_name, "message": "API agent must set a model."})

        api_key_env = str(provider.get("api_key_env", ""))
        if not api_key_env:
            issues.append(
                {
                    "severity": "ERROR",
                    "agent": agent_name,
                    "message": f"Provider {provider_name or '<missing>'} must set api_key_env.",
                }
            )
        elif not os.environ.get(api_key_env):
            issues.append(
                {
                    "severity": "ERROR",
                    "agent": agent_name,
                    "message": f"Missing environment variable for API provider: {api_key_env}.",
                }
            )

        if not provider.get("base_url"):
            issues.append(
                {
                    "severity": "ERROR",
                    "agent": agent_name,
                    "message": f"Provider {provider_name or '<missing>'} must set base_url.",
                }
            )
        return issues

    def manifest(self) -> dict[str, Any]:
        return {
            "runtime_profile": self.profile,
            "default_driver": self.default_driver,
            "knowledge_runtime": self.knowledge_runtime,
            "orchestrator": self.orchestrator,
            "capability_policy": self.capability_policy,
            "api_providers": {
                name: {
                    "base_url": provider.get("base_url"),
                    "api_key_env": provider.get("api_key_env"),
                    "default_model": provider.get("default_model"),
                }
                for name, provider in self.api_providers.items()
            },
            "agents": {
                agent_name: {
                    "driver": config.get("driver", self.default_driver),
                    "provider": config.get("provider"),
                    "model": config.get("model"),
                }
                for agent_name, config in self.agents.items()
            },
        }

    def complete_text(self, agent_name: str, prompt: str) -> str:
        config = self.agent_config(agent_name)
        if config.get("driver") != "api":
            raise RuntimeError(f"{agent_name} is configured for Codex/local execution, not API execution.")
        validation = self._validate_api_agent(agent_name, config)
        if validation:
            raise RuntimeError(f"API runtime is invalid for {agent_name}: {validation}")

        provider_name = str(config["provider"])
        provider = self.api_providers[provider_name]
        if provider_name == "openai":
            return _complete_openai(provider, config, prompt)
        if provider_name == "anthropic":
            return _complete_anthropic(provider, config, prompt)
        raise RuntimeError(f"Unsupported API provider: {provider_name}")


def build_agent_runtime(config: dict[str, Any] | None) -> AgentRuntime:
    config = config or {}
    profile = _profile_from_config(config)
    default_driver = _normalize_driver(config.get("default_driver", config.get("mode", "codex")))
    knowledge_runtime = dict(config.get("knowledge_runtime", {}))
    knowledge_runtime.setdefault("provider", "notebooklm_cli")
    orchestrator = dict(config.get("orchestrator", {}))
    orchestrator["driver"] = _normalize_driver(orchestrator.get("driver", "codex"))

    capability_policy = dict(config.get("capability_policy", {}))
    if not capability_policy:
        capability_policy = _default_capability_policy(profile)

    unsupported_config: list[str] = []
    if "provider_defaults" in config:
        unsupported_config.append("agent_runtime.provider_defaults")

    api_providers = _build_api_providers(config.get("api_providers", {}))
    agents = {"default": {"driver": default_driver}}
    raw_agents = config.get("agents", {}) if isinstance(config.get("agents", {}), dict) else {}
    for agent_name in AGENT_NAMES:
        raw = dict(raw_agents.get(agent_name, {}))
        agents[agent_name] = _build_agent_config(agent_name, raw, default_driver, api_providers)

    for agent_name in raw_agents:
        if agent_name not in AGENT_NAMES:
            unsupported_config.append(f"agent_runtime.agents.{agent_name}")

    return AgentRuntime(
        profile=profile,
        default_driver=default_driver,
        knowledge_runtime=knowledge_runtime,
        orchestrator=orchestrator,
        api_providers=api_providers,
        agents=agents,
        capability_policy=capability_policy,
        unsupported_config=unsupported_config,
    )


def _profile_from_config(config: dict[str, Any]) -> str:
    if config.get("runtime_profile"):
        return str(config["runtime_profile"])
    legacy_mode = str(config.get("mode", "local"))
    if legacy_mode in {"api", "api_assisted"}:
        return "api_assisted"
    return "notebooklm_only"


def _default_capability_policy(profile: str) -> dict[str, Any]:
    if profile == "api_assisted":
        return {
            "external_calls": ["notebooklm_cli", "llm_api"],
            "llm_api": True,
            "notebooklm_skill_mutation": False,
        }
    return {
        "external_calls": ["notebooklm_cli"],
        "llm_api": False,
        "notebooklm_skill_mutation": False,
    }


def _build_api_providers(raw_providers: Any) -> dict[str, dict[str, Any]]:
    providers: dict[str, dict[str, Any]] = {}
    if isinstance(raw_providers, dict):
        for name, raw in raw_providers.items():
            if name not in API_PROVIDERS or not isinstance(raw, dict):
                continue
            providers[name] = {
                "base_url": raw.get("base_url", _default_base_url(name)),
                "api_key_env": raw.get("api_key_env", _default_api_key_env(name)),
                "default_model": raw.get("default_model", raw.get("model", "")),
                "temperature": raw.get("temperature", 0.2),
                "max_tokens": raw.get("max_tokens", 1800),
            }
    for name in API_PROVIDERS:
        providers.setdefault(
            name,
            {
                "base_url": _default_base_url(name),
                "api_key_env": _default_api_key_env(name),
                "default_model": "",
                "temperature": 0.2,
                "max_tokens": 1800,
            },
        )
    return providers


def _build_agent_config(
    agent_name: str,
    raw: dict[str, Any],
    default_driver: str,
    api_providers: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    api_block = raw.get("api") if isinstance(raw.get("api"), dict) else {}
    driver = _normalize_driver(raw.get("executor", raw.get("driver", default_driver)))
    provider = str(raw.get("provider", api_block.get("provider", "openai")))
    provider_config = api_providers.get(provider, {})
    model = str(raw.get("model", api_block.get("model", provider_config.get("default_model", ""))))
    return {
        "driver": driver,
        "provider": provider,
        "model": model,
        "temperature": raw.get("temperature", api_block.get("temperature", provider_config.get("temperature", 0.2))),
        "max_tokens": raw.get("max_tokens", api_block.get("max_tokens", provider_config.get("max_tokens", 1800))),
        "api_supported": agent_name in API_DRIVER_SUPPORTED_AGENTS,
    }


def _normalize_driver(value: Any) -> str:
    text = str(value or "codex").lower()
    if text == "local":
        return "codex"
    return text


def _normalize_calls(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    known_order = ["notebooklm_cli", "llm_api"]
    values = [str(item) for item in value]
    if any(item not in known_order for item in values):
        return values
    return [item for item in known_order if item in values]


def _default_base_url(provider: str) -> str:
    if provider == "anthropic":
        return "https://api.anthropic.com/v1"
    return "https://api.openai.com/v1"


def _default_api_key_env(provider: str) -> str:
    if provider == "anthropic":
        return "ANTHROPIC_API_KEY"
    return "OPENAI_API_KEY"


def _complete_openai(provider: dict[str, Any], config: dict[str, Any], prompt: str) -> str:
    payload = {
        "model": config["model"],
        "messages": [
            {
                "role": "system",
                "content": "You are a bounded policy report writing agent. Use only the provided material and preserve visible MATERIAL_NEEDED gaps.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": float(config.get("temperature", provider.get("temperature", 0.2))),
        "max_tokens": int(config.get("max_tokens", provider.get("max_tokens", 1800))),
    }
    data = _post_json(
        _join_url(str(provider["base_url"]), "chat/completions"),
        payload,
        {
            "Authorization": f"Bearer {os.environ[str(provider['api_key_env'])]}",
            "Content-Type": "application/json",
        },
    )
    return str(data["choices"][0]["message"]["content"]).strip()


def _complete_anthropic(provider: dict[str, Any], config: dict[str, Any], prompt: str) -> str:
    payload = {
        "model": config["model"],
        "max_tokens": int(config.get("max_tokens", provider.get("max_tokens", 1800))),
        "temperature": float(config.get("temperature", provider.get("temperature", 0.2))),
        "messages": [{"role": "user", "content": prompt}],
    }
    data = _post_json(
        _join_url(str(provider["base_url"]), "messages"),
        payload,
        {
            "x-api-key": os.environ[str(provider["api_key_env"])],
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
    )
    content = data.get("content", [])
    return "\n".join(str(part.get("text", "")) for part in content if isinstance(part, dict)).strip()


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    request = Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urlopen(request, timeout=120) as response:  # noqa: S310 - user-configured API endpoint.
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API request failed with HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise RuntimeError(f"API request failed: {exc.reason}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("API response was not a JSON object.")
    return data


def _join_url(base_url: str, suffix: str) -> str:
    return f"{base_url.rstrip('/')}/{suffix.lstrip('/')}"
