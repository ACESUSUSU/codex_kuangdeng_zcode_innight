#!/usr/bin/env bash
set -euo pipefail

runtime="${ZCODE_DESKTOP_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/computer-use-linux}"
export PATH="$runtime/system/usr/bin:$PATH"
if [[ -d "$runtime/system/usr/lib/x86_64-linux-gnu" ]]; then
    export LD_LIBRARY_PATH="$runtime/system/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi
if [[ -f "$runtime/system/usr/share/glib-2.0/schemas/gschemas.compiled" ]]; then
    export GSETTINGS_SCHEMA_DIR="$runtime/system/usr/share/glib-2.0/schemas"
fi
if [[ "$(uname -s)" != Linux ]]; then
    echo 'The desktop MCP requires Linux; macOS ZCode uses the host native Computer Use tools.' >&2
    exit 1
fi
if [[ -z "${DISPLAY:-}" || "${XDG_SESSION_TYPE:-x11}" != x11 ]]; then
    echo 'This package targets a logged-in X11 desktop. Start Codex in that desktop session.' >&2
    exit 1
fi
if [[ ! -x "$runtime/bin/computer-use-linux" ]]; then
    echo 'Desktop runtime not installed. Run this skill scripts/setup-desktop.sh first.' >&2
    exit 1
fi
export COMPUTER_USE_LINUX_SCREENSHOT_BACKEND=gnome-screenshot
exec "$runtime/bin/computer-use-linux" "${@:-mcp}"
