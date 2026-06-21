"""工作流通用 LLM 客户端。

本文件只封装文本生成接口，NotebookLM 检索仍由 notebooklm_client 负责。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

from deepseek_client import DeepSeekClient

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - 运行时给出清晰错误
    OpenAI = None  # type: ignore[assignment]


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_PATH = WORKFLOW_ROOT / ".env"


class LLMClientError(RuntimeError):
    """LLM 客户端配置或调用错误。"""


class TextLLMClient(Protocol):
    """工作流所需的最小文本生成接口。"""

    def ask(self, prompt: str, system_prompt: str | None = None) -> str:
        """输入提示词，返回最终正文。"""


def _ensure_project_path(path: str | Path) -> Path:
    """限制可选配置文件读取在当前项目目录内。"""
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = WORKFLOW_ROOT / candidate
    resolved = candidate.resolve()
    root = WORKFLOW_ROOT.resolve()
    if resolved != root and root not in resolved.parents:
        raise LLMClientError(f"路径超出项目目录: {resolved}")
    return resolved


def _parse_env_file(env_path: Path = DEFAULT_ENV_PATH) -> dict[str, str]:
    """读取简单 .env 文件；进程环境变量仍拥有最高优先级。"""
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
    """优先读取进程环境变量，其次读取项目 .env。"""
    value = os.environ.get(name)
    if value:
        return value
    value = env_values.get(name)
    if value:
        return value
    return None


def _parse_int(value: str | None, name: str) -> int | None:
    """解析可选正整数配置。"""
    if value is None:
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise LLMClientError(f"{name} 必须是整数: {value}") from exc
    if parsed <= 0:
        raise LLMClientError(f"{name} 必须大于 0: {value}")
    return parsed


@dataclass(frozen=True)
class AnthropicCompatConfig:
    """Anthropic 兼容 OpenAI Chat Completions 接口配置。"""

    api_key: str
    base_url: str
    model: str
    timeout_seconds: int = 300
    max_tokens: int | None = None


def load_anthropic_compat_config(
    env_path: str | Path = DEFAULT_ENV_PATH,
) -> AnthropicCompatConfig:
    """从环境变量或项目 .env 加载 Anthropic 兼容接口配置。"""
    env_values = _parse_env_file(Path(env_path))

    api_key = _get_env_value("ANTHROPIC_COMPAT_API_KEY", env_values)
    if not api_key:
        raise LLMClientError("缺少 ANTHROPIC_COMPAT_API_KEY")

    base_url = _get_env_value("ANTHROPIC_COMPAT_BASE_URL", env_values)
    if not base_url:
        raise LLMClientError("缺少 ANTHROPIC_COMPAT_BASE_URL")

    model = _get_env_value("ANTHROPIC_COMPAT_MODEL", env_values)
    if not model:
        raise LLMClientError("缺少 ANTHROPIC_COMPAT_MODEL")

    timeout_seconds = _parse_int(
        _get_env_value("ANTHROPIC_COMPAT_TIMEOUT_SECONDS", env_values),
        "ANTHROPIC_COMPAT_TIMEOUT_SECONDS",
    ) or 300
    max_tokens = _parse_int(
        _get_env_value("ANTHROPIC_COMPAT_MAX_TOKENS", env_values),
        "ANTHROPIC_COMPAT_MAX_TOKENS",
    )

    return AnthropicCompatConfig(
        api_key=api_key,
        base_url=base_url,
        model=model,
        timeout_seconds=timeout_seconds,
        max_tokens=max_tokens,
    )


class AnthropicCompatClient:
    """通过 OpenAI SDK 调用 Anthropic 兼容接口。"""

    def __init__(self, config: AnthropicCompatConfig | None = None) -> None:
        if OpenAI is None:
            raise LLMClientError("缺少 openai 依赖，请先安装 openai SDK")
        self.config = config or load_anthropic_compat_config()
        self._client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout_seconds,
        )

    def chat(self, messages: Sequence[Mapping[str, Any]]) -> str:
        """发送消息并只返回最终正文，不记录或解析思维链。"""
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": [dict(message) for message in messages],
        }
        if self.config.max_tokens is not None:
            kwargs["max_tokens"] = self.config.max_tokens

        response = self._client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        return "".join(part.get("text", "") for part in content if isinstance(part, dict))

    def ask(self, prompt: str, system_prompt: str | None = None) -> str:
        """便捷单轮调用。"""
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages)


def create_llm_client(provider: str) -> TextLLMClient:
    """根据 provider 创建文本生成客户端。"""
    normalized = provider.strip().lower()
    if normalized == "deepseek":
        return DeepSeekClient()
    if normalized in {"anthropic_compat", "anthropic-compatible", "claude_compat"}:
        return AnthropicCompatClient()
    raise LLMClientError(f"未知 LLM provider: {provider}")
