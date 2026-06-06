"""运行目录与 Markdown 文件读写工具。

本模块只面向当前项目目录内的文件操作，默认运行目录为：

    runs/<run_id>/
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from pathlib import Path


RUNS_DIR_NAME = "runs"
_SAFE_RUN_ID = re.compile(r"^[A-Za-z0-9._-]+$")


def project_root() -> Path:
    """返回当前项目根目录。

    文件位于 workflow/ 下，因此 workflow 的上一级就是当前项目目录。
    """

    return Path(__file__).resolve().parent.parent


def ensure_within_project(path: str | Path, base_dir: str | Path | None = None) -> Path:
    """校验路径仍在当前项目目录内，并返回解析后的绝对路径。"""

    root = Path(base_dir).resolve() if base_dir is not None else project_root()
    resolved = Path(path).resolve()

    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"路径超出当前项目目录：{resolved}") from exc

    return resolved


def make_run_id(prefix: str = "run") -> str:
    """生成适合目录名使用的运行 ID。"""

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    suffix = uuid.uuid4().hex[:8]
    return f"{prefix}-{timestamp}-{suffix}"


def validate_run_id(run_id: str) -> str:
    """校验运行 ID，避免路径穿越或不可预期的目录名。"""

    if not run_id or not _SAFE_RUN_ID.fullmatch(run_id):
        raise ValueError("run_id 只能包含字母、数字、点、下划线和连字符")
    return run_id


def runs_root(base_dir: str | Path | None = None) -> Path:
    """创建并返回 runs/ 根目录。"""

    root = _base_root(base_dir)
    path = ensure_within_project(root / RUNS_DIR_NAME, root)
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_run_dir(run_id: str | None = None, base_dir: str | Path | None = None) -> tuple[str, Path]:
    """创建 runs/<run_id>/ 目录。

    如果未传入 run_id，则自动生成一个新的运行 ID。
    """

    actual_run_id = validate_run_id(run_id) if run_id is not None else make_run_id()
    root = _base_root(base_dir)
    path = runs_root(base_dir) / actual_run_id
    path = ensure_within_project(path, root)
    path.mkdir(parents=True, exist_ok=True)
    return actual_run_id, path


def get_run_dir(run_id: str, base_dir: str | Path | None = None, create: bool = False) -> Path:
    """返回 runs/<run_id>/ 路径，必要时创建目录。"""

    actual_run_id = validate_run_id(run_id)
    root = _base_root(base_dir)
    path = runs_root(base_dir) / actual_run_id
    path = ensure_within_project(path, root)
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_subdir(run_dir: str | Path, relative_path: str | Path) -> Path:
    """在运行目录下创建子目录，并返回该子目录路径。"""

    base = ensure_within_project(run_dir)
    path = ensure_within_project(base / relative_path, base)
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_parent(path: str | Path) -> Path:
    """确保文件父目录存在，并返回文件路径。"""

    file_path = ensure_within_project(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    return file_path


def write_markdown(path: str | Path, content: str) -> Path:
    """写入 Markdown 文本，统一使用 UTF-8。"""

    file_path = ensure_parent(path)
    file_path.write_text(_normalize_text(content), encoding="utf-8")
    return file_path


def append_markdown(path: str | Path, content: str) -> Path:
    """追加 Markdown 文本，统一使用 UTF-8。"""

    file_path = ensure_parent(path)
    existing = file_path.read_text(encoding="utf-8") if file_path.exists() else ""
    file_path.write_text(existing + _normalize_text(content), encoding="utf-8")
    return file_path


def read_markdown(path: str | Path, default: str | None = None) -> str:
    """读取 Markdown 文本；文件不存在且提供 default 时返回 default。"""

    file_path = ensure_within_project(path)
    if not file_path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(file_path)
    return file_path.read_text(encoding="utf-8")


def markdown_path(run_dir: str | Path, filename: str) -> Path:
    """返回运行目录下的 Markdown 文件路径。"""

    if not filename.endswith(".md"):
        raise ValueError("filename 必须是 .md 文件")
    base = ensure_within_project(run_dir)
    return ensure_within_project(base / filename, base)


def _base_root(base_dir: str | Path | None) -> Path:
    """返回项目内的基准目录。"""

    return ensure_within_project(base_dir) if base_dir is not None else project_root()


def _normalize_text(content: str) -> str:
    """保证文本以单个换行结尾，便于后续追加和 diff。"""

    return content.rstrip() + "\n"
