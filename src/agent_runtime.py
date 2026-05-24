from __future__ import annotations

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
    "EvidenceUseReviewerAgent",
    "SectionContractReviewerAgent",
    "ClaimAuditAgent",
    "ReportQualityReviewerAgent",
    "DriftReviewerAgent",
    "KillArgumentAgent",
    "ReportAssembler",
    "IntegrationAgent",
]

DRIVERS = {"local"}
API_DRIVER_SUPPORTED_AGENTS: set[str] = set()


@dataclass(frozen=True)
class AgentRuntime:
    mode: str
    agents: dict[str, dict[str, Any]]
    capability_policy: dict[str, Any]
    unsupported_config: list[str]

    def agent_config(self, agent_name: str) -> dict[str, Any]:
        return self.agents.get(agent_name, self.agents.get("default", {"driver": self.mode}))

    def driver_for(self, agent_name: str) -> str:
        return str(self.agent_config(agent_name).get("driver", self.mode))

    def validate(self) -> list[dict[str, str]]:
        issues: list[dict[str, str]] = []
        if self.mode != "local":
            issues.append(
                {
                    "severity": "ERROR",
                    "agent": "*",
                    "message": "Only local agent runtime is allowed; external LLM API drivers are disabled for NotebookLM-only execution.",
                }
            )
        allowed_calls = self.capability_policy.get("external_calls")
        if allowed_calls != ["notebooklm_cli"]:
            issues.append(
                {
                    "severity": "ERROR",
                    "agent": "*",
                    "message": "Capability policy must allow exactly one external call surface: ['notebooklm_cli'].",
                }
            )
        if self.capability_policy.get("llm_api") is not False:
            issues.append(
                {
                    "severity": "ERROR",
                    "agent": "*",
                    "message": "Capability policy must set llm_api: false.",
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
        for item in self.unsupported_config:
            issues.append(
                {
                    "severity": "ERROR",
                    "agent": "*",
                    "message": f"Unsupported external runtime config under NotebookLM-only policy: {item}",
                }
            )

        for agent_name, config in self.agents.items():
            if agent_name == "default":
                continue
            driver = str(config.get("driver", self.mode))
            if driver != "local":
                issues.append(
                    {
                        "severity": "ERROR",
                        "agent": agent_name,
                        "message": f"Only local driver is allowed for this workflow; found {driver}.",
                    }
                )
        return issues

    def manifest(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "capability_policy": self.capability_policy,
            "agents": {
                agent_name: {"driver": config.get("driver", "local")}
                for agent_name, config in self.agents.items()
            },
        }

    def complete_text(self, agent_name: str, prompt: str) -> str:
        raise RuntimeError(
            f"{agent_name} attempted to call an external LLM API. "
            "This project is currently constrained to local orchestration plus NotebookLM CLI retrieval only."
        )


def build_agent_runtime(config: dict[str, Any] | None) -> AgentRuntime:
    config = config or {}
    mode = str(config.get("mode", config.get("driver", "local")))
    default_driver = str(config.get("default_driver", "local"))
    capability_policy = dict(config.get("capability_policy", {}))
    if not capability_policy:
        capability_policy = {
            "external_calls": ["notebooklm_cli"],
            "llm_api": False,
            "notebooklm_skill_mutation": False,
        }

    agents = {"default": {"driver": default_driver}}
    unsupported_config: list[str] = []
    if "provider_defaults" in config:
        unsupported_config.append("agent_runtime.provider_defaults")
    for agent_name in AGENT_NAMES:
        raw = dict(config.get("agents", {}).get(agent_name, {}))
        if "api" in raw:
            unsupported_config.append(f"agent_runtime.agents.{agent_name}.api")
        agents[agent_name] = {"driver": str(raw.get("driver", default_driver))}
    return AgentRuntime(mode=mode, agents=agents, capability_policy=capability_policy, unsupported_config=unsupported_config)
