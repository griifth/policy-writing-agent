from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def load_yaml(path: str | Path) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text) or {}
    except ModuleNotFoundError:
        data = _parse_simple_yaml(text)
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    lines = [
        (len(raw) - len(raw.lstrip(" ")), raw.strip())
        for raw in text.splitlines()
        if raw.strip() and not raw.strip().startswith("#")
    ]
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]

    for index, (indent, content) in enumerate(lines):
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if content.startswith("- "):
            if not isinstance(parent, list):
                raise ValueError(f"Unexpected list item: {content}")
            parent.append(_parse_scalar(content[2:]))
            continue

        if ":" not in content:
            raise ValueError(f"Unsupported YAML line: {content}")
        key, value = content.split(":", 1)
        key = key.strip()
        value = value.strip()

        if value:
            parsed_value = _parse_scalar(value)
            if isinstance(parent, dict):
                parent[key] = parsed_value
            else:
                raise ValueError(f"Unexpected mapping under list: {content}")
            continue

        next_is_list = index + 1 < len(lines) and lines[index + 1][0] > indent and lines[index + 1][1].startswith("- ")
        child: Any = [] if next_is_list else {}
        if isinstance(parent, dict):
            parent[key] = child
        else:
            raise ValueError(f"Unexpected nested mapping under list: {content}")
        stack.append((indent, child))

    return root


def _parse_scalar(value: str) -> Any:
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "None"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(item.strip()) for item in inner.split(",")]
    if value.isdigit():
        return int(value)
    return value


def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def write_text(path: str | Path, content: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def write_json(path: str | Path, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def timestamp_run_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def utc_timestamp() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def slugify(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]+", "_", value).strip("_")
    return normalized.lower() or "item"


def ensure_dir(path: str | Path) -> Path:
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def update_workflow_state(run_dir: str | Path, phase: str, status: str, details: dict[str, Any] | None = None) -> None:
    state_path = Path(run_dir) / "workflow_state.json"
    if state_path.exists():
        state = load_json(state_path)
    else:
        state = {"phases": [], "current_phase": None}
    state["current_phase"] = phase
    state["phases"].append(
        {
            "phase": phase,
            "status": status,
            "generated_at": utc_timestamp(),
            "details": details or {},
        }
    )
    write_json(state_path, state)
