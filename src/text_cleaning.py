from __future__ import annotations

import re
from typing import Any


BRACKET_CITATION_RE = re.compile(r"\s*\[(?:\d+(?:\s*[-,，、]\s*\d+)*)\]")


def strip_citation_markers(value: Any) -> str:
    text = str(value) if value is not None else ""
    text = BRACKET_CITATION_RE.sub("", text)
    text = re.sub(r"\s+([。！？；，、,.!?;:])", r"\1", text)
    return text.strip()

