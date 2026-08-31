#!/usr/bin/env python3
"""Validate SKILL.md against the Agent Skills specification (agentskills.io).

Run from anywhere: python3 test/validate_skill.py [skill-dir]
Checks the constraints the spec makes checkable, so a frontmatter edit that
breaks portability across the 25+ SKILL.md-reading agents fails here first.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent)
problems: list[str] = []

skill = root / "SKILL.md"
if not skill.exists():
    sys.exit(f"FAIL: no SKILL.md in {root}")
text = skill.read_text(encoding="utf-8")

m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
if not m:
    sys.exit("FAIL: SKILL.md has no YAML frontmatter block")
fm = m.group(1)

name = re.search(r"^name:\s*(\S+)\s*$", fm, re.M)
if not name:
    problems.append("frontmatter has no name field")
else:
    n = name.group(1)
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", n) or len(n) > 64:
        problems.append(f"name {n!r} violates the spec (lowercase/digits/single hyphens, max 64)")
    if n != root.name:
        problems.append(f"name {n!r} does not match the directory name {root.name!r}")

desc = re.search(r'^description:\s*"?(.+?)"?\s*$', fm, re.M | re.S)
if not desc:
    problems.append("frontmatter has no description field")
else:
    d = re.search(r'description:\s*"(.*?)"\n\w', fm + "\nx", re.S)
    length = len(d.group(1)) if d else len(desc.group(1))
    if not 1 <= length <= 1024:
        problems.append(f"description is {length} characters (spec allows 1-1024)")
    if "<" in (d.group(1) if d else desc.group(1)):
        problems.append("description contains angle brackets — some agents reject XML-ish text")

comp = re.search(r"^compatibility:\s*(.+)$", fm, re.M)
if comp and len(comp.group(1)) > 500:
    problems.append("compatibility exceeds 500 characters")

lines = len(text.splitlines())
if lines > 500:
    problems.append(f"SKILL.md is {lines} lines — the spec recommends under 500; move detail to references")

for ref in re.findall(r"\]\((?!http)([^)]+)\)", text):
    if not (root / ref.split("#")[0]).exists():
        problems.append(f"SKILL.md links to {ref}, which does not exist in the skill")

for p in problems:
    print("FAIL:", p)
if problems:
    sys.exit(1)
print(f"OK: {root.name} conforms — name valid, description {length} chars, {lines} lines, links resolve")
