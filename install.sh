#!/bin/bash
# Install understory as a skill for the harness you use.
#
#   ./install.sh claude     ~/.claude/skills/understory  (Claude Code, Cursor, Copilot)
#   ./install.sh skills     ~/.agents/skills/understory  (Codex, Cursor, Gemini CLI, Copilot)
#   ./install.sh cursor     ./.cursor/rules/understory.mdc
#   ./install.sh agents     ./AGENTS.md
#   ./install.sh copilot    ./.github/copilot-instructions.md
#
# The file targets refuse to overwrite an existing file unless --force is given.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-claude}"
FORCE="${2:-}"

no_clobber() {
  if [ -e "$1" ] && [ "$FORCE" != "--force" ]; then
    echo "$1 already exists; merge $2 into it by hand, or rerun with --force" >&2
    exit 1
  fi
}

install_skill() {
  DEST="$1/understory"
  mkdir -p "$1"
  rm -rf "$DEST"
  cp -R "$HERE/skills/understory" "$DEST"
  rm -rf "$DEST/__pycache__"
  echo "installed to $DEST"
}

case "$TARGET" in
  claude)
    install_skill "${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
    ;;
  skills)
    install_skill "${AGENTS_SKILLS_DIR:-$HOME/.agents/skills}"
    ;;
  cursor)
    no_clobber .cursor/rules/understory.mdc "$HERE/skills/understory/adapters/cursor-rule.mdc"
    mkdir -p .cursor/rules
    cp "$HERE/skills/understory/adapters/cursor-rule.mdc" .cursor/rules/understory.mdc
    echo "wrote .cursor/rules/understory.mdc (the toolkit still lives at $HERE)"
    ;;
  agents)
    no_clobber ./AGENTS.md "$HERE/skills/understory/adapters/AGENTS.md"
    cp "$HERE/skills/understory/adapters/AGENTS.md" ./AGENTS.md
    echo "wrote ./AGENTS.md"
    ;;
  copilot)
    no_clobber .github/copilot-instructions.md "$HERE/skills/understory/adapters/copilot-instructions.md"
    mkdir -p .github
    cp "$HERE/skills/understory/adapters/copilot-instructions.md" .github/copilot-instructions.md
    echo "wrote .github/copilot-instructions.md"
    ;;
  *)
    echo "usage: ./install.sh [claude|skills|cursor|agents|copilot] [--force]" >&2
    exit 1
    ;;
esac
