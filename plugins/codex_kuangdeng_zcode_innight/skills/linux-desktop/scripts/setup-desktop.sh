#!/usr/bin/env bash
set -euo pipefail

skill_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
runtime="${ZCODE_DESKTOP_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/computer-use-linux}"
export PATH="$runtime/system/usr/bin:$PATH"
missing=()
for program in node npm tar patch cc pkg-config wmctrl xprop xwininfo xdotool gnome-screenshot; do
    command -v "$program" >/dev/null 2>&1 || missing+=("$program")
done
if ! /usr/bin/python3 -c 'import cairo, gi; gi.require_foreign("cairo"); gi.require_version("Gtk", "3.0"); from gi.repository import Gtk' 2>/dev/null; then
    missing+=(python3-gi python3-cairo python3-gi-cairo gir1.2-gtk-3.0)
fi
if [[ -x "$runtime/cargo/bin/cargo" ]]; then
    export CARGO_HOME="$runtime/cargo"
    export RUSTUP_HOME="$runtime/rustup"
    export PATH="$runtime/cargo/bin:$PATH"
fi
command -v cargo >/dev/null 2>&1 || missing+=(cargo)
if ((${#missing[@]})); then
    printf 'Missing prerequisites: %s\n' "${missing[*]}" >&2
    echo 'See references/setup.md. This installer does not install system packages or change shell profiles.' >&2
    exit 1
fi
node -e 'if(Number(process.versions.node.split(".")[0]) < 18) throw Error("Node.js >=18 required; Node 22 tested")'
case "${1:-}" in
    --check) echo 'Build and desktop prerequisites found.'; exit 0 ;;
    '') ;;
    *) echo 'Usage: setup-desktop.sh [--check]' >&2; exit 2 ;;
esac

mkdir -p "$runtime"
build_dir="$(mktemp -d "$runtime/build-zcode-collab.XXXXXX")"
echo "Preparing patched source in $build_dir"
tar -xzf "$skill_dir/assets/computer-use-linux-v0.5.0.tar.gz" --strip-components=1 -C "$build_dir"
patch -d "$build_dir" -p1 < "$skill_dir/assets/ubuntu22.patch"
(
    cd "$build_dir"
    cargo build --locked --release --bin computer-use-linux
    mkdir -p "$runtime/bin"
    install -m 755 "${CARGO_TARGET_DIR:-target}/release/computer-use-linux" "$runtime/bin/computer-use-linux"
)
npm install --prefix "$runtime" --no-audit --no-fund --save-exact @modelcontextprotocol/sdk@1.30.0
echo "Installed runtime and SDK in $runtime. Build source retained at $build_dir."
echo 'Next: follow references/setup.md to enable accessibility and launch ZCode.'
