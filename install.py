#!/usr/bin/env python3
"""Install understory for the harness you use. Cross-platform.

    python3 install.py claude    # ~/.claude/skills/understory (Claude Code, Cursor, Copilot)
    python3 install.py skills    # ~/.agents/skills/understory (Codex, Cursor, Gemini CLI, Copilot)
    python3 install.py agents    # ./AGENTS.md in the current project
    python3 install.py cursor    # ./.cursor/rules/understory.mdc
    python3 install.py copilot   # ./.github/copilot-instructions.md

SKILL.md is an open standard read by 25+ agents (Claude Code, Codex, Cursor,
Gemini CLI, Copilot, Goose, ...). Claude Code reads ~/.claude/skills;
Codex CLI and Gemini CLI read ~/.agents/skills; Cursor and Copilot read both.
The agents/cursor/copilot targets are fallbacks for tools that only read a
plain instructions file, and refuse to overwrite an existing file unless you
pass --force.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE / "skills" / "understory"
SKIP = {".DS_Store", "__pycache__"}


def install_skill(env: str, default: Path) -> None:
    dest = Path(os.environ.get(env, default)) / "understory"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(PKG, dest, ignore=lambda d, names: [n for n in names if n in SKIP])
    print(f"installed to {dest}")


def install_file(src: str, dest: str) -> None:
    target = Path.cwd() / dest
    if target.exists() and "--force" not in sys.argv:
        sys.exit(f"{target} already exists; merge {PKG / 'adapters' / src} into it "
                 "by hand, or rerun with --force to replace it")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PKG / "adapters" / src, target)
    print(f"wrote {target} (the toolkit itself stays at {HERE})")


TARGETS = {
    "claude": lambda: install_skill("CLAUDE_SKILLS_DIR", Path.home() / ".claude" / "skills"),
    "skills": lambda: install_skill("AGENTS_SKILLS_DIR", Path.home() / ".agents" / "skills"),
    "agents": lambda: install_file("AGENTS.md", "AGENTS.md"),
    "cursor": lambda: install_file("cursor-rule.mdc", ".cursor/rules/understory.mdc"),
    "copilot": lambda: install_file("copilot-instructions.md", ".github/copilot-instructions.md"),
}

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--force"]
    choice = args[0] if args else "claude"
    if choice not in TARGETS:
        sys.exit(f"usage: python3 install.py [{'|'.join(TARGETS)}] [--force]")
    TARGETS[choice]()
