from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from agent_runtime import AGENT_NAMES, API_DRIVER_SUPPORTED_AGENTS, build_agent_runtime
from io_utils import load_yaml, write_text


PROJECT_DIR = Path(__file__).resolve().parents[1]
CONFIG_TARGETS = {
    "mock": PROJECT_DIR / "config" / "report_task.yaml",
    "real": PROJECT_DIR / "config" / "report_task.real.yaml",
}
CONSOLE_HTML = PROJECT_DIR / "runtime_console.html"


class RuntimeConsoleHandler(BaseHTTPRequestHandler):
    server_version = "PolicyRuntimeConsole/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/runtime-console"}:
            self._send_file(CONSOLE_HTML, "text/html; charset=utf-8")
            return
        if parsed.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        if parsed.path == "/api/config":
            target = _target_from_query(parsed.query)
            config = load_yaml(CONFIG_TARGETS[target])
            self._send_json(
                {
                    "target": target,
                    "path": str(CONFIG_TARGETS[target]),
                    "config": config,
                    "validation": build_agent_runtime(config.get("agent_runtime", {})).validate(),
                    "env": _env_status(config),
                    "schema": _runtime_schema(),
                }
            )
            return
        if parsed.path == "/api/schema":
            self._send_json(_runtime_schema())
            return
        self._send_json({"error": "not_found", "path": parsed.path}, status=404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/config":
            self._handle_save_config()
            return
        if parsed.path == "/api/validate":
            payload = self._read_json_or_error()
            if payload is None:
                return
            config = payload.get("config", {})
            self._send_json({"validation": build_agent_runtime(config.get("agent_runtime", {})).validate(), "env": _env_status(config)})
            return
        self._send_json({"error": "not_found", "path": parsed.path}, status=404)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        print(f"{self.address_string()} - {format % args}")

    def _handle_save_config(self) -> None:
        payload = self._read_json_or_error()
        if payload is None:
            return
        target = str(payload.get("target", "real"))
        if target not in CONFIG_TARGETS:
            self._send_json({"error": "invalid_target", "allowed": sorted(CONFIG_TARGETS)}, status=400)
            return
        config = payload.get("config")
        if not isinstance(config, dict):
            self._send_json({"error": "invalid_config"}, status=400)
            return
        validation = build_agent_runtime(config.get("agent_runtime", {})).validate()
        if validation:
            self._send_json({"error": "validation_failed", "validation": validation}, status=400)
            return
        write_text(CONFIG_TARGETS[target], dump_yaml(config))
        saved = load_yaml(CONFIG_TARGETS[target])
        self._send_json(
            {
                "target": target,
                "path": str(CONFIG_TARGETS[target]),
                "config": saved,
                "validation": build_agent_runtime(saved.get("agent_runtime", {})).validate(),
                "env": _env_status(saved),
            }
        )

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        if not raw:
            return {}
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("Expected JSON object payload.")
        return payload

    def _read_json_or_error(self) -> dict[str, Any] | None:
        try:
            return self._read_json()
        except (json.JSONDecodeError, ValueError) as exc:
            self._send_json({"error": "invalid_json", "message": str(exc)}, status=400)
            return None

    def _send_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self._send_json({"error": "file_not_found", "path": str(path)}, status=404)
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, payload: Any, status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def _target_from_query(query: str) -> str:
    values = parse_qs(query).get("target", ["real"])
    target = values[0]
    if target not in CONFIG_TARGETS:
        return "real"
    return target


def _runtime_schema() -> dict[str, Any]:
    return {
        "targets": sorted(CONFIG_TARGETS),
        "agents": AGENT_NAMES,
        "api_driver_supported_agents": sorted(API_DRIVER_SUPPORTED_AGENTS),
        "drivers": ["local"],
        "providers": [],
        "capability_policy": {
            "external_calls": ["notebooklm_cli"],
            "llm_api": False,
            "notebooklm_skill_mutation": False,
        },
    }


def _env_status(config: dict[str, Any]) -> dict[str, bool]:
    return {}


def dump_yaml(payload: Any) -> str:
    return _dump_node(payload, 0).rstrip() + "\n"


def _dump_node(value: Any, indent: int) -> str:
    spaces = " " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                lines.append(f"{spaces}{key}:")
                lines.append(_dump_node(item, indent + 2))
            else:
                lines.append(f"{spaces}{key}: {_format_scalar(item)}")
        return "\n".join(lines)
    if isinstance(value, list):
        if not value:
            return f"{spaces}[]"
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{spaces}-")
                lines.append(_dump_node(item, indent + 2))
            else:
                lines.append(f"{spaces}- {_format_scalar(item)}")
        return "\n".join(lines)
    return f"{spaces}{_format_scalar(value)}"


def _format_scalar(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    return json.dumps(text, ensure_ascii=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the policy writing agent runtime console.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), RuntimeConsoleHandler)
    print(f"Runtime console: http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
