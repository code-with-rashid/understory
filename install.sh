#!/bin/bash
# Install understory as a skill for the harness you use.
#
#   ./install.sh claude     ~/.claude/skills/understory
#   ./install.sh cursor     ./.cursor/rules/understory.mdc
#   ./install.sh agents     ./AGENTS.md
#   ./install.sh copilot    ./.github/copilot-instructions.md
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-claude}"

case "$TARGET" in
  claude)
    DEST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}/understory"
    mkdir -p "$(dirname "$DEST")"
    rm -rf "$DEST"
    cp -R "$HERE" "$DEST"
    rm -rf "$DEST/.git" "$DEST/test" "$DEST/examples"
    echo "installed to $DEST"
    ;;
  cursor)
    mkdir -p .cursor/rules
    cp "$HERE/adapters/cursor-rule.mdc" .cursor/rules/understory.mdc
    echo "wrote .cursor/rules/understory.mdc (the toolkit still lives at $HERE)"
    ;;
  agents)
    cp "$HERE/adapters/AGENTS.md" ./AGENTS.md
    echo "wrote ./AGENTS.md"
    ;;
  copilot)
    mkdir -p .github
    cp "$HERE/adapters/copilot-instructions.md" .github/copilot-instructions.md
    echo "wrote .github/copilot-instructions.md"
    ;;
  *)
    echo "usage: ./install.sh [claude|cursor|agents|copilot]" >&2
    exit 1
    ;;
esac
