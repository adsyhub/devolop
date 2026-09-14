#!/usr/bin/env bash
# Launch the Codex CLI, whichever version is installed.
#
# Same reason as claude_cli.sh: the ChatGPT VS Code extension bundles codex under
# a version-stamped directory and does not put it on PATH, so the profile cannot
# name the binary directly and stay true after an update.
set -euo pipefail

if command -v codex >/dev/null 2>&1; then
    exec codex "$@"
fi

newest=""
for candidate in "$HOME"/.vscode-server/extensions/openai.chatgpt-*/bin/*/codex; do
    [ -x "$candidate" ] || continue
    newest="$candidate"
done

if [ -z "$newest" ]; then
    echo "Codex CLI not found: no codex on PATH and no openai.chatgpt-* extension binary." >&2
    exit 127
fi

exec "$newest" "$@"
