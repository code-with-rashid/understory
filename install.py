#!/usr/bin/env python3
"""Install understory for the harness you use. Cross-platform.

    python3 install.py claude    # ~/.claude/skills/understory (SKILL.md standard)
    python3 install.py agents    # ./AGENTS.md in the current project
    python3 install.py cursor    # ./.cursor/rules/understory.mdc
    python3 install.py copilot   # ./.github/copilot-instructions.md

SKILL.md is an open standard read by 25+ agents (Claude Code, Codex, Cursor,
Gemini CLI, Copilot, Goose, ...). If your tool supports Agent Skills, use the
`claude` target — the same installed directory works for all of them. The other
targets are fallbacks for tools that only read a plain instructions file.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKIP = {".git", ".DS_Store", "__pycache__", "test", "examples", "docs"}


def install_skill() -> None:
    dest = Path(os.environ.get("CLAUDE_SKILLS_DIR",
                               Path.home() / ".claude" / "skills")) / "understory"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(HERE, dest, ignore=lambda d, names: [n for n in names if n in SKIP])
    print(f"installed to {dest}")
    print("read by any agent that supports the Agent Skills standard")


def install_file(src: str, dest: str) -> None:
    target = Path.cwd() / dest
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(HERE / "adapters" / src, target)
    print(f"wrote {target} (the toolkit itself stays at {HERE})")


TARGETS = {
    "claude": install_skill,
    "agents": lambda: install_file("AGENTS.md", "AGENTS.md"),
    "cursor": lambda: install_file("cursor-rule.mdc", ".cursor/rules/understory.mdc"),
    "copilot": lambda: install_file("copilot-instructions.md", ".github/copilot-instructions.md"),
}

if __name__ == "__main__":
    choice = sys.argv[1] if len(sys.argv) > 1 else "claude"
    if choice not in TARGETS:
        sys.exit(f"usage: python3 install.py [{'|'.join(TARGETS)}]")
    TARGETS[choice]()
