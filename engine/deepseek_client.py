# -*- coding: utf-8 -*-
"""DeepSeek 外部调用客户端（direction_workflow · 执行引擎）。

移植来源：example1/workflow/deepseek_client.py（旧引擎真源只读，此为独立副本）。
原样保留的血换逻辑：
  - 空响应防护：content 为空即抛 DeepSeekEmptyResponseError，绝不把空结果当产物落盘
    （根因：finish_reason=length，推理 thinking 烧穿 max_tokens）；
  - 逐调用 thinking_enabled 覆盖：供逐级降级重试（原参 → effort=low → 关 thinking）使用，
    降级梯子本身在 run_entity.py（与旧引擎 report_pipeline._ask_deepseek 同款）。
本副本相对旧引擎的差异（均为独立可用所需，不改行为）：
  1. PROJECT_ROOT 上移两级指向包的上一级目录，默认 .env 即该目录下的 .env
     ——密钥不迁移、不复制、不入本目录；
  2. chat() 调用后在 self.last_meta 留存 token 用量与 finish_reason（run_entity 留痕用），
     不改变返回值与异常行为。
密钥纪律：本文件与本目录一律不写入、不打印任何密钥。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - 运行时给出更清晰的依赖错误
    OpenAI = None  # type: ignore[assignment]


# engine/ 位于 direction_workflow/engine/，parents[2] = 包的上一级目录
PROJECT_ROOT = Path(__file__).resolve().parents[2]
# 旧引擎既有 .env 位置（example1/.env）；strategic_response_workflow/.env 亦可经
# 环境变量 DEEPSEEK_ENV_PATH 或 run_entity.py --env 指定。
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"


class DeepSeekConfigError(RuntimeError):
    """DeepSeek 配置缺失或格式错误。"""


class DeepSeekEmptyResponseError(RuntimeError):
    """DeepSeek 返回空 content（偶发；调用方应重试，而非把空结果当产物落盘）。"""


def _ensure_project_path(path: str | Path) -> Path:
    """确保配置文件路径仍在当前项目内，避免越界读取。"""
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    resolved = candidate.resolve()
    root = PROJECT_ROOT.resolve()
    if resolved != root and root not in resolved.parents:
        raise DeepSeekConfigError(f"路径超出项目目录: {resolved}")
    return resolved


def _parse_env_file(env_path: Path = DEFAULT_ENV_PATH) -> dict[str, str]:
    """读取简单 .env 文件；不依赖 python-dotenv，便于独立运行。"""
    env_path = _ensure_project_path(env_path)
    if not env_path.exists():
        return {}

    values: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def _get_env_value(name: str, env_values: Mapping[str, str]) -> str | None:
    """优先使用进程环境变量，其次读取项目 .env 中的值。"""
    value = os.environ.get(name)
    if value is not None and value != "":
        return value
    value = env_values.get(name)
    if value is not None and value != "":
        return value
    return None


def _parse_int(value: str | None, name: str) -> int | None:
    """解析可选整数配置。"""
    if value is None:
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise DeepSeekConfigError(f"{name} 必须是整数: {value}") from exc
    if parsed <= 0:
        raise DeepSeekConfigError(f"{name} 必须大于 0: {value}")
    return parsed


def _parse_bool(value: str | None, name: str) -> bool | None:
    """解析可选布尔配置，未设置时不向 API 发送 thinking 开关。"""
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on", "enabled"}:
        return True
    if normalized in {"0", "false", "no", "n", "off", "disabled"}:
        return False
    raise DeepSeekConfigError(f"{name} 必须是布尔值: {value}")


@dataclass(frozen=True)
class DeepSeekConfig:
    """DeepSeek 调用配置。"""

    api_key: str
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    timeout_seconds: int = 120
    max_tokens: int | None = None
    reasoning_effort: str | None = None
    thinking_enabled: bool | None = None


def load_deepseek_config(env_path: str | Path = DEFAULT_ENV_PATH) -> DeepSeekConfig:
    """从项目 .env 与进程环境变量加载 DeepSeek 配置。

    env_path 也可经进程环境变量 DEEPSEEK_ENV_PATH 覆盖（仍须落在项目内）。
    """
    override = os.environ.get("DEEPSEEK_ENV_PATH")
    if override and Path(env_path) == DEFAULT_ENV_PATH:
        env_path = Path(override)
    env_values = _parse_env_file(Path(env_path))

    api_key = _get_env_value("DEEPSEEK_API_KEY", env_values)
    if not api_key:
        raise DeepSeekConfigError("缺少 DEEPSEEK_API_KEY")

    base_url = _get_env_value("DEEPSEEK_BASE_URL", env_values) or "https://api.deepseek.com"
    model = _get_env_value("DEEPSEEK_MODEL", env_values) or "deepseek-chat"
    timeout_seconds = _parse_int(
        _get_env_value("DEEPSEEK_TIMEOUT_SECONDS", env_values),
        "DEEPSEEK_TIMEOUT_SECONDS",
    ) or 120
    max_tokens = _parse_int(
        _get_env_value("DEEPSEEK_MAX_TOKENS", env_values),
        "DEEPSEEK_MAX_TOKENS",
    )
    reasoning_effort = _get_env_value("DEEPSEEK_REASONING_EFFORT", env_values) or "max"
    thinking_enabled = _parse_bool(
        _get_env_value("DEEPSEEK_THINKING_ENABLED", env_values),
        "DEEPSEEK_THINKING_ENABLED",
    )

    return DeepSeekConfig(
        api_key=api_key,
        base_url=base_url,
        model=model,
        timeout_seconds=timeout_seconds,
        max_tokens=max_tokens,
        reasoning_effort=reasoning_effort,
        thinking_enabled=thinking_enabled,
    )


class DeepSeekClient:
    """基于 OpenAI-compatible SDK 的 DeepSeek 客户端。"""

    def __init__(self, config: DeepSeekConfig | None = None) -> None:
        if OpenAI is None:
            raise DeepSeekConfigError("缺少 openai 依赖，请先安装 openai SDK")
        self.config = config or load_deepseek_config()
        self.last_meta: dict[str, Any] | None = None
        self._client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout_seconds,
        )

    def chat(
        self,
        messages: Sequence[Mapping[str, Any]],
        reasoning_effort: str | None = None,
        thinking_enabled: bool | None = None,
    ) -> str:
        """发送多轮消息，只返回最终 answer content，不返回 reasoning_content。

        thinking_enabled 为 None 时沿用全局配置；显式传 True/False 时按调用覆盖
        （用于空响应降级重试：推理烧穿 max_tokens 时关闭思考保正文产出）。
        每次调用后 self.last_meta 留存 token 用量与 finish_reason（空响应时同样留存，
        供降级留痕），不含任何密钥信息。
        """
        request_messages = [self._strip_reasoning_content(message) for message in messages]
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": request_messages,
        }
        if self.config.max_tokens is not None:
            kwargs["max_tokens"] = self.config.max_tokens
        effective_reasoning_effort = reasoning_effort or self.config.reasoning_effort
        if effective_reasoning_effort:
            kwargs["reasoning_effort"] = effective_reasoning_effort
        effective_thinking = (
            thinking_enabled if thinking_enabled is not None else self.config.thinking_enabled
        )
        if effective_thinking is not None:
            thinking_type = "enabled" if effective_thinking else "disabled"
            kwargs["extra_body"] = {"thinking": {"type": thinking_type}}

        response = self._client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        message = choice.message
        self.last_meta = self._extract_meta(response, choice, effective_reasoning_effort, effective_thinking)

        # DeepSeek 可能返回 reasoning_content；这里刻意不保存、不拼接、不向外暴露。
        content = message.content
        if content is None:
            text = ""
        elif isinstance(content, str):
            text = content
        else:
            text = "".join(part.get("text", "") for part in content if isinstance(part, dict))
        if not text.strip():
            raise DeepSeekEmptyResponseError(
                f"DeepSeek 返回空 content（finish_reason={choice.finish_reason}，"
                f"model={self.config.model}）"
            )
        return text

    def ask(
        self,
        prompt: str,
        system_prompt: str | None = None,
        reasoning_effort: str | None = None,
        thinking_enabled: bool | None = None,
    ) -> str:
        """便捷单轮调用。"""
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return self.chat(
            messages,
            reasoning_effort=reasoning_effort,
            thinking_enabled=thinking_enabled,
        )

    @staticmethod
    def _extract_meta(
        response: Any,
        choice: Any,
        reasoning_effort: str | None,
        thinking_enabled: bool | None,
    ) -> dict[str, Any]:
        """从响应中提取 token 用量等留痕字段（只留数字与状态，不含密钥）。"""
        usage = getattr(response, "usage", None)
        reasoning_tokens = None
        details = getattr(usage, "completion_tokens_details", None) if usage else None
        if details is not None:
            reasoning_tokens = getattr(details, "reasoning_tokens", None)
        return {
            "model": getattr(response, "model", None),
            "finish_reason": getattr(choice, "finish_reason", None),
            "prompt_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
            "completion_tokens": getattr(usage, "completion_tokens", None) if usage else None,
            "total_tokens": getattr(usage, "total_tokens", None) if usage else None,
            "reasoning_tokens": reasoning_tokens,
            "reasoning_effort": reasoning_effort,
            "thinking_enabled": thinking_enabled,
        }

    @staticmethod
    def _strip_reasoning_content(message: Mapping[str, Any]) -> dict[str, Any]:
        """清理输入消息中的 reasoning_content，避免推理字段回传导致接口报错。"""
        cleaned = dict(message)
        cleaned.pop("reasoning_content", None)
        return cleaned
