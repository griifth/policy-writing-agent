#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""部署后跨平台环境自检脚本（Win/mac 通用，纯标准库）。

用法：
    python3 scripts/deploy_selfcheck.py       (mac/Linux)
    python  scripts\\deploy_selfcheck.py       (Windows)

逐项打印 [OK]/[WARN]/[FAIL]，最后汇总：任一 FAIL 则退出码非 0。
不打印任何密钥内容。
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# 项目根：本脚本位于 <root>/scripts/deploy_selfcheck.py
ROOT = Path(__file__).resolve().parents[1]

# 计数器
_counts = {"OK": 0, "WARN": 0, "FAIL": 0}


def report(status: str, title: str, detail: str = "") -> None:
    """打印一条检查结果并计数。status ∈ {OK, WARN, FAIL}。"""
    _counts[status] = _counts.get(status, 0) + 1
    line = f"[{status}] {title}"
    if detail:
        line += f" — {detail}"
    print(line)


def check_python_version() -> None:
    major, minor = sys.version_info[:2]
    ver = f"{major}.{minor}.{sys.version_info[2]}"
    if (major, minor) >= (3, 10):
        report("OK", "Python 版本", f"当前 {ver} (>= 3.10)")
    else:
        report("FAIL", "Python 版本", f"当前 {ver}，需要 >= 3.10")


def check_pyyaml() -> None:
    try:
        import yaml  # noqa: F401
        ver = getattr(yaml, "__version__", "unknown")
        report("OK", "PyYAML (import yaml)", f"已安装，版本 {ver}")
    except Exception as exc:  # noqa: BLE001
        report("FAIL", "PyYAML (import yaml)",
               f"导入失败：{exc}。请 pip install pyyaml")


def _which_notebooklm():
    """定位 notebooklm 可执行文件。返回路径或 None。"""
    env_path = os.environ.get("NOTEBOOKLM_CLI_PATH", "").strip()
    if env_path:
        # 环境变量可能是命令名，也可能是全路径
        candidate = shutil.which(env_path)
        if candidate:
            return candidate
        p = Path(env_path)
        if p.is_file():
            return str(p)
    # shutil.which 在 Windows 会自动匹配 .exe/.cmd (PATHEXT)
    for name in ("notebooklm", "notebooklm.exe"):
        found = shutil.which(name)
        if found:
            return found
    return None


