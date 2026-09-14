#!/usr/bin/env bash
# Launch the Claude Code CLI, whichever version is installed.
#
# The VS Code extension ships the binary under a version-stamped directory, so a
# path written into a provider profile goes stale on the next extension update -
# and a stale path shows up in the studio as "CLI 未安装", not as "CLI moved".
# Resolving the newest install at call time keeps the profile correct across
# updates. A `claude` already on PATH wins: an explicit install beats a bundle.
set -euo pipefail

if command -v claude >/dev/null 2>&1; then
    exec claude "$@"
fi

newest=""
for candidate in "$HOME"/.vscode-server/extensions/anthropic.claude-code-*/resources/native-binary/claude; do
    [ -x "$candidate" ] || continue
    newest="$candidate"
done

if [ -z "$newest" ]; then
    echo "Claude Code CLI not found: no claude on PATH and no anthropic.claude-code-* extension binary." >&2
    exit 127
fi

exec "$newest" "$@"
