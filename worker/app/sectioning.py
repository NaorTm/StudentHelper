# worker/app/sectioning.py
from __future__ import annotations

import re


HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*)(?:\s+|\s*-\s*)(.+)$")


def extract_sections(text: str) -> list[tuple[str | None, str]]:
    sections: list[tuple[str | None, str]] = []
    current_heading: str | None = None
    current_lines: list[str] = []

    def flush():
        nonlocal current_lines
        if current_lines:
            sections.append((current_heading, "\n".join(current_lines).strip()))
            current_lines = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        match = HEADING_RE.match(line)
        if match:
            flush()
            current_heading = f"{match.group(1)} {match.group(2)}"
            continue

        if len(line) > 3 and line.isupper():
            flush()
            current_heading = line
            continue

        current_lines.append(line)

    flush()
    if not sections and text.strip():
        sections.append((None, text.strip()))
    return sections