def check_notebooklm() -> None:
    found = _which_notebooklm()
    if not found:
        report("WARN", "notebooklm CLI",
               "未在 PATH / NOTEBOOKLM_CLI_PATH 找到；现查材料时才需要。"
               "安装后可设 NOTEBOOKLM_CLI_PATH 指向可执行文件")
        return
    # 找到了：尝试跑一次 auth check（超时/失败降级为 WARN，绝不 FAIL）
    try:
        proc = subprocess.run(
            [found, "auth", "check", "--test", "--json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=20,
        )
        if proc.returncode == 0:
            report("OK", "notebooklm CLI", f"已找到并通过 auth check：{found}")
        else:
            report("WARN", "notebooklm CLI",
                   f"已找到 {found}，但 auth check 返回码 {proc.returncode}；"
                   "请手动运行 `notebooklm auth check --test --json` 确认登录")
    except subprocess.TimeoutExpired:
        report("WARN", "notebooklm CLI",
               f"已找到 {found}，auth check 超时；"
               "请手动运行 `notebooklm auth check --test --json` 确认登录")
    except Exception as exc:  # noqa: BLE001
        report("WARN", "notebooklm CLI",
               f"已找到 {found}，auth check 未能执行（{exc}）；"
               "请手动运行 `notebooklm auth check --test --json` 确认登录")


def check_pandoc() -> None:
    found = shutil.which("pandoc") or shutil.which("pandoc.exe")
    if found:
        report("OK", "pandoc", f"已找到：{found}")
    else:
        report("WARN", "pandoc",
               "未找到；仅导出 docx 时才需要，可后续再装")


def _env_has_nonempty_key(env_file: Path, key: str) -> bool:
    """检测 .env 文件中 key 是否存在且值非空。不返回/不打印值。"""
    prefix = key + "="
    try:
        for raw in env_file.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line.startswith("#") or not line:
                continue
            if line.startswith(prefix):
                value = line[len(prefix):].strip().strip('"').strip("'")
                return bool(value)
    except Exception:  # noqa: BLE001
        return False
    return False


def check_env_files() -> None:
    targets = [
        ("strategic 引擎", ROOT / "strategic_response_workflow" / ".env"),
        ("root 引擎", ROOT / ".env"),
    ]
    for label, env_file in targets:
        rel = env_file.relative_to(ROOT) if env_file.is_relative_to(ROOT) else env_file
        if not env_file.exists():
            report("FAIL", f".env（{label}）",
                   f"缺失：{rel}（可复制同目录 .env.example 后填 DEEPSEEK_API_KEY）")
            continue
        if _env_has_nonempty_key(env_file, "DEEPSEEK_API_KEY"):
            report("OK", f".env（{label}）",
                   f"{rel} 存在且 DEEPSEEK_API_KEY 已设置（值未读出）")
        else:
            report("FAIL", f".env（{label}）",
                   f"{rel} 存在但 DEEPSEEK_API_KEY 为空/缺失")


def check_assets() -> None:
    assets = [
        ("root workflow 目录", ROOT / "workflow"),
        ("root runner", ROOT / "workflow" / "runner.py"),
        ("strategic runner",
         ROOT / "strategic_response_workflow" / "workflow" / "runner.py"),
        ("strategic 体例目录 report_modules",
         ROOT / "strategic_response_workflow" / "report_modules"),
    ]
    for label, path in assets:
        rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
        if path.exists():
            report("OK", f"资产：{label}", str(rel))
        else:
            report("FAIL", f"资产：{label}", f"缺失：{rel}")

    # 校验三个 strategic 体例子目录（与 report_type 三选一对应）
    modules_root = ROOT / "strategic_response_workflow" / "report_modules"
    expected = ("experience_response", "strategic_response", "trend_review")
    if modules_root.is_dir():
        present = {p.name for p in modules_root.iterdir() if p.is_dir()}
        missing = [m for m in expected if m not in present]
        if missing:
            report("WARN", "strategic 体例子目录",
                   f"缺少：{', '.join(missing)}（report_type 可选值应有对应目录）")
        else:
            report("OK", "strategic 体例子目录",
                   "experience_response / strategic_response / trend_review 均在")


def print_next_steps() -> None:
    print("")
    print("建议的下一步（两个引擎的 --dry-run 冒烟命令）：")
    print("")
    print("  # strategic 引擎（战略响应体例示例）")
    print("  python strategic_response_workflow/workflow/runner.py \\")
    print('      --report-type strategic_response \\')
    print('      --topic "人工智能+教育" \\')
    print('      --target-country "美国" \\')
    print('      --strategy-domain "基础教育数字化" \\')
    print('      --notebook-name "The Digital Promise AI Literacy Framework" \\')
    print("      --dry-run")
    print("")
    print("  # root 引擎（通用国际比较 MVP）")
    print("  python workflow/runner.py \\")
    print('      --topic "人工智能+教育" \\')
    print('      --notebook-name "The Digital Promise AI Literacy Framework" \\')
    print("      --dry-run")
    print("")
    print("  （Windows 下把行尾 \\ 去掉、写成一行，或用 ^ 续行；python3 换成 python）")


def main() -> int:
    print("=" * 68)
    print("部署自检 deploy_selfcheck.py")
    print(f"项目根：{ROOT}")
    print("=" * 68)

    check_python_version()
    check_pyyaml()
    check_notebooklm()
    check_pandoc()
    check_env_files()
    check_assets()

    print("")
    print("-" * 68)
    print(f"汇总：OK={_counts['OK']}  WARN={_counts['WARN']}  FAIL={_counts['FAIL']}")
    print("-" * 68)

    print_next_steps()

    return 1 if _counts["FAIL"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
