#!/usr/bin/env python3
"""Report likely Western punctuation in Chinese prose without modifying files."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


CJK = r"\u3400-\u4dbf\u4e00-\u9fff"

RULES = [
    ("英文双引号", re.compile(rf'(?<=[{CJK}])"|"(?=[{CJK}])')),
    ("英文单引号", re.compile(rf"(?<=[{CJK}])'|'(?=[{CJK}])")),
    ("英文逗号", re.compile(rf"(?<=[{CJK}]),|,(?=[{CJK}])")),
    ("英文冒号", re.compile(rf"(?<=[{CJK}]):|:(?=[{CJK}])")),
    ("英文分号", re.compile(rf"(?<=[{CJK}]);|;(?=[{CJK}])")),
    ("英文问号", re.compile(rf"(?<=[{CJK}])\?")),
    ("英文叹号", re.compile(rf"(?<=[{CJK}])!")),
    ("英文左括号", re.compile(rf"\((?=[{CJK}])")),
    ("英文右括号", re.compile(rf"(?<=[{CJK}])\)")),
    ("中文语境斜杠", re.compile(rf"(?<=[{CJK}])/|/(?=[{CJK}])")),
    ("中文语境英文加号", re.compile(rf"(?<=[{CJK}])\+|\+(?=[{CJK}])")),
    ("英文三点省略号", re.compile(rf"(?<=[{CJK}])\.{{3}}|\.{{3}}(?=[{CJK}])")),
    ("双英文减号", re.compile(rf"(?<=[{CJK}])--|--(?=[{CJK}])")),
]


def excerpt(line: str, start: int, end: int, radius: int = 16) -> str:
    left = max(0, start - radius)
    right = min(len(line), end + radius)
    return line[left:right].strip().replace("\t", " ")


def scan(text: str, label: str) -> int:
    findings = 0
    for line_no, line in enumerate(text.splitlines(), 1):
        for rule_name, pattern in RULES:
            for match in pattern.finditer(line):
                findings += 1
                column = match.start() + 1
                print(
                    f"{label}:{line_no}:{column}: {rule_name}: "
                    f"{match.group(0)!r}  [{excerpt(line, match.start(), match.end())}]"
                )
    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="扫描中文文本中疑似误用的英文标点；仅报告候选项，不修改文件。"
    )
    parser.add_argument("files", nargs="*", help="UTF-8 文本文件；不提供时读取标准输入")
    parser.add_argument(
        "--fail-on-findings",
        action="store_true",
        help="发现候选项时返回退出码 1，适合自动校验",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    total = 0

    if not args.files:
        total += scan(sys.stdin.read(), "<stdin>")
    else:
        for raw_path in args.files:
            path = Path(raw_path)
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                print(f"{path}: 无法读取：{exc}", file=sys.stderr)
                return 2
            total += scan(text, str(path))

    print(f"共发现 {total} 个待人工判断的标点候选项。")
    return 1 if total and args.fail_on_findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
