"""NotebookLM CLI 外部调用客户端。"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"


class NotebookLMClientError(RuntimeError):
    """NotebookLM CLI 调用失败。"""


@dataclass(frozen=True)
class Notebook:
    """NotebookLM notebook 的最小结构。"""

    id: str
    name: str
    raw: Mapping[str, Any]


class NotebookLMClient:
    """用 subprocess 封装 notebooklm CLI，所有 notebook 操作都显式传 id。"""

    def __init__(
        self,
        cli_path: str | None = None,
        timeout_seconds: int | None = None,
        cwd: str | Path = PROJECT_ROOT,
    ) -> None:
        self.cli_path = cli_path or _load_cli_path()
        self.timeout_seconds = timeout_seconds or _load_timeout_seconds()
        self.cwd = self._ensure_project_path(cwd)

    def check_auth(self) -> Mapping[str, Any]:
        """检查认证是否真实可用；--test 会发起网络校验，避免只验证本地 cookie。"""
        data = self._run_json(["auth", "check", "--test", "--json"])
        checks = data.get("checks") if isinstance(data.get("checks"), Mapping) else {}
        if data.get("status") != "ok" or checks.get("token_fetch") is not True:
            raise NotebookLMClientError(f"NotebookLM 认证不可用: {data}")
        return data

    def list_notebooks(self) -> list[Notebook]:
        """列出 notebooks，并兼容 CLI 可能返回的几种 JSON 包装格式。"""
        data = self._run_json(["list", "--json"])
        return self._parse_notebooks(data)

    def find_notebook(self, notebook_name: str) -> Notebook:
        """先精确匹配 notebook_name；未命中时要求唯一模糊匹配。"""
        notebooks = self.list_notebooks()
        exact_matches = [item for item in notebooks if item.name == notebook_name]
        if len(exact_matches) == 1:
            return exact_matches[0]
        if len(exact_matches) > 1:
            raise NotebookLMClientError(f"notebook 精确匹配不唯一: {notebook_name}")

        query = notebook_name.casefold()
        fuzzy_matches = [
            item
            for item in notebooks
            if query in item.name.casefold() or item.name.casefold() in query
        ]
        if len(fuzzy_matches) == 1:
            return fuzzy_matches[0]
        if not fuzzy_matches:
            raise NotebookLMClientError(f"未找到 notebook: {notebook_name}")
        names = ", ".join(item.name for item in fuzzy_matches)
        raise NotebookLMClientError(f"notebook 模糊匹配不唯一: {names}")

    def ask_notebook(
        self,
        notebook_id: str,
        prompt_file: str | Path,
        output_file: str | Path | None = None,
    ) -> str:
        """用 prompt 文件向指定 notebook 提问，并可保存自然文本 stdout。"""
        prompt_path = self._ensure_project_path(prompt_file)
        if not prompt_path.is_file():
            raise NotebookLMClientError(f"prompt 文件不存在: {prompt_path}")

        output = self._run_text(
            [
                "ask",
                "--prompt-file",
                str(prompt_path),
                "--notebook",
                notebook_id,
                "--timeout",
                str(self.timeout_seconds),
            ]
        )
        if output_file is not None:
            output_path = self._ensure_project_path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output, encoding="utf-8")
        return output

    def ask_by_name(
        self,
        notebook_name: str,
        prompt_file: str | Path,
        output_file: str | Path | None = None,
    ) -> str:
        """按 notebook 名称匹配后提问；实际 CLI 调用仍显式传 notebook id。"""
        notebook = self.find_notebook(notebook_name)
        return self.ask_notebook(
            notebook_id=notebook.id,
            prompt_file=prompt_file,
            output_file=output_file,
        )

    def _run_json(self, args: Sequence[str]) -> Mapping[str, Any]:
        """执行 CLI 并解析 JSON 输出。"""
        output = self._run_text(args)
        try:
            data = json.loads(output)
        except json.JSONDecodeError as exc:
            raise NotebookLMClientError(f"NotebookLM 输出不是合法 JSON: {output[:500]}") from exc
        if not isinstance(data, Mapping):
            return {"items": data}
        return data

    def _run_text(self, args: Sequence[str]) -> str:
        """执行 notebooklm CLI，捕获 stdout/stderr 并统一错误消息。"""
        command = [self.cli_path, *args]
        try:
            completed = subprocess.run(
                command,
                cwd=self.cwd,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
        except FileNotFoundError as exc:
            raise NotebookLMClientError("未找到 notebooklm CLI，请先安装并登录") from exc
        except subprocess.TimeoutExpired as exc:
            raise NotebookLMClientError(f"NotebookLM CLI 调用超时: {' '.join(command)}") from exc

        if completed.returncode != 0:
            stderr = completed.stderr.strip()
            stdout = completed.stdout.strip()
            detail = stderr or stdout or f"退出码 {completed.returncode}"
            raise NotebookLMClientError(f"NotebookLM CLI 调用失败: {detail}")
        return completed.stdout.strip()

    @staticmethod
    def _parse_notebooks(data: Mapping[str, Any]) -> list[Notebook]:
        """从 JSON 中提取 notebook 列表，并标准化 id/name 字段。"""
        items = data.get("notebooks") or data.get("items") or data.get("data")
        if items is None and NotebookLMClient._looks_like_notebook(data):
            items = [data]
        if not isinstance(items, list):
            raise NotebookLMClientError(f"无法识别 notebook 列表结构: {data}")

        notebooks: list[Notebook] = []
        for item in items:
            if not isinstance(item, Mapping):
                continue
            notebook_id = (
                item.get("id")
                or item.get("notebook_id")
                or item.get("notebookId")
                or item.get("uuid")
            )
            notebook_name = item.get("name") or item.get("title")
            if notebook_id and notebook_name:
                notebooks.append(
                    Notebook(id=str(notebook_id), name=str(notebook_name), raw=item)
                )
        return notebooks

    @staticmethod
    def _looks_like_notebook(data: Mapping[str, Any]) -> bool:
        """判断单个对象是否像 notebook。"""
        has_id = any(key in data for key in ("id", "notebook_id", "notebookId", "uuid"))
        has_name = any(key in data for key in ("name", "title"))
        return has_id and has_name

    @staticmethod
    def _ensure_project_path(path: str | Path) -> Path:
        """限制文件读写在当前项目目录内。"""
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            candidate = PROJECT_ROOT / candidate
        resolved = candidate.resolve()
        root = PROJECT_ROOT.resolve()
        if resolved != root and root not in resolved.parents:
            raise NotebookLMClientError(f"路径超出项目目录: {resolved}")
        return resolved


def ask_notebook_by_name(
    notebook_name: str,
    prompt_file: str | Path,
    output_file: str | Path | None = None,
) -> str:
    """模块级便捷函数：按名称匹配 notebook 并保存回答。"""
    return NotebookLMClient().ask_by_name(
        notebook_name=notebook_name,
        prompt_file=prompt_file,
        output_file=output_file,
    )


def _load_cli_path() -> str:
    """从环境变量或项目 .env 读取 NotebookLM CLI 路径。

    CLI 可执行文件可能位于项目外的本地 skill/源码目录；这里仅使用该路径作为
    subprocess 可执行入口，不放宽工作流文件读写边界。
    """

    env_value = os.environ.get("NOTEBOOKLM_CLI_PATH")
    if env_value:
        return env_value

    if DEFAULT_ENV_PATH.exists():
        for line in DEFAULT_ENV_PATH.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            if key.strip() == "NOTEBOOKLM_CLI_PATH":
                return value.strip().strip('"').strip("'")

    return "notebooklm"


def _load_timeout_seconds() -> int:
    """从环境变量或项目 .env 读取 NotebookLM 调用超时。"""

    raw_value = os.environ.get("NOTEBOOKLM_TIMEOUT_SECONDS")
    if raw_value is None and DEFAULT_ENV_PATH.exists():
        for line in DEFAULT_ENV_PATH.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            if key.strip() == "NOTEBOOKLM_TIMEOUT_SECONDS":
                raw_value = value.strip().strip('"').strip("'")
                break

    if raw_value is None:
        return 300
    try:
        timeout = int(raw_value)
    except ValueError as exc:
        raise NotebookLMClientError(f"NOTEBOOKLM_TIMEOUT_SECONDS 必须是整数: {raw_value}") from exc
    if timeout <= 0:
        raise NotebookLMClientError("NOTEBOOKLM_TIMEOUT_SECONDS 必须大于 0")
    return timeout
